"""
TeamMoa ALB 부하 테스트 시나리오
- 로드밸런싱 검증 (2대 EC2 트래픽 분산)
- 고가용성 검증 (Failover 테스트)
- 성능 측정 (응답 시간, 처리량, 에러율)
"""

from locust import HttpUser, task, between, events
from locust.exception import StopUser
import config
import logging
from urllib.parse import urljoin
import random
import gevent

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEAM_IDS = [4, 5, 6]

class TeamMoaUser(HttpUser):
    """
    TeamMoa 일반 사용자 시뮬레이션
    - 로그인 후 세션 유지
    - 팀 관리, TODO, 스케줄 등 주요 기능 사용
    """

    # 사용자 행동 대기 시간 (1~5초)
    wait_time = between(config.WAIT_TIME_MIN, config.WAIT_TIME_MAX)

    def on_start(self):
        """
        각 사용자가 시작할 때 실행 
        테스트 풀에서 랜덤으로 로그인
        """
        self.try_login()  # 실패 시 내부에서 StopUser


    def try_login(self):
        """로그인 재시도 로직"""
        MAX_RETRIES = 3
        for _ in range(MAX_RETRIES):
            self.user_index = random.randint(1, 300)
            self.username = f"loaduser{self.user_index}"
            self.password = config.TEST_USER_PASSWORD
            # 팀 ID 풀에서 인덱스로 선택
            self.team_id = TEAM_IDS[(self.user_index - 1) // 100]

            if self.login():
                return True

            gevent.sleep(random.uniform(1, 3))

        raise StopUser("로그인 최대 재시도 실패")


    def login(self):
        with self.client.post(
            "/api/v1/users/login/",
            data={
                "username": self.username,
                "password": self.password,
            },
            name="01_API_로그인",
            catch_response=True,
        ) as response:

            if response.status_code == 200 and "sessionid" in self.client.cookies:
                response.success()
                return True

            if response.status_code == 429:
                response.failure("429 Too Many Requests")
                return False

            response.failure(f"status {response.status_code}")
            return False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SSR (Server-Side Rendering) 시나리오
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @task(25)  # 가중치 25%
    def view_home(self):
        """홈 페이지 조회"""
        self.client.get("/", name="02_홈_페이지")

    @task(20) # 가중치 20%
    def view_teams(self):
        """팀 목록 조회 (순수 조회용)"""
        self.client.get(
            "/api/v1/teams/",
            name="03_API_팀_목록"
        )

    @task(15)  # 가중치 15%
    def view_team_detail(self):
        """팀 상세 정보 조회"""
        if not self.team_id:
            return

        self.client.get(
            f"/api/v1/teams/{self.team_id}/",
            name="04_API_팀_상세"
        )

    @task(10)  # 가중치 10%
    def view_shares(self):
        """공유 게시판 조회"""
        if not self.team_id:
            return

        self.client.get(
            f"/shares/{self.team_id}/",
            name="05_공유게시판"
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # API (REST API) 시나리오
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @task(15)  # 가중치 15%
    def api_todos(self):
        """TODO 목록 조회 (API)"""
        if self.team_id:
            self.client.get(
                f"/api/v1/teams/{self.team_id}/todos/",
                name="06_API_TODO_목록"
            )

    @task(10)  # 가중치 10%
    def api_schedules(self):
        """스케줄 조회 (API)"""
        if self.team_id:
            self.client.get(
                f"/api/v1/teams/{self.team_id}/schedules/",
                name="07_API_스케줄_조회"
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Health Check (로드밸런싱 확인용)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @task(5)  # 가중치 5% (가벼운 요청)
    def health_check(self):
        """Health Check 엔드포인트"""
        self.client.get("/health/", name="08_Health_Check")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Locust 이벤트 핸들러 (테스트 시작/종료 시 실행)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """테스트 시작 시 실행"""
    logger.info("=" * 60)
    logger.info("TeamMoa ALB 부하 테스트 시작")
    logger.info(f"대상 URL: {config.ALB_URL}")
    logger.info(f"동시 사용자: {config.MIN_USERS} → {config.MAX_USERS}")
    logger.info(f"테스트 시간: {config.TEST_DURATION}")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """테스트 종료 시 실행"""
    logger.info("=" * 60)
    logger.info("TeamMoa ALB 부하 테스트 종료")
    logger.info(f"결과 리포트: {config.REPORT_HTML}")
    logger.info("=" * 60)

    # 통계 요약 출력
    stats = environment.stats
    logger.info(f"총 요청 수: {stats.total.num_requests}")
    logger.info(f"총 실패 수: {stats.total.num_failures}")
    logger.info(f"평균 응답 시간: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"95%ile 응답 시간: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    logger.info(f"에러율: {stats.total.fail_ratio * 100:.2f}%")

    # SLA 체크
    p95_response_time = stats.total.get_response_time_percentile(0.95)
    error_rate = stats.total.fail_ratio * 100

    logger.info("=" * 60)
    logger.info("SLA 검증 결과:")

    if p95_response_time <= config.SLA_RESPONSE_TIME_P95:
        logger.info(f"✅ 95%ile 응답 시간: {p95_response_time:.2f}ms (목표: {config.SLA_RESPONSE_TIME_P95}ms)")
    else:
        logger.warning(f"❌ 95%ile 응답 시간: {p95_response_time:.2f}ms (목표: {config.SLA_RESPONSE_TIME_P95}ms)")

    if error_rate <= config.SLA_ERROR_RATE:
        logger.info(f"✅ 에러율: {error_rate:.2f}% (목표: {config.SLA_ERROR_RATE}%)")
    else:
        logger.warning(f"❌ 에러율: {error_rate:.2f}% (목표: {config.SLA_ERROR_RATE}%)")

    logger.info("=" * 60)
