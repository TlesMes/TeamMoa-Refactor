# 노트북(부하 생성기) 세션 브리프

> 이 문서는 **노트북에서 실행되는 Claude Code 세션**에 그대로 넘기는 지시서다.
> 서버 세션(서버 PC)이 서버 기동·시드·자원 수집을 맡고, 이 세션은 **부하 생성만** 맡는다.

---

## 네 역할

너는 **부하 생성기 담당**이다. 서버는 다른 PC(`192.168.50.97`)에서 이미 돌고 있다.
서버를 기동하거나 코드를 고치려 하지 마라. 이 노트북에서 Locust만 돌리고 결과를 모은다.

## 이 실험이 답하려는 질문

2025-12-16 AWS 측정은 부하가 너무 약해서(사용자당 0.29 RPS) 150 VU에서도
p95가 76ms였다. **꺾이는 지점을 못 찾았다.** 그래서 "여유가 있다" 외에는
말할 수 있는 게 없었다.

이번엔 **무릎(knee)을 찾는다.** 응답 시간이 급증하거나 에러율이 오르는 지점.

## 절대 어기면 안 되는 것

1. **중단 조건은 측정 전에 이미 고정됐다. 바꾸지 마라.**
   - `p95 > 500ms` 또는 `에러율 > 1%`
   - 수치가 안 예쁘다고 조건을 조정하는 순간 이 실험은 무의미해진다.
2. **생성기(이 노트북)의 CPU를 반드시 기록한다.**
   `run_stages.py` 가 자동으로 `results/generator_*.csv` 에 남긴다.
   이게 없으면 "서버 한계를 쟀다"고 말할 수 없다 — 생성기가 먼저 포화되면
   서버는 한가해 보이기 때문이다. **이번 실험에서 가장 중요한 기록이다.**
3. **무릎이 안 나와도 "못 찾았다"로 끝내지 마라.**
   무엇이 먼저 걸렸는지까지 규명한다 (RUNBOOK 6절).
4. **AWS 측정치와 절대값을 섞어 쓰지 마라.** 별개 실험이다.

---

## 준비

```bash
git clone https://github.com/TlesMes/TeamMoa-Refactor.git
cd TeamMoa-Refactor
git switch <서버 세션이 알려준 브랜치>
cd docs/guides/load-testing/local-knee
pip install locust psutil matplotlib
```

### iperf3 설치 (대역폭 측정용, 노트북에도 필요)

서버 PC에는 이미 설치했다 (`ar51an.iPerf3` 3.21). 노트북에도 같은 버전을 깐다.

```powershell
# Windows
winget install --id ar51an.iPerf3 --accept-source-agreements --accept-package-agreements
```
```bash
# macOS / Linux
brew install iperf3        # 또는  sudo apt install iperf3
```

> winget 설치 직후에는 PATH가 현재 셸에 반영되지 않는다. 셸을 새로 열거나
> 전체 경로로 실행할 것.

### 이 노트북 스펙을 먼저 기록한다 (리포트 근거 항목)

```bash
python -c "import psutil,platform;print(platform.platform());print(psutil.cpu_count(False),'physical /',psutil.cpu_count(),'logical');print(round(psutil.virtual_memory().total/1e9,1),'GB')"
```

예상: MSI P65 Creator 8RD / i7-8750H (6C/12T) / 16GB.
**실측값으로 갱신할 것.**

---

## 1단계: 경로와 네트워크 확인 (측정 전 필수)

서버 PC의 Wi-Fi는 원래 네트워크 프로필이 "공용"이라 ping이 막혀 있었다.
서버 세션이 이미 개인으로 바꾸고 ICMP·8000·5201 포트를 열어뒀다.
그래도 **실제로 통하는지 직접 확인한다.**

```bash
ping -c 50 192.168.50.97          # Windows면: ping -n 50 192.168.50.97
curl -i http://192.168.50.97:8000/health/
```

`/health/` 가 200이 아니면 여기서 멈추고 서버 세션에 알린다.

### 네트워크가 병목이 아님을 증명 — 수치를 남긴다

서버 PC에서 서버 세션이 `iperf3 -s` 를 띄운다. 그 다음 노트북에서:

```bash
# 업로드 방향 (노트북 → 서버) : 요청 트래픽에 해당
iperf3 -c 192.168.50.97 -t 20

# 다운로드 방향 (서버 → 노트북) : 응답 트래픽에 해당. 이쪽이 더 중요하다
iperf3 -c 192.168.50.97 -t 20 -R
```

**기록**: 양방향 대역폭(Mbps), RTT 평균/최대/표준편차, TCP 재전송(Retr) 수.

> 응답이 요청보다 훨씬 크므로(공유게시판 8.7KB 등) **`-R` 방향이 병목 판정의
> 핵심**이다. 재전송 수가 눈에 띄면 무선 간섭이 있다는 뜻이고, 그 상태의 p95는
> 서버 특성이 아니라 무선 특성을 반영한다.

> ⚠️ 서버·노트북 **양쪽 다 무선**이고 같은 AP에 붙어 있다.
> 두 단말이 같은 채널의 airtime을 나눠 쓰기 때문에 유선 대비 실효 대역폭이
> 절반 아래로 떨어지고 jitter가 커진다. p95를 재는 실험에서 jitter는 측정 오염이다.
> 대역폭이 목표 처리량(RPS × 평균 응답 크기)의 2배에 못 미치면
> **네트워크가 병목이므로 서버 세션에 알리고 유선 전환을 논의한다.**

---

## 2단계: 단계별 측정

VU: **50 → 100 → 200 → 400 → 800** (배수 증가)
각 단계 180초, 앞 60초는 워밍업으로 버린다 (`analyze.py` 가 자동 처리).

```bash
export TARGET_URL=http://192.168.50.97:8000
export TEAM_IDS=1,2,3        # 서버 세션이 시드 후 알려준 값으로 교체
python run_stages.py 50
```

**단계 시작 시각을 서버 세션과 맞출 필요는 없다.**
서버 쪽 자원 수집기가 전 구간 연속으로 돌고 있고, 집계할 때 Locust CSV의
타임스탬프로 각 단계 구간을 잘라 쓴다. 너는 네 페이스대로 진행하면 된다.

전 단계를 한 번에 돌리려면 인자 없이:
```bash
python run_stages.py
```

### 무릎 구간 좁히기

중단 조건에 걸린 단계가 나오면 직전 단계와 그 사이를 다시 잰다.
예: 200 정상 / 400 위반 → `python run_stages.py 250 300 350`

---

## 3단계: 집계

서버 세션이 보내준 `server_continuous.csv` 를 `results/` 에 넣고:

```bash
python analyze.py
```

단계별 표와 `results/knee_curve.png` 가 나온다.

---

## 생성기가 먼저 포화됐는지 판정하는 법

`results/generator_*.csv` 의 `cpu_pct` 를 본다.

| 상황 | 해석 |
|---|---|
| 생성기 CPU < 60%, 서버 CPU 높음 | ✅ 서버 한계를 재고 있다 |
| 생성기 CPU > 80% | ❌ **생성기 포화.** 이 단계 수치는 서버 한계가 아니다 |
| 양쪽 다 낮은데 p95만 오름 | 큐잉 지연. Daphne 스레드풀 / DB 커넥션 / 네트워크 의심 |

`config.LOCUST_PROCESSES = 6` 으로 워커를 6개 띄운다 (Locust는 기본이 단일
프로세스라 1코어만 쓴다). 그래도 포화되면 서버 세션에 알린다.

---

## 참고

- 상세 절차와 환경 제약: [RUNBOOK.md](./RUNBOOK.md)
- 기존 AWS 실험(별개): [../load-test-report.md](../load-test-report.md) — **덮어쓰지 마라**
