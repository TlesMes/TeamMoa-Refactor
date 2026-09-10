"""
로컬 한계점 탐색용 Locust 시나리오 (2026-09-10)

기존 docs/guides/load-testing/locustfile.py 에서 바뀐 점:
 1. wait_time 을 config에서 읽어 0.5~1초로 낮춤 (VU당 부하 밀도 상승)
 2. 로그인을 VU 인덱스 결정론적으로 배분 (랜덤 재시도 루프 제거)
    → 로그인 실패가 조용히 묻히지 않고 드러난다
 3. 로그인 실패 시 즉시 StopUser + 카운터 집계
    → "로그인이 안 돼서 부하가 안 걸린 것"을 서버 여유로 오독하지 않게 한다
 4. 시나리오 가중치와 엔드포인트는 원본과 동일하게 유지 (비교 가능성 확보)
"""
import itertools
import logging

from locust import HttpUser, between, events, task
from locust.exception import StopUser

import config

logger = logging.getLogger(__name__)

# VU에 사용자 계정을 겹치지 않게 순번으로 배분한다.
# --processes 로 워커를 여러 개 띄우면 각 프로세스가 별도 카운터를 갖는다.
# 워커 인덱스만큼 시작점을 밀어 계정이 프로세스 간에 겹치지 않게 한다.
_user_counter = itertools.count(1)
_worker_offset = {"value": 0}

LOGIN_FAILURES = {"count": 0}


class TeamMoaUser(HttpUser):
    wait_time = between(config.WAIT_TIME_MIN, config.WAIT_TIME_MAX)

    def on_start(self):
        idx = next(_user_counter) + _worker_offset["value"]
        # 300개 계정을 순환 사용 (VU가 300을 넘으면 계정을 공유하게 된다)
        self.user_index = ((idx - 1) % config.USERS_TOTAL) + 1
        self.username = f"loaduser{self.user_index}"
        self.password = config.TEST_USER_PASSWORD

        per_team = config.USERS_TOTAL // len(config.TEAM_IDS)
        self.team_id = config.TEAM_IDS[min((self.user_index - 1) // per_team,
                                           len(config.TEAM_IDS) - 1)]

        if not self.login():
            LOGIN_FAILURES["count"] += 1
            raise StopUser("로그인 실패")

    def login(self):
        with self.client.post(
            "/api/v1/users/login/",
            data={"username": self.username, "password": self.password},
            name="01_API_로그인",
            catch_response=True,
        ) as r:
            if r.status_code == 200 and "sessionid" in self.client.cookies:
                r.success()
                return True
            r.failure(f"status {r.status_code}")
            return False

    # ── SSR ──────────────────────────────────────────
    @task(25)
    def view_home(self):
        self.client.get("/", name="02_홈_페이지")

    @task(20)
    def view_teams(self):
        self.client.get("/api/v1/teams/", name="03_API_팀_목록")

    @task(15)
    def view_team_detail(self):
        self.client.get(f"/api/v1/teams/{self.team_id}/", name="04_API_팀_상세")

    @task(10)
    def view_shares(self):
        self.client.get(f"/shares/{self.team_id}/", name="05_공유게시판")

    # ── API ──────────────────────────────────────────
    @task(15)
    def api_todos(self):
        self.client.get(f"/api/v1/teams/{self.team_id}/todos/", name="06_API_TODO_목록")

    @task(10)
    def api_schedules(self):
        self.client.get(f"/api/v1/teams/{self.team_id}/schedules/", name="07_API_스케줄_조회")

    @task(5)
    def health_check(self):
        self.client.get("/health/", name="08_Health_Check")


@events.init.add_listener
def on_init(environment, **kwargs):
    """워커 프로세스마다 계정 배분 시작점을 다르게 잡는다."""
    idx = getattr(environment.runner, "worker_index", 0) or 0
    _worker_offset["value"] = idx * (config.USERS_TOTAL // max(config.LOCUST_PROCESSES, 1))


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    LOGIN_FAILURES["count"] = 0
    logger.info("=" * 60)
    logger.info(f"대상: {config.TARGET_URL}  팀: {config.TEAM_IDS}")
    logger.info(f"wait_time: {config.WAIT_TIME_MIN}~{config.WAIT_TIME_MAX}s")
    logger.info(f"중단 조건: p95 > {config.STOP_P95_MS}ms 또는 에러율 > {config.STOP_ERROR_RATE}%")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    s = environment.stats.total
    p95 = s.get_response_time_percentile(0.95)
    err = s.fail_ratio * 100
    logger.info("=" * 60)
    logger.info(f"요청 {s.num_requests} / 실패 {s.num_failures}")
    logger.info(f"평균 {s.avg_response_time:.1f}ms / p95 {p95:.1f}ms / 에러율 {err:.2f}%")
    logger.info(f"로그인 실패로 중단된 VU: {LOGIN_FAILURES['count']}")

    breached = []
    if p95 > config.STOP_P95_MS:
        breached.append(f"p95 {p95:.1f}ms > {config.STOP_P95_MS}ms")
    if err > config.STOP_ERROR_RATE:
        breached.append(f"에러율 {err:.2f}% > {config.STOP_ERROR_RATE}%")
    logger.info("중단 조건 위반: " + (", ".join(breached) if breached else "없음"))
    logger.info("=" * 60)
