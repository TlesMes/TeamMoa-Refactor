"""
부하 테스트 설정 파일
TeamMoa ALB 로드밸런싱 및 고가용성 검증용
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 대상 서버 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALB_URL = "https://teammoa.shop"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트 계정 설정 (EC2에서 자동 생성됨)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST_USER_PASSWORD = "LoadTest2024!"
TEST_TEAM_PASSWORD = "1234"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Locust 테스트 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 동시 사용자 수 (점진적 증가)
MIN_USERS = 10      # 시작 사용자 수
MAX_USERS = 200     # 최대 사용자 수
SPAWN_RATE = 10     # 초당 사용자 증가 수

# 테스트 시간
TEST_DURATION = "5m"  # 5분 (예: 5m, 10m, 1h)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 대기 시간 설정 (사용자 행동 시뮬레이션)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WAIT_TIME_MIN = 2  # 최소 대기 시간 (초)
WAIT_TIME_MAX = 5  # 최대 대기 시간 (초)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 성능 목표 (SLA)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SLA_RESPONSE_TIME_P95 = 500  # ms (95%ile 응답 시간)
SLA_ERROR_RATE = 1.0         # % (에러율 1% 이하)
SLA_RPS_TARGET = 100         # requests/sec (목표 처리량)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 결과 저장 경로
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import os
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# 타임스탬프 포함 파일명
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT_HTML = os.path.join(RESULTS_DIR, f"report_{TIMESTAMP}.html")
REPORT_CSV = os.path.join(RESULTS_DIR, f"stats_{TIMESTAMP}.csv")
