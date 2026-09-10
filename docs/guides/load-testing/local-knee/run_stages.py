"""
노트북(부하 생성기)에서 실행하는 단계별 실행기 (2026-09-10)

VU를 배수로 올리며 각 단계를 headless Locust로 돌리고,
동시에 **생성기 자신의 CPU를 샘플링**한다.
생성기 CPU 기록이 없으면 "서버 한계를 쟀다"고 말할 수 없다 —
생성기가 먼저 포화되면 서버는 한가해 보이기 때문이다.

사전 준비:
    pip install locust psutil

실행:
    TARGET_URL=http://192.168.50.97:8000 TEAM_IDS=1,2,3 python run_stages.py
    (Windows PowerShell: $env:TARGET_URL="..."; $env:TEAM_IDS="1,2,3"; python run_stages.py)

특정 단계만:
    python run_stages.py 400
"""
import csv
import os
import subprocess
import sys
import threading
import time

import psutil

import config

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = config.RESULTS_DIR


def sample_generator(stage, stop_evt):
    """생성기(노트북) 자원 사용량 샘플링

    ⚠️ net_sent_mb / net_recv_mb 는 psutil.net_io_counters() 기반이라
    **노트북 전체 트래픽**이다. locust가 쓴 양이 아니다. 실제로 요청 수가
    거의 같은 단계끼리도 45% 차이가 났다. 대역폭 실사용량은 이 값이 아니라
    시나리오 가중치 × 응답 크기로 산출할 것 (REPORT.md 4절).
    이 컬럼은 상한으로만 읽는다.

    cpu_pct 는 시스템 전체지만 이쪽은 의도한 것이다 — 워커 6개가 별도
    프로세스라 마스터 프로세스만 재면 생성기 포화를 놓친다.
    """
    path = os.path.join(RESULTS, f"generator_{stage}.csv")
    psutil.cpu_percent(interval=None)  # 첫 호출은 버림
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ts", "cpu_pct", "mem_pct", "net_sent_mb", "net_recv_mb", "open_sockets"])
        base = psutil.net_io_counters()
        while not stop_evt.is_set():
            time.sleep(2)
            n = psutil.net_io_counters()
            try:
                socks = len(psutil.Process().net_connections())
            except Exception:
                socks = -1
            w.writerow([
                time.strftime("%Y-%m-%dT%H:%M:%S"),
                psutil.cpu_percent(interval=None),
                psutil.virtual_memory().percent,
                round((n.bytes_sent - base.bytes_sent) / 1e6, 2),
                round((n.bytes_recv - base.bytes_recv) / 1e6, 2),
                socks,
            ])
            f.flush()


def run_stage(vu):
    stage = f"vu{vu:04d}"
    prefix = os.path.join(RESULTS, stage)
    spawn_rate = max(10, vu // 10)   # 스폰 구간을 10초 내로 끝내 정상 상태를 길게 확보

    print("=" * 60)
    print(f"[{stage}] VU={vu} spawn_rate={spawn_rate} "
          f"processes={config.LOCUST_PROCESSES} "
          f"duration={config.STAGE_DURATION_SEC}s  target={config.TARGET_URL}")
    print("=" * 60)

    stop_evt = threading.Event()
    t = threading.Thread(target=sample_generator, args=(stage, stop_evt), daemon=True)
    t.start()

    locustfile = os.path.join(HERE, "locustfile.py")
    base_cmd = [sys.executable, "-m", "locust", "-f", locustfile]

    worker_procs = []
    if sys.platform == "win32":
        # --processes는 네이티브 Windows에서 미지원(WSL 전용)이라 gevent
        # 단일 프로세스로 떨어져 1코어만 쓰게 된다. 생성기가 먼저 포화되는
        # 문제를 피하려고 master-worker를 수동으로 띄운다(워커는 독립
        # 프로세스라 Windows에서도 동작). 마스터가 리슨을 시작한 뒤에
        # 워커를 붙여야 초기 연결 실패/재시도 지연이 없다.
        cmd = base_cmd + [
            "--host", config.TARGET_URL,
            "--headless", "--master",
            "--expect-workers", str(config.LOCUST_PROCESSES),
            "-u", str(vu),
            "-r", str(spawn_rate),
            "-t", f"{config.STAGE_DURATION_SEC}s",
            "--csv", prefix,
            "--csv-full-history",
            "--only-summary",
        ]
        master_proc = subprocess.Popen(cmd, cwd=HERE)
        time.sleep(3)  # 마스터가 5557 포트 리슨을 시작할 시간 확보

        for _ in range(config.LOCUST_PROCESSES):
            worker_procs.append(subprocess.Popen(
                base_cmd + ["--worker", "--master-host", "127.0.0.1"],
                cwd=HERE,
            ))

        rc = master_proc.wait()
    else:
        cmd = base_cmd + [
            "--host", config.TARGET_URL,
            "--headless",
            "-u", str(vu),
            "-r", str(spawn_rate),
            "-t", f"{config.STAGE_DURATION_SEC}s",
            "--csv", prefix,
            "--csv-full-history",
            "--only-summary",
            "--processes", str(config.LOCUST_PROCESSES),
        ]
        rc = subprocess.call(cmd, cwd=HERE)

    for p in worker_procs:
        p.terminate()
    for p in worker_procs:
        p.wait(timeout=10)

    stop_evt.set()
    t.join(timeout=5)
    print(f"[{stage}] locust exit={rc}")
    return rc


def main():
    stages = [int(a) for a in sys.argv[1:]] or config.VU_STAGES
    print(f"단계: {stages}")
    print(f"중단 조건(측정 전 확정): p95 > {config.STOP_P95_MS}ms 또는 "
          f"에러율 > {config.STOP_ERROR_RATE}%")
    for vu in stages:
        run_stage(vu)
        if vu != stages[-1]:
            print("서버 회복 대기 30초...")
            time.sleep(30)
    print("\n완료. analyze.py 로 정상 상태 구간을 집계할 것.")


if __name__ == "__main__":
    main()
