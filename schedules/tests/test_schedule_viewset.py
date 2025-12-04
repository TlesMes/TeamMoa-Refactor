"""
Schedules API 테스트 (13개)

테스트 구성:
- TestScheduleViewSet: 13개 - 개인 스케줄 저장, 팀 가용성 조회, 내 스케줄 조회

REST API 엔드포인트:
- POST /api/v1/teams/{team_pk}/schedules/save-personal/
- GET /api/v1/teams/{team_pk}/schedules/team-availability/
- GET /api/v1/teams/{team_pk}/schedules/my-schedule/
"""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from schedules.models import PersonalDaySchedule


@pytest.mark.django_db
class TestScheduleViewSet:
    """ScheduleViewSet API 테스트"""

    # ================================
    # save_personal_schedule 액션 테스트
    # ================================

    def test_save_personal_schedule_success(self, authenticated_client, team, host_teamuser, base_date):
        """인증된 팀 멤버 스케줄 저장 성공"""
        url = reverse('api:team-schedules-save-personal', kwargs={'team_pk': team.pk})
        data = {
            'week_start': str(base_date),
            'schedule_data': {
                'time_9-1': True,
                'time_10-1': True,
                'time_14-1': True,
            }
        }

        response = authenticated_client.post(url, data, format='json')

        # 검증: 응답 성공
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['messages']) > 0
        assert '스케줄이 성공적으로 저장' in response.data['messages'][0]['message']
        assert response.data['updated_days'] == 1

        # 검증: DB에 저장됨
        schedule = PersonalDaySchedule.objects.get(
            owner=host_teamuser,
            date=base_date
        )
        assert 9 in schedule.available_hours
        assert 10 in schedule.available_hours
        assert 14 in schedule.available_hours

    def test_save_personal_schedule_full_week(self, authenticated_client, team, base_date):
        """7일 전체 스케줄 저장"""
        url = reverse('api:team-schedules-save-personal', kwargs={'team_pk': team.pk})
        schedule_data = {}

        # 7일간 업무시간 체크
        for day in range(7):
            for hour in range(9, 19):
                schedule_data[f'time_{hour}-{day + 1}'] = True

        data = {
            'week_start': str(base_date),
            'schedule_data': schedule_data
        }

        response = authenticated_client.post(url, data, format='json')

        # 검증
        assert response.status_code == status.HTTP_200_OK
        assert response.data['updated_days'] == 7

    def test_save_personal_schedule_unauthenticated(self, api_client, team, base_date):
        """비인증 사용자 401 (또는 403)"""
        url = reverse('api:team-schedules-save-personal', kwargs={'team_pk': team.pk})
        data = {
            'week_start': str(base_date),
            'schedule_data': {'time_9-1': True}
        }

        response = api_client.post(url, data, format='json')

        # 검증: 인증/권한 실패 (DRF는 비인증 시 403 반환할 수도 있음)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_save_personal_schedule_non_member(
        self, authenticated_client, team, another_user, base_date
    ):
        """비멤버 403 (팀에 속하지 않은 사용자)"""
        # authenticated_client는 user로 인증됨, 다른 팀 생성
        from teams.models import Team, TeamUser
        other_team = Team.objects.create(
            title='다른팀',
            maxuser=10,
            currentuser=1,
            teampasswd='pass123',
            introduction='다른 팀입니다',
            host=another_user,
            invitecode='OTHER123'
        )
        TeamUser.objects.create(team=other_team, user=another_user)

        # user는 other_team의 멤버가 아님
        url = reverse('api:team-schedules-save-personal', kwargs={'team_pk': other_team.pk})
        data = {
            'week_start': str(base_date),
            'schedule_data': {'time_9-1': True}
        }

        response = authenticated_client.post(url, data, format='json')

        # 검증: 권한 없음
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_save_personal_schedule_invalid_week_start(
        self, authenticated_client, team
    ):
        """잘못된 날짜 형식"""
        url = reverse('api:team-schedules-save-personal', kwargs={'team_pk': team.pk})
        data = {
            'week_start': 'invalid-date',
            'schedule_data': {'time_9-1': True}
        }

        response = authenticated_client.post(url, data, format='json')

        # 검증: Serializer 유효성 검사 실패
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_save_personal_schedule_missing_fields(
        self, authenticated_client, team, base_date
    ):
        """필수 필드 누락"""
        url = reverse('api:team-schedules-save-personal', kwargs={'team_pk': team.pk})
        data = {
            'week_start': str(base_date)
            # schedule_data 누락
        }

        response = authenticated_client.post(url, data, format='json')

        # 검증: Serializer 유효성 검사 실패
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ================================
    # get_team_availability 액션 테스트
    # ================================

    def test_get_team_availability_success(
        self, authenticated_client, team, personal_schedule, base_date
    ):
        """팀 가용성 조회 성공"""
        url = reverse('api:team-schedules-availability', kwargs={'team_pk': team.pk})
        params = {
            'start_date': str(base_date),
            'end_date': str(base_date)
        }

        response = authenticated_client.get(url, params)

        # 검증: 응답 성공
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']) == 1

        # 검증: 가용성 데이터 구조
        availability_data = response.data['data'][0]
        assert 'date' in availability_data
        assert 'availability' in availability_data

        # 검증: 9-18시 각각 1명
        availability = availability_data['availability']
        assert availability['9'] == 1
        assert availability['18'] == 1

    def test_get_team_availability_date_range(
        self, authenticated_client, team, weekly_schedules, base_date
    ):
        """날짜 범위 조회 (7일)"""
        url = reverse('api:team-schedules-availability', kwargs={'team_pk': team.pk})
        start_date = base_date
        end_date = start_date + timedelta(days=6)

        params = {
            'start_date': str(start_date),
            'end_date': str(end_date)
        }

        response = authenticated_client.get(url, params)

        # 검증: 7일치 데이터
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 7

    def test_get_team_availability_invalid_date_format(
        self, authenticated_client, team, base_date
    ):
        """잘못된 날짜 형식 400"""
        url = reverse('api:team-schedules-availability', kwargs={'team_pk': team.pk})
        params = {
            'start_date': 'invalid',
            'end_date': str(base_date)
        }

        response = authenticated_client.get(url, params)

        # 검증: Serializer 유효성 검사 실패
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_team_availability_missing_params(
        self, authenticated_client, team
    ):
        """쿼리 파라미터 누락 400"""
        url = reverse('api:team-schedules-availability', kwargs={'team_pk': team.pk})

        response = authenticated_client.get(url)

        # 검증: 필수 파라미터 누락
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ================================
    # get_my_schedule 액션 테스트
    # ================================

    def test_get_my_schedule_success(
        self, authenticated_client, team, personal_schedule, base_date
    ):
        """내 스케줄 조회 성공"""
        url = reverse('api:team-schedules-my-schedule', kwargs={'team_pk': team.pk})
        params = {
            'start_date': str(base_date),
            'end_date': str(base_date)
        }

        response = authenticated_client.get(url, params)

        # 검증: 응답 성공
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']) == 1

        # 검증: 내 스케줄 데이터
        my_schedule = response.data['data'][0]
        assert 'date' in my_schedule
        assert 'available_hours' in my_schedule
        assert 9 in my_schedule['available_hours']

    def test_get_my_schedule_empty(self, authenticated_client, team, base_date):
        """스케줄이 없는 경우 빈 배열"""
        url = reverse('api:team-schedules-my-schedule', kwargs={'team_pk': team.pk})
        params = {
            'start_date': str(base_date),
            'end_date': str(base_date)
        }

        response = authenticated_client.get(url, params)

        # 검증: 빈 배열
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data'] == []

    def test_get_my_schedule_date_range(
        self, authenticated_client, team, weekly_schedules, base_date
    ):
        """날짜 범위 조회 (7일)"""
        url = reverse('api:team-schedules-my-schedule', kwargs={'team_pk': team.pk})
        start_date = base_date
        end_date = start_date + timedelta(days=6)

        params = {
            'start_date': str(start_date),
            'end_date': str(end_date)
        }

        response = authenticated_client.get(url, params)

        # 검증: 5일치 데이터 (weekly_schedules는 5일만 생성)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 5
