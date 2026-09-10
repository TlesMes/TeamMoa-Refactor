"""
단계별 결과 집계 + 곡선 생성 (2026-09-10)

locust의 _stats_history.csv 에서 **워밍업 구간을 잘라낸 정상 상태**만 집계한다.
스폰 구간을 포함해 평균을 내면 무릎 위치가 흐려진다.

서버 CSV와 생성기 CSV(generator_*.csv)가 같은 results/ 에 있으면 함께 병합한다.
서버 CSV는 두 방식 다 받는다:
  - server_<stage>.csv      단계마다 따로 수집한 경우
  - server_continuous.csv   전 구간 연속 수집한 경우 (권장)
연속 수집이면 각 단계의 정상 상태 구간으로 잘라 쓰므로, 서버 세션과 생성기 세션이
단계 시작 시각을 서로 맞출 필요가 없다.

실행:
    pip install matplotlib
    python analyze.py
"""
import csv
import glob
import os
import statistics
from datetime import datetime

import config

RESULTS = config.RESULTS_DIR


def read_csv(path):
    # locust가 이 Windows 환경의 기본 코드페이지(cp949)로 CSV를 쓰는 경우가
    # 있어(태스크 이름의 한글 때문) utf-8-sig가 실패하면 cp949로 재시도한다.
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except UnicodeDecodeError:
        with open(path, newline="", encoding="cp949") as f:
            return list(csv.DictReader(f))


def num(row, *keys, default=None):
    """헤더 이름이 locust 버전마다 달라서 후보를 순서대로 시도한다."""
    for k in keys:
        if k in row and row[k] not in ("", "N/A", None):
            try:
                return float(row[k])
            except ValueError:
                pass
    return default


def steady_rows(rows):
    """스폰 완료 + WARMUP_DISCARD_SEC 이후 구간만 남긴다."""
    if not rows:
        return []
    t0 = float(rows[0]["Timestamp"])
    target = max(num(r, "User Count", default=0) or 0 for r in rows)
    # VU가 목표치를 유지하지 못하는 단계가 있다. 서버가 500을 던지면 on_start의
    # 로그인이 실패해 VU가 죽고 User Count가 목표 아래로 내려간다(VU400→371,
    # VU800→634). "정확히 목표치"를 요구하면 그 단계가 통째로 누락되는데,
    # 하필 그런 단계가 가장 중요한 구간이다. 목표의 90%면 정상 상태로 본다.
    out = [r for r in rows
           if (num(r, "User Count", default=0) or 0) >= target * 0.9
           and float(r["Timestamp"]) - t0 >= config.WARMUP_DISCARD_SEC]
    if not out:  # 그래도 비면 워밍업만 잘라내고 뒤쪽 2/3를 쓴다
        out = rows[len(rows) // 3:]
    return out


def summarize_stage(prefix):
    hist = f"{prefix}_stats_history.csv"
    if not os.path.exists(hist):
        return None
    all_rows = [r for r in read_csv(hist) if r.get("Name") == "Aggregated"]
    # 목표 VU는 필터링 전 전체에서 구한다. 정상 상태 구간만 보면 실제로
    # 유지된 수가 나오는데, 둘이 다른 단계(VU400→371)가 판정에 중요하다.
    target = int(max(num(r, "User Count", default=0) for r in all_rows)) if all_rows else 0
    rows = steady_rows(all_rows)
    if not rows:
        return None

    rps = [num(r, "Requests/s", default=0) for r in rows]
    fps = [num(r, "Failures/s", default=0) for r in rows]
    p95 = [num(r, "95%", "95%ile", default=0) for r in rows]
    avg = [num(r, "Total Average Response Time", "Total Median Response Time", default=0)
           for r in rows]

    total_rps = statistics.mean(rps) if rps else 0
    total_fps = statistics.mean(fps) if fps else 0
    return {
        "window": stage_window(rows),
        "users_target": target,
        "users": int(max(num(r, "User Count", default=0) for r in rows)),
        "rps": total_rps,
        "avg_ms": statistics.mean(avg) if avg else 0,
        "p95_ms": statistics.mean(p95) if p95 else 0,
        "p95_max_ms": max(p95) if p95 else 0,
        "err_pct": (total_fps / total_rps * 100) if total_rps else 0,
        "samples": len(rows),
    }


SERVER_COLS = ["host_cpu_pct", "web_cpu_pct", "web_mem_mb", "db_cpu_pct",
               "mysql_threads_connected", "mysql_threads_running"]


def summarize_side(path, cols, window=None):
    """window=(start_epoch, end_epoch) 가 주어지면 그 구간의 행만 집계한다."""
    if not os.path.exists(path):
        return {}
    rows = read_csv(path)
    if window:
        rows = [r for r in rows if _in_window(r.get("ts"), window)]
    out = {}
    for c in cols:
        vals = [float(r[c]) for r in rows if r.get(c) not in ("", None) and float(r[c]) >= 0]
        if vals:
            out[c + "_avg"] = statistics.mean(vals)
            out[c + "_max"] = max(vals)
    return out


def _in_window(ts, window):
    """서버 수집기의 ISO 타임스탬프를 epoch로 바꿔 구간 안인지 본다."""
    if not ts:
        return False
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return False
    if dt.tzinfo is None:
        dt = dt.astimezone()   # naive면 로컬 시간대로 간주
    e = dt.timestamp()
    return window[0] <= e <= window[1]


def stage_window(rows):
    """정상 상태 구간의 (시작, 끝) epoch. 서버 CSV를 같은 구간으로 자르는 데 쓴다."""
    if not rows:
        return None
    ts = [float(r["Timestamp"]) for r in rows]
    return (min(ts), max(ts))


def main():
    stages = []
    for prefix in sorted(glob.glob(os.path.join(RESULTS, "vu*_stats_history.csv"))):
        base = prefix.replace("_stats_history.csv", "")
        stage = os.path.basename(base)
        s = summarize_stage(base)
        if not s:
            print(f"[skip] {stage}: 정상 상태 구간 없음")
            continue
        s["stage"] = stage

        # 서버 지표: 단계별 파일이 있으면 그걸 쓰고, 없으면 연속 수집 파일을
        # 이 단계의 정상 상태 구간으로 잘라 쓴다.
        # 연속 수집 방식이면 두 세션이 단계 시작을 맞출 필요가 없다.
        per_stage = os.path.join(RESULTS, f"server_{stage}.csv")
        continuous = os.path.join(RESULTS, "server_continuous.csv")
        if os.path.exists(per_stage):
            s.update(summarize_side(per_stage, SERVER_COLS))
            s["server_src"] = "per-stage"
        elif os.path.exists(continuous):
            s.update(summarize_side(continuous, SERVER_COLS, window=s["window"]))
            s["server_src"] = "continuous"
        else:
            s["server_src"] = "없음"

        s.update(summarize_side(
            os.path.join(RESULTS, f"generator_{stage}.csv"),
            ["cpu_pct", "mem_pct"]))
        stages.append(s)

    if not stages:
        print("결과 없음. run_stages.py 를 먼저 실행할 것.")
        return

    stages.sort(key=lambda s: s["users"])

    hdr = ("| VU | RPS | 평균(ms) | p95(ms) | p95최대 | 에러율 | 서버CPU% | web CPU% | "
           "DB CPU% | MySQL conn | 생성기CPU% | 판정 |")
    print(hdr)
    print("|" + "---|" * 12)
    srcs = {s.get("server_src") for s in stages}
    knee = None
    for s in stages:
        breach = (s["p95_ms"] > config.STOP_P95_MS or s["err_pct"] > config.STOP_ERROR_RATE)
        if breach and knee is None:
            knee = s["stage"]
        print("| {users} | {rps:.1f} | {avg_ms:.1f} | {p95_ms:.1f} | {p95_max_ms:.0f} | "
              "{err_pct:.2f}% | {hc:.0f} | {wc:.0f} | {dc:.0f} | {mc:.0f} | {gc:.0f} | {v} |".format(
                  hc=s.get("host_cpu_pct_avg", -1), wc=s.get("web_cpu_pct_avg", -1),
                  dc=s.get("db_cpu_pct_avg", -1),
                  mc=s.get("mysql_threads_connected_max", -1),
                  gc=s.get("cpu_pct_avg", -1),
                  v="위반" if breach else "정상", **s))

    print()
    print(f"서버 지표 출처: {', '.join(sorted(x for x in srcs if x))}")
    print(f"중단 조건: p95 > {config.STOP_P95_MS}ms 또는 에러율 > {config.STOP_ERROR_RATE}%")
    print(f"무릎(최초 위반 단계): {knee or '나오지 않음 — 무엇이 먼저 걸렸는지 규명 필요'}")

    try:
        plot(stages)
    except ImportError:
        print("(matplotlib 없음 — 그래프 생략)")


def plot(stages):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    vu = [s["users"] for s in stages]
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))

    ax[0].plot(vu, [s["rps"] for s in stages], "o-", color="#2563eb")
    ax[0].set_title("Throughput (RPS)")
    ax[0].set_xlabel("Virtual Users")

    ax[1].plot(vu, [s["p95_ms"] for s in stages], "o-", color="#dc2626", label="p95")
    ax[1].plot(vu, [s["avg_ms"] for s in stages], "o--", color="#f59e0b", label="avg")
    ax[1].axhline(config.STOP_P95_MS, ls=":", color="gray", label="stop: 500ms")
    ax[1].set_title("Response time (ms)")
    ax[1].set_xlabel("Virtual Users")
    ax[1].legend()

    ax[2].plot(vu, [s["err_pct"] for s in stages], "o-", color="#7c3aed", label="error %")
    ax[2].plot(vu, [s.get("host_cpu_pct_avg", 0) for s in stages], "s--",
               color="#059669", label="server CPU %")
    ax[2].plot(vu, [s.get("cpu_pct_avg", 0) for s in stages], "^--",
               color="#9ca3af", label="generator CPU %")
    ax[2].axhline(config.STOP_ERROR_RATE, ls=":", color="gray")
    ax[2].set_title("Errors & saturation")
    ax[2].set_xlabel("Virtual Users")
    ax[2].legend()

    for a in ax:
        a.set_xscale("log", base=2)
        a.set_xticks(vu)
        a.set_xticklabels([str(v) for v in vu])
        a.grid(alpha=.3)

    fig.tight_layout()
    out = os.path.join(RESULTS, "knee_curve.png")
    fig.savefig(out, dpi=140)
    print(f"그래프: {out}")


if __name__ == "__main__":
    main()
