# 로컬 한계점 탐색 부하 테스트 — 실행 절차

> **작성일**: 2026-09-10
> **목적**: 2025-12-16 AWS 측정에서 못 찾은 **무릎(knee)** 을 로컬 환경에서 찾는다.
> **주의**: 이 실험은 AWS 실험과 **환경이 다르므로 절대값을 섞어 쓰지 않는다.**
> 기존 `../load-test-report.md` 는 건드리지 않는다.

---

## 0. 측정 전에 고정한 중단 조건 (STOP CONDITION)

**측정을 시작하기 전에 아래를 확정했고, 결과를 보고 바꾸지 않는다.**

| 조건 | 임계값 |
|---|---|
| 95%ile 응답 시간 | **> 500 ms** |
| 에러율 | **> 1 %** |

둘 중 **하나라도** 위반한 첫 단계를 "무릎을 넘은 단계"로 판정한다.
판정은 **스폰 완료 후 60초를 버린 정상 상태 구간**으로만 한다
(스폰 구간을 포함하면 무릎 위치가 흐려진다).

`config.py` 의 `STOP_P95_MS`, `STOP_ERROR_RATE` 에 같은 값이 박혀 있다.

---

## 1. 환경 구성

### 서버 (이 PC)

| 항목 | 값 |
|---|---|
| CPU | AMD Ryzen 5 5600 (6C / 12T) |
| RAM | 32 GB |
| OS | Windows 11 Pro 26200 |
| 컨테이너 | Docker Desktop (WSL2 백엔드) |
| 스택 | `docker-compose.loadtest.yml` — MySQL 8.0 / Redis 7 / Django(Daphne) |

**앱 서버는 gunicorn이 아니라 Daphne(ASGI) 단일 프로세스다.**
워커 프로세스 개념이 없고, 동기 뷰는 `asgiref` 스레드풀에서 처리된다.
기본 스레드 상한은 `min(32, CPU+4)` 이므로, 이 값이 병목 후보 1순위다.
→ 리포트에 반드시 기록할 것.

### prod 대비 의도적 차이 (전부 기록 대상)

| 항목 | prod | 여기 | 이유 |
|---|---|---|---|
| Nginx | 있음 | **없음** (Daphne 직접) | 변수 축소 |
| HTTPS | ALB에서 종단 | **평문 HTTP** | 로컬에 종단점 없음 |
| `SECURE_SSL_REDIRECT` / secure 쿠키 | True | **False** | 평문 HTTP에서 로그인 불가해짐 |
| DRF throttle | anon 100/h, user 1000/h | **해제** | 아래 참고 |
| 코드 마운트 | 없음(이미지) | 없음(이미지) | Windows bind-mount I/O 오염 방지 |
| `DEBUG` | False | **False** | dev.py는 쿼리 로그 누적으로 측정 불가 |

**DRF throttle 해제는 이 실험에서 가장 중요한 사전 조치다.**
로그인 API는 `AllowAny`(익명)라 `AnonRateThrottle` 이 **IP 단위**로 걸린다.
부하는 노트북 1대(단일 IP)에서 나오므로 **시간당 100회 로그인 후 전부 429**가 된다.
인증 후 API도 사용자당 1000/hour라 VU당 1~2 RPS면 수 분 내 소진된다.
해제하지 않으면 "서버가 언제 무너지는가"가 아니라 **"DRF 카운터가 언제 차는가"** 를
재게 된다. (뒤집어 말하면 *prod에서는 인프라 한계보다 이 정책이 먼저 걸린다* —
이것 자체가 리포트에 남길 결과다.)

### 부하 생성기 (노트북)

| 항목 | 값 |
|---|---|
| 모델 | MSI P65 Creator 8RD |
| CPU | Intel Core i7-8750H (6C / 12T) |
| RAM | 16 GB (실측값으로 갱신할 것) |
| 연결 | 내부 WLAN (192.168.50.x) |

- **반드시 별도 기계에서 돌린다.** 같은 PC에서 돌리면 생성기가 먼저 병목이 되어
  결론을 못 낸다.
- **Locust를 멀티프로세스로 돌린다 (`--processes 6`).** Locust는 gevent 단일 프로세스라
  기본값으로는 CPU 1코어만 쓴다. 6코어 중 1코어만 쓰면 수백 RPS에서 생성기가 먼저 포화되고,
  서버는 한가해 보인다. `run_stages.py` 가 `config.LOCUST_PROCESSES` 만큼 워커를 띄운다.
- 실제 스펙은 노트북에서 아래로 확인해 리포트에 기록한다.
  ```bash
  python -c "import psutil,platform;print(platform.platform());print(psutil.cpu_count(False),'physical /',psutil.cpu_count(),'logical');print(round(psutil.virtual_memory().total/1e9,1),'GB')"
  ```

### 네트워크 — 확인된 제약

서버 PC의 이더넷은 ISP 공인 IP(`110.13.194.229`)라 내부 LAN에 없다.
**내부망 경로는 Wi-Fi(`192.168.50.97`) 뿐이며, 즉 서버 쪽도 무선이다.**
→ 2단계에서 RTT/대역폭을 반드시 먼저 측정하고, 네트워크가 병목이 아님을 확인한다.
대역폭이 부족하면 서버 PC 이더넷을 공유기에 물리거나 노트북을 유선으로 바꾼다.

---

## 2. 사전 점검 (측정 전 반드시)

### 2-1. 서버 기동

```powershell
docker compose -f docker-compose.loadtest.yml up -d --build
docker compose -f docker-compose.loadtest.yml ps
```

### 2-2. 시드 데이터 생성 (계정 300 / 팀 3 / 게시물·TODO·스케줄)

```powershell
docker compose -f docker-compose.loadtest.yml exec -T web python manage.py shell < docs/guides/load-testing/local-knee/seed_load_data.py
```

마지막 줄에 출력되는 `TEAM_IDS = [...]` 를 받아 적는다. 노트북에서 쓴다.

### 2-3. 네트워크 프로필 + 방화벽 (관리자 PowerShell 1회)

**측정 시작 전 확인된 함정**: 서버 PC의 Wi-Fi(`TlesMes_5G`)는 네트워크 프로필이
**공용(Public)** 이었고, ICMP 에코 인바운드 허용 규칙이 하나도 없었다.
그래서 노트북에서 `ping` 을 쏘면 무조건 "요청 시간 만료"가 난다.
이걸 AP 클라이언트 격리로 오진하기 쉽지만 **원인은 Windows 방화벽**이다.
프로필이 Public인 채로 `-Profile Private` 규칙을 넣으면 규칙이 적용되지 않아
8000 포트도 열리지 않는다.

```powershell
# 1) Wi-Fi를 개인 네트워크로 전환 (이걸 먼저 해야 아래 Private 규칙이 먹는다)
Set-NetConnectionProfile -InterfaceAlias "Wi-Fi" -NetworkCategory Private

# 2) RTT 측정을 위한 ICMP 에코 허용
New-NetFirewallRule -DisplayName "LoadTest ICMPv4 Echo" -Direction Inbound -Protocol ICMPv4 -IcmpType 8 -Action Allow -Profile Private

# 3) 앱 포트
New-NetFirewallRule -DisplayName "TeamMoa LoadTest 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private

# 4) 대역폭 측정용 iperf3 포트
New-NetFirewallRule -DisplayName "LoadTest iperf3 5201" -Direction Inbound -Protocol TCP -LocalPort 5201 -Action Allow -Profile Private
```

확인:
```powershell
Get-NetConnectionProfile -InterfaceAlias "Wi-Fi" | Select-Object Name,NetworkCategory
```

> ICMP 허용은 편의 기능이 아니다. 2-5의 RTT 수치는 "네트워크가 병목이 아니었음"을
> 증명하는 필수 기록 항목이므로, ping이 통하지 않으면 그 근거를 만들 수 없다.

> **Tailscale을 경로로 쓰지 않는다.** 양쪽에 깔려 있어 유혹이 있지만, userspace
> WireGuard 암호화와 경우에 따라 릴레이가 끼어 지연·처리량이 왜곡된다.
> 반드시 `192.168.50.x` 로컬 주소로 직접 붙는다.

### 2-4. 노트북에서 도달 확인

```bash
curl -i http://192.168.50.97:8000/health/
```

### 2-5. 네트워크가 병목이 아님을 확인 — **수치를 기록한다**

```bash
# RTT
ping -c 50 192.168.50.97

# 대역폭 (서버 PC에서 iperf3 -s, 노트북에서)
iperf3 -c 192.168.50.97 -t 20
```

기록: RTT 평균/최대, jitter, 대역폭(Mbps).
목표 RPS × 평균 응답 크기가 대역폭의 절반을 넘으면 네트워크가 병목이다.

### 2-5b. 사전 점검 결과 (2026-09-11 서버 PC 실측, 무부하 단일 요청)

시드 직후 로컬(127.0.0.1)에서 시나리오 8개를 전부 확인했다. 부하를 걸기 전에
엔드포인트가 200을 내는지 확인하지 않으면, 부하가 아니라 에러율을 재게 된다.

| 태스크 | 경로 | 상태 | 응답 크기 | 무부하 응답시간 |
|---|---|---|---|---|
| 01 로그인 | `POST /api/v1/users/login/` | 200 (sessionid 발급) | - | - |
| 02 홈 | `/` | **302 → `/teams/` 200** | 4,415 B | 20.8 ms |
| 03 팀 목록 | `/api/v1/teams/` | 200 | 204 B | 17.5 ms |
| 04 팀 상세 | `/api/v1/teams/1/` | 200 | 236 B | 16.8 ms |
| 05 공유게시판 | `/shares/1/` | 200 | 8,738 B | 63.1 ms |
| 06 TODO 목록 | `/api/v1/teams/1/todos/` | 200 | 4,862 B | 28.3 ms |
| 07 스케줄 | `/api/v1/teams/1/schedules/` | 200 | 2,279 B | 17.2 ms |
| 08 Health | `/health/` | 200 | 43 B | 7.6 ms |

**⚠️ 홈 태스크는 실제로 2왕복이다.** `/` 가 302로 `/teams/` 에 리다이렉트되고
Locust(requests)는 리다이렉트를 따라간다. 즉 **Locust는 요청 1건으로 집계하지만
서버는 2번 처리한다.** 가중치가 25%로 가장 크므로 영향이 작지 않다.

> 서버 실측 RPS ≈ Locust 집계 RPS × (1 + 0.25) 로 보정해 읽어야 한다.
> 시나리오 자체는 AWS 실험과의 비교 가능성을 위해 원본 그대로 둔다.
> 보정은 리포트에서 하고, 근거로 이 표를 인용한다.

무부하 기준 가장 무거운 것은 **공유게시판(63ms, 8.7KB)** 이다.
N+1 최적화 전후 비교에서 차이가 가장 크게 드러날 후보다.

### 2-5c. 시드 결과 (2026-09-11)

```
사용자 300명 / 팀 3개 (id = 1, 2, 3) / 팀당 멤버 100명
팀당 게시물 60, TODO 120, 개인 스케줄 700
→ TEAM_IDS=1,2,3
```

### 2-6. 생성기 준비

```bash
pip install locust psutil matplotlib
```

---

## 3. 측정 절차

VU 단계: **50 → 100 → 200 → 400 → 800** (배수 증가)
각 단계 180초, 앞 60초는 워밍업으로 버림.

### 각 단계마다

**서버 PC에서 (단계 시작 직전):**
```powershell
powershell -ExecutionPolicy Bypass -File docs\guides\load-testing\local-knee\monitor_server.ps1 -Stage vu0050 -DurationSec 200
```

**노트북에서:**
```bash
export TARGET_URL=http://192.168.50.97:8000
export TEAM_IDS=1,2,3          # 2-2 에서 받아 적은 값
python run_stages.py 50
```

`-Stage` 이름은 `vu0050`, `vu0100`, `vu0200`, `vu0400`, `vu0800` 으로
locust CSV 접두사(`vu0050` …)와 **정확히 맞춰야** 집계가 병합된다.

전 단계를 한 번에 돌리려면 `python run_stages.py` (인자 없음).
단, 서버 모니터는 단계마다 따로 띄워야 하므로 처음에는 단계별로 수동 진행을 권한다.

### 무릎 구간 좁히기

중단 조건에 걸린 단계가 나오면, 직전 단계와 그 사이를 다시 잰다.
예: 200 정상 / 400 위반 → `python run_stages.py 250 300 350`

---

## 4. 집계

서버 PC의 `results/server_*.csv` 를 노트북의 `results/` 로 모은 뒤:

```bash
python analyze.py
```

단계별 표 + `results/knee_curve.png` 가 나온다.

---

## 5. 기록 항목 (하나도 빠뜨리지 않는다)

| 항목 | 출처 | 왜 필요한가 |
|---|---|---|
| VU, RPS, 평균, p95, 에러율 | `analyze.py` | 곡선의 기본 |
| **서버 CPU / 메모리 / MySQL 커넥션** | `monitor_server.ps1` | **서버가 한계였음을 증명** |
| **생성기 CPU / 메모리** | `run_stages.py` | **생성기가 병목이 아니었음을 증명** |
| RTT / 대역폭 | 2-5 | 네트워크가 병목이 아님을 증명 |
| PC 스펙, compose 구성, Daphne 스레드풀 상한 | 이 문서 1절 | 재현 조건 |

가운데 두 줄이 없으면 "서버 한계를 쟀다"고 쓸 수 없다.

---

## 6. 무릎이 안 나올 경우

**"한계를 못 찾았다"로 끝내지 않는다. 무엇이 먼저 걸렸는지까지 규명한다.**
확인 순서:

1. **생성기 CPU가 80%+** → 생성기 포화. VU를 더 못 올린다. 노트북 추가 또는 locust 분산 모드.
2. **에러가 429** → throttle이 살아 있다. `loadtest.py` 설정이 적용됐는지 확인.
3. **에러가 connection reset / timeout인데 서버 CPU는 한가함**
   → Daphne 스레드풀(`min(32, CPU+4)`) 또는 리스닝 백로그. 큐잉 지연으로 p95만 오른다.
4. **MySQL `Threads_connected` 가 상한 근처** → DB 커넥션이 먼저 걸림.
   `CONN_MAX_AGE=600` 이라 커넥션이 오래 잡혀 있다.
5. **서버 CPU 100%인데 web 컨테이너가 아니라 db가 먹고 있음** → 쿼리 비용이 한계.
   → 확장 실험(N+1 이전 커밋 비교)의 대조군으로 딱 맞는 상황.
6. **대역폭이 Wi-Fi 상한 근처** → 네트워크 병목. 유선으로 바꿔 재측정.

어느 경우든 **그 지표의 실측값을 리포트에 싣는다.** 그게 결과다.

---

## 7. 확장 실험 — N+1 최적화 이전과 비교

최적화 커밋 2개와 그 직전 상태(대조군)는 다음과 같다.

| 역할 | 커밋 | 내용 |
|---|---|---|
| 대조군(최적화 직전) | `43eefc5` | `docs: portfolio → technical 디렉토리 링크 수정` |
| 최적화 1 | `c159f51` | `perf(query): 중복 쿼리 제거로 4개 페이지 성능 최적화` |
| 최적화 2 | `41f941c` | `perf(query): N+1 쿼리 문제 완전 해결` |

```bash
git switch -c perf/before-n1-fix 43eefc5
# loadtest 설정/compose/시드 스크립트는 이 브랜치에 없으므로 main에서 가져온다
git checkout main -- TeamMoa/settings/loadtest.py docker-compose.loadtest.yml docs/guides/load-testing/local-knee
docker compose -f docker-compose.loadtest.yml up -d --build
```

> 대조군 브랜치에는 이후 추가된 마이그레이션이 없으므로 **DB 볼륨을 반드시 새로 만든다**
> (`docker compose -f docker-compose.loadtest.yml down -v` 후 재기동 + 시드 재생성).
> 같은 DB를 공유하면 스키마 불일치로 측정이 아니라 에러를 재게 된다.

같은 시드 / 같은 중단 조건 / 같은 단계로 한 번 더 돌린다.
비교 결과는 "쿼리 수를 줄였다"가 아니라
**"무릎이 VU N에서 VU M으로 옮겨갔다"** 로 쓴다.
