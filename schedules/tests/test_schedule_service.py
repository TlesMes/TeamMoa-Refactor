"""
ScheduleService 서비스 레이어 테스트

비즈니스 로직:
- 주간 스케줄 저장 (JSON 기반)
- 팀 가용성 실시간 계산
- 날짜 범위 쿼리 최적화
"""
import pytest
from datetime import date, timedelta
from schedules.models import PersonalDaySchedule


@pytest.mark.django_db
class TestScheduleService:
    """ScheduleService 테스트"""

    # ================================
    # save_personal_schedule() 테스트
    # ================================

    def test_save_personal_schedule_success(self, host_teamuser, schedule_service, base_date):
        """주간 스케줄 정상 저장"""
        week_start = base_date
        schedule_data = {
            'time_9-1': True,  # 월요일 9시
            'time_14-1': True,  # 월요일 14시
            'time_9-2': True,  # 화요일 9시
        }

        updated_days = schedule_service.save_personal_schedule(
            team_user=host_teamuser,
            week_start=week_start,
            schedule_data=schedule_data
        )

        # 검증: 2일치 스케줄 저장됨
        assert updated_days == 2

        # 검증: DB에 실제 저장됨
        schedules = PersonalDaySchedule.objects.filter(owner=host_teamuser)
        assert schedules.count() == 2

        # 검증: 월요일 스케줄
        monday_schedule = schedules.get(date=week_start)
        assert 9 in monday_schedule.available_hours
        assert 14 in monday_schedule.available_hours
        assert len(monday_schedule.available_hours) == 2

        # 검증: 화요일 스케줄
        tuesday_schedule = schedules.get(date=week_start + timedelta(days=1))
        assert tuesday_schedule.available_hours == [9]

    def test_save_personal_schedule_full_week(self, host_teamuser, schedule_service, base_date):
        """7일 전체 스케줄 저장"""
        week_start = base_date
        schedule_data = {}

        # 7일간 9-18시 업무시간 체크
        for day in range(7):
            for hour in range(9, 19):
                schedule_data[f'time_{hour}-{day + 1}'] = True

        updated_days = schedule_service.save_personal_schedule(
            team_user=host_teamuser,
            week_start=week_start,
            schedule_data=schedule_data
        )

        # 검증
        assert updated_days == 7
        schedules = PersonalDaySchedule.objects.filter(owner=host_teamuser)
        assert schedules.count() == 7

        # 각 날짜별 10시간 저장 확인
        for schedule in schedules:
            assert len(schedule.available_hours) == 10

    def test_save_personal_schedule_overwrites_existing(
        self, host_teamuser, personal_schedule, schedule_service, base_date
    ):
        """기존 스케줄 덮어쓰기 (중복 방지)"""
        week_start = base_date

        # 기존 스케줄 확인
        assert PersonalDaySchedule.objects.filter(
            owner=host_teamuser,
            date=week_start
        ).count() == 1
        old_schedule = PersonalDaySchedule.objects.get(
            owner=host_teamuser,
            date=week_start
        )
        assert 9 in old_schedule.available_hours

        # 새 스케줄로 덮어쓰기 (저녁시간만)
        schedule_data = {
            'time_18-1': True,
            'time_19-1': True,
        }

        updated_days = schedule_service.save_personal_schedule(
            team_user=host_teamuser,
            week_start=week_start,
            schedule_data=schedule_data
        )

        # 검증: 여전히 1개만 존재
        assert updated_days == 1
        assert PersonalDaySchedule.objects.filter(
            owner=host_teamuser,
            date=week_start
        ).count() == 1

        # 검증: 데이터가 변경됨
        new_schedule = PersonalDaySchedule.objects.get(
            owner=host_teamuser,
            date=week_start
        )
        assert 18 in new_schedule.available_hours
        assert 19 in new_schedule.available_hours
        assert 9 not in new_schedule.available_hours  # 기존 데이터 삭제됨

    def test_save_personal_schedule_empty_hours(self, host_teamuser, schedule_service, base_date):
        """빈 시간대 처리 (체크 안 함)"""
        week_start = base_date
        schedule_data = {}  # 아무것도 체크 안 함

        updated_days = schedule_service.save_personal_schedule(
            team_user=host_teamuser,
            week_start=week_start,
            schedule_data=schedule_data
        )

        # 검증: 저장된 날짜 없음
        assert updated_days == 0
        assert PersonalDaySchedule.objects.filter(owner=host_teamuser).count() == 0

    def test_save_personal_schedule_partial_days(self, host_teamuser, schedule_service, base_date):
        """일부 요일만 선택"""
        week_start = base_date
        schedule_data = {
            'time_9-1': True,   # 월요일
            'time_9-3': True,   # 수요일
            'time_9-5': True,   # 금요일
        }

        updated_days = schedule_service.save_personal_schedule(
            team_user=host_teamuser,
            week_start=week_start,
            schedule_data=schedule_data
        )

        # 검증: 3일만 저장됨
        assert updated_days == 3
        schedules = PersonalDaySchedule.objects.filter(owner=host_teamuser)
        assert schedules.count() == 3

    def test_save_personal_schedule_invalid_date(self, host_teamuser, schedule_service):
        """잘못된 날짜 형식"""
        week_start = "2025-10-20"  # 문자열 (date 객체 아님)
        schedule_data = {'time_9-1': True}

        with pytest.raises(ValueError, match='유효하지 않은 날짜 형식'):
            schedule_service.save_personal_schedule(
                team_user=host_teamuser,
                week_start=week_start,
                schedule_data=schedule_data
            )

    # ================================
    # get_team_availability() 테스트
    # ================================

    def test_get_team_availability_single_member(
        self, team, personal_schedule, schedule_service, base_date
    ):
        """단일 멤버 가용성 조회"""
        start_date = base_date
        end_date = base_date

        result = schedule_service.get_team_availability(
            team=team,
            start_date=start_date,
            end_date=end_date
        )

        # 검증: 1일치 결과
        assert len(result) == 1
        assert result[0]['date'] == start_date

        # 검증: 9-18시 각각 1명
        availability = result[0]['availability']
        for hour in range(9, 19):
            assert availability[hour] == 1

        # 검증: 다른 시간대는 0명
        assert availability[0] == 0
        assert availability[23] == 0

    def test_get_team_availability_multiple_members(
        self, team, overlapping_schedules, schedule_service, base_date
    ):
        """다중 멤버 중복 시간대"""
        start_date = base_date
        end_date = base_date

        result = schedule_service.get_team_availability(
            team=team,
            start_date=start_date,
            end_date=end_date
        )

        # 검증: 겹치는 시간대 (9-11시) 2명
        availability = result[0]['availability']
        assert availability[9] == 2
        assert availability[10] == 2
        assert availability[11] == 2

        # 검증: 한 명만 있는 시간대
        assert availability[13] == 1  # team_user만
        assert availability[14] == 1  # team_user만
        assert availability[18] == 1  # another_team_user만
        assert availability[19] == 1  # another_team_user만

    def test_get_team_availability_no_schedules(
        self, team, schedule_service, base_date
    ):
        """스케줄이 없는 경우 (모두 0명)"""
        start_date = base_date
        end_date = base_date

        result = schedule_service.get_team_availability(
            team=team,
            start_date=start_date,
            end_date=end_date
        )

        # 검증: 모든 시간대 0명
        availability = result[0]['availability']
        for hour in range(24):
            assert availability[hour] == 0

    def test_get_team_availability_date_range(
        self, team, weekly_schedules, schedule_service, base_date
    ):
        """날짜 범위 쿼리 (7일)"""
        start_date = base_date
        end_date = start_date + timedelta(days=6)

        result = schedule_service.get_team_availability(
            team=team,
            start_date=start_date,
            end_date=end_date
        )

        # 검증: 7일치 결과
        assert len(result) == 7

        # 검증: 월~금 (처음 5일)은 1명, 토~일 (마지막 2일)은 0명
        for i in range(5):
            availability = result[i]['availability']
            assert availability[9] == 1  # 업무시간
            assert availability[0] == 0  # 새벽시간

        for i in range(5, 7):
            availability = result[i]['availability']
            assert availability[9] == 0  # 주말은 스케줄 없음

    def test_get_team_availability_optimized_query(
        self, team, weekly_schedules, schedule_service, django_assert_num_queries, base_date
    ):
        """쿼리 최적화 검증 (1개 쿼리로 처리)"""
        start_date = base_date
        end_date = start_date + timedelta(days=6)

        # 쿼리 수 검증: 1개만 실행되어야 함 (select_related 덕분)
        with django_assert_num_queries(1):
            schedule_service.get_team_availability(
                team=team,
                start_date=start_date,
                end_date=end_date
            )

    # ================================
    # 통합 시나리오 테스트
    # ================================

    def test_weekly_schedule_lifecycle(self, host_teamuser, schedule_service, base_date):
        """주간 스케줄 저장 → 조회 → 수정 시나리오"""
        week_start = base_date

        # 1. 초기 스케줄 저장
        schedule_data = {
            'time_9-1': True,
            'time_10-1': True,
        }
        updated_days = schedule_service.save_personal_schedule(
            team_user=host_teamuser,
            week_start=week_start,
            schedule_data=schedule_data
        )
        assert updated_days == 1

        # 2. 가용성 조회
        result = schedule_service.get_team_availability(
            team=host_teamuser.team,
            start_date=week_start,
            end_date=week_start
        )
        assert result[0]['availability'][9] == 1

        # 3. 스케줄 수정
        schedule_data_updated = {
            'time_14-1': True,
            'time_15-1': True,
        }
        updated_days = schedule_service.save_personal_schedule(
            team_user=host_teamuser,
            week_start=week_start,
            schedule_data=schedule_data_updated
        )
        assert updated_days == 1

        # 4. 변경사항 확인
        result = schedule_service.get_team_availability(
            team=host_teamuser.team,
            start_date=week_start,
            end_date=week_start
        )
        availability = result[0]['availability']
        assert availability[9] == 0   # 기존 데이터 삭제됨
        assert availability[14] == 1  # 새 데이터
        assert availability[15] == 1
