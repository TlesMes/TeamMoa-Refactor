"""
Schedules 앱 전용 pytest fixtures
"""
import pytest
from datetime import date, timedelta
from schedules.models import PersonalDaySchedule
from schedules.services import ScheduleService
from teams.models import TeamUser


# ================================
# 상수 정의
# ================================

# 테스트 기준 날짜 (2025-10-20 월요일)
TEST_BASE_DATE = date(2025, 10, 20)

# 시간대 상수 (가독성 및 유지보수성 향상)
BUSINESS_HOURS = list(range(9, 19))  # 9-18시 (업무시간)
EVENING_HOURS = list(range(18, 23))  # 18-22시 (저녁시간)
MORNING_HOURS = list(range(9, 13))   # 9-12시 (오전)
AFTERNOON_HOURS = list(range(13, 19))  # 13-18시 (오후)

WEEKDAYS = 5  # 월~금


# ================================
# 서비스 및 도메인 객체 Fixtures
# ================================

@pytest.fixture
def schedule_service():
    """ScheduleService 인스턴스"""
    return ScheduleService()


@pytest.fixture(scope="session")
def base_date():
    """
    테스트 기준 날짜 (고정)

    Returns:
        date: 2025-10-20 (월요일)

    Note:
        테스트 재현성을 위해 고정된 날짜 사용
        scope="session"으로 전체 테스트 세션에서 한 번만 생성
    """
    return TEST_BASE_DATE


@pytest.fixture
def host_teamuser(db, team, user):
    """
    팀장 TeamUser (Members 앱과 네이밍 일관성 유지)

    Note:
        db fixture는 Django DB 접근을 위해 필요 (암묵적 사용)
    """
    return TeamUser.objects.get(team=team, user=user)


@pytest.fixture
def member_teamuser(db, team, another_user):
    """
    일반 멤버 TeamUser (Members 앱과 네이밍 일관성 유지)

    Note:
        db fixture는 Django DB 접근을 위해 필요 (암묵적 사용)
    """
    teamuser = TeamUser.objects.create(team=team, user=another_user)
    team.currentuser += 1
    team.save()
    return teamuser


# ================================
# 스케줄 데이터 Fixtures
# ================================

@pytest.fixture
def personal_schedule(db, host_teamuser, base_date):
    """
    개인 스케줄 (업무시간 9-18시)

    사용 시나리오:
    - 단일 멤버 가용성 테스트
    - 기본 CRUD 테스트
    """
    return PersonalDaySchedule.objects.create(
        owner=host_teamuser,
        date=base_date,
        available_hours=BUSINESS_HOURS
    )


@pytest.fixture
def weekly_schedules(db, host_teamuser, base_date):
    """
    주간 스케줄 (월~금, 업무시간)

    사용 시나리오:
    - 날짜 범위 쿼리 테스트
    - 주간 가용성 계산 테스트
    """
    schedules = []

    for day_offset in range(WEEKDAYS):
        schedule = PersonalDaySchedule.objects.create(
            owner=host_teamuser,
            date=base_date + timedelta(days=day_offset),
            available_hours=BUSINESS_HOURS
        )
        schedules.append(schedule)

    return schedules


@pytest.fixture
def another_schedule(db, member_teamuser, base_date):
    """
    다른 멤버의 스케줄 (저녁시간 18-22시)

    사용 시나리오:
    - 다중 멤버 비교 테스트
    """
    return PersonalDaySchedule.objects.create(
        owner=member_teamuser,
        date=base_date,
        available_hours=EVENING_HOURS
    )


@pytest.fixture
def overlapping_schedules(db, host_teamuser, member_teamuser, base_date):
    """
    겹치는 시간대가 있는 두 멤버의 스케줄

    구조:
    - host_teamuser: 9-14시 (오전 + 점심)
    - member_teamuser: 9-12시, 18-20시 (오전 + 저녁)
    - 중복 시간대: 9-12시 (2명)

    사용 시나리오:
    - 팀 가용성 중복 계산 테스트
    - 다중 사용자 스케줄 병합 테스트
    """
    schedule1 = PersonalDaySchedule.objects.create(
        owner=host_teamuser,
        date=base_date,
        available_hours=MORNING_HOURS + [13, 14]  # 9-14시
    )
    schedule2 = PersonalDaySchedule.objects.create(
        owner=member_teamuser,
        date=base_date,
        available_hours=MORNING_HOURS + [18, 19, 20]  # 9-12시, 18-20시
    )
    return [schedule1, schedule2]
