"""
로컬 한계점 탐색 부하 테스트 설정 (2026-09-10)

기존 docs/guides/load-testing/config.py 는 AWS ALB 실험용이므로 건드리지 않는다.
이 파일은 별개 실험용이다.
"""
import os
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 대상 서버 — 서버 PC의 내부망 IP (노트북에서 접근 가능한 주소)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 환경변수 TARGET_URL 로 덮어쓸 수 있다.
TARGET_URL = os.environ.get("TARGET_URL", "http://192.168.50.97:8000")

# 시드 스크립트가 출력한 팀 ID. seed_load_data.py 실행 후 값 확인해 맞출 것.
TEAM_IDS = [int(x) for x in os.environ.get("TEAM_IDS", "1,2,3").split(",")]

TEST_USER_PASSWORD = "LoadTest2024!"
USERS_TOTAL = 300

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 대기 시간 — 사용자당 약 1~2 RPS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 기존 AWS 실험은 between(2,5)라 사용자당 0.29 RPS에 그쳤고, 그래서 150 VU에서도
# 무릎이 안 나왔다. 여기서는 0.5~1초로 낮춰 VU당 부하 밀도를 5배 가까이 올린다.
WAIT_TIME_MIN = float(os.environ.get("WAIT_TIME_MIN", "0.5"))
WAIT_TIME_MAX = float(os.environ.get("WAIT_TIME_MAX", "1.0"))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 중단 조건 (STOP CONDITION) — 측정 전 확정. 결과에 맞춰 바꾸지 않는다.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 아래 둘 중 **하나라도** 걸리면 그 단계를 "무릎을 넘었다"로 판정한다.
# 정상 구간 안정화 후(스폰 완료 + 60초)의 정상 상태 구간으로만 판정한다.
STOP_P95_MS = 500.0     # 95%ile 응답 시간 > 500ms
STOP_ERROR_RATE = 1.0   # 에러율 > 1%

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 생성기 멀티프로세스 (중요)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Locust는 gevent 기반 단일 프로세스라 기본값으로는 **CPU 1코어만** 쓴다.
# 생성기(i7-8750H, 6C/12T)가 수백 RPS에서 먼저 포화되면 서버가 한가해 보이고,
# 그걸 "서버에 여유가 있다"로 오독하게 된다 — 기존 AWS 측정이 빠진 함정이다.
# 워커 프로세스를 코어 수만큼 띄워 생성기 여유를 확보한다.
LOCUST_PROCESSES = int(os.environ.get("LOCUST_PROCESSES", "6"))

# 단계별 VU (배수 증가)
VU_STAGES = [50, 100, 200, 400, 800]

# 단계당 측정 시간 / 워밍업 제외 구간
STAGE_DURATION_SEC = 180
WARMUP_DISCARD_SEC = 60

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
