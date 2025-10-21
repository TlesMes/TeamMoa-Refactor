"""
Schedules SSR 뷰 테스트

템플릿 뷰:
- scheduler_page: 팀 스케줄 조회 페이지
- scheduler_upload_page: 개인 스케줄 업로드 페이지
"""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from django.contrib.messages import get_messages
from schedules.models import PersonalDaySchedule


@pytest.mark.django_db
class TestScheduleViews:
    """Schedules SSR 뷰 테스트"""

    # ================================
    # scheduler_page 뷰 테스트
    # ================================

    def test_scheduler_page_get_success(self, client, user, team):
        """팀 멤버 스케줄 페이지 접근 성공"""
        client.force_login(user)
        url = reverse('schedules:scheduler_page', kwargs={'pk': team.pk})

        response = client.get(url)

        # 검증: 응답 성공
        assert response.status_code == 200
        assert 'team' in response.context
        assert response.context['team'] == team
        assert 'selected_week' in response.context

        # 검증: 템플릿 사용
        assert 'schedules/scheduler_page.html' in [t.name for t in response.templates]

    def test_scheduler_page_non_member_redirect(self, client, another_user, team):
        """비멤버는 접근 불가 (리다이렉트)"""
        client.force_login(another_user)
        url = reverse('schedules:scheduler_page', kwargs={'pk': team.pk})

        response = client.get(url)

        # 검증: 리다이렉트
        assert response.status_code == 302

    def test_scheduler_page_unauthenticated_redirect(self, client, team):
        """비로그인 사용자 리다이렉트"""
        url = reverse('schedules:scheduler_page', kwargs={'pk': team.pk})

        response = client.get(url)

        # 검증: 로그인 페이지로 리다이렉트
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    # ================================
    # scheduler_upload_page 뷰 테스트
    # ================================

    def test_scheduler_upload_page_get_success(self, client, user, team):
        """스케줄 업로드 페이지 접근 성공"""
        client.force_login(user)
        url = reverse('schedules:scheduler_upload_page', kwargs={'pk': team.pk})

        response = client.get(url)

        # 검증: 응답 성공
        assert response.status_code == 200
        assert 'team' in response.context
        assert response.context['team'] == team

        # 검증: 템플릿 사용
        assert 'schedules/scheduler_upload_page.html' in [t.name for t in response.templates]

    def test_scheduler_upload_page_post_success(self, client, user, team, host_teamuser):
        """스케줄 업로드 POST 성공"""
        client.force_login(user)
        url = reverse('schedules:scheduler_upload_page', kwargs={'pk': team.pk})

        # POST 데이터 (월요일 9-10시)
        data = {
            'week': str(date.today()),
            'time_9-1': 'on',
            'time_10-1': 'on',
        }

        response = client.post(url, data)

        # 검증: 스케줄 페이지로 리다이렉트
        assert response.status_code == 302
        assert response.url == reverse('schedules:scheduler_page', kwargs={'pk': team.pk})

        # 검증: 성공 메시지
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert '성공적으로 업로드' in str(messages[0])

        # 검증: DB에 저장됨
        schedule = PersonalDaySchedule.objects.get(
            owner=host_teamuser,
            date=date.today()
        )
        assert 9 in schedule.available_hours
        assert 10 in schedule.available_hours

    def test_scheduler_upload_page_post_empty_schedule(
        self, client, user, team
    ):
        """빈 스케줄 업로드 (시간대 선택 안 함)"""
        client.force_login(user)
        url = reverse('schedules:scheduler_upload_page', kwargs={'pk': team.pk})

        data = {
            'week': str(date.today()),
            # 체크박스 선택 안 함
        }

        response = client.post(url, data)

        # 검증: 리다이렉트
        assert response.status_code == 302

        # 검증: 정보 메시지
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert '가능 시간이 없습니다' in str(messages[0])

        # 검증: DB에 저장 안 됨
        assert PersonalDaySchedule.objects.count() == 0

    def test_scheduler_upload_page_post_invalid_week(
        self, client, user, team
    ):
        """잘못된 주차 형식"""
        client.force_login(user)
        url = reverse('schedules:scheduler_upload_page', kwargs={'pk': team.pk})

        data = {
            'week': 'invalid-date',
            'time_9-1': 'on',
        }

        response = client.post(url, data)

        # 검증: 에러 처리 (페이지 재렌더링)
        assert response.status_code == 200

        # 검증: 에러 메시지
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) >= 1

    def test_scheduler_upload_page_post_missing_week(
        self, client, user, team
    ):
        """주차 파라미터 누락"""
        client.force_login(user)
        url = reverse('schedules:scheduler_upload_page', kwargs={'pk': team.pk})

        data = {
            # week 누락
            'time_9-1': 'on',
        }

        response = client.post(url, data)

        # 검증: 에러 처리
        assert response.status_code == 200

        # 검증: 에러 메시지
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) >= 1
        assert '주간을 선택해주세요' in str(messages[0])

    def test_scheduler_upload_page_non_member(self, client, another_user, team):
        """비멤버는 업로드 불가"""
        client.force_login(another_user)
        url = reverse('schedules:scheduler_upload_page', kwargs={'pk': team.pk})

        data = {
            'week': str(date.today()),
            'time_9-1': 'on',
        }

        response = client.post(url, data)

        # 검증: 리다이렉트 (권한 없음)
        assert response.status_code == 302
