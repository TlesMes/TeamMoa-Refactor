"""
TeamMoa 프로젝트 공통 pytest fixtures

모든 앱에서 공통으로 사용하는 기본 fixture들을 정의합니다.
"""
import pytest
from django.contrib.auth import get_user_model
from teams.models import Team, TeamUser

User = get_user_model()


@pytest.fixture
def user(db):
    """기본 테스트 사용자"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123!',
        nickname='테스터',
        is_active=True
    )


@pytest.fixture
def another_user(db):
    """추가 테스트 사용자 (권한 테스트용)"""
    return User.objects.create_user(
        username='anotheruser',
        email='another@example.com',
        password='testpass123!',
        nickname='다른유저',
        is_active=True
    )


@pytest.fixture
def third_user(db):
    """세 번째 테스트 사용자 (다중 멤버 테스트용)"""
    return User.objects.create_user(
        username='thirduser',
        email='third@example.com',
        password='testpass123!',
        nickname='세번째유저',
        is_active=True
    )


@pytest.fixture
def team(db, user):
    """기본 팀 (user가 호스트)"""
    team = Team.objects.create(
        title='테스트팀',
        maxuser=10,
        teampasswd='teampass123',
        introduction='테스트용 팀입니다',
        host=user,
        currentuser=1,
        invitecode='TEST1234'
    )
    TeamUser.objects.create(team=team, user=user)
    return team


@pytest.fixture
def api_client():
    """DRF API 테스트 클라이언트"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """인증된 API 클라이언트"""
    api_client.force_authenticate(user=user)
    return api_client
