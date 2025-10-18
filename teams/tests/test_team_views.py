"""
Teams App SSR/AJAX 뷰 테스트

핵심 Form 기반 뷰와 AJAX 엔드포인트만 테스트합니다.

테스트 대상:
✅ Form 기반 뷰: team_create, team_info_change, team_disband
✅ AJAX 엔드포인트: team_verify_code, team_join_process
✅ 렌더링 확인: main_page, team_search
"""
import pytest
from django.urls import reverse
from teams.models import Team, TeamUser


@pytest.mark.django_db
class TestMainPageView:
    """메인 페이지 렌더링 테스트"""

    def test_main_page_authenticated_user(self, client, user):
        """로그인한 사용자는 팀 목록 페이지 렌더링"""
        client.force_login(user)
        url = reverse('teams:main_page')
        response = client.get(url)

        assert response.status_code == 200
        assert 'teams/main_authenticated.html' in [t.name for t in response.templates]

    def test_main_page_unauthenticated_user(self, client):
        """비로그인 사용자는 랜딩 페이지 렌더링"""
        url = reverse('teams:main_page')
        response = client.get(url)

        assert response.status_code == 200
        assert 'teams/main_landing.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestTeamCreateView:
    """팀 생성 Form 뷰 테스트"""

    def test_team_create_get(self, client, user):
        """팀 생성 폼 페이지 렌더링"""
        client.force_login(user)
        url = reverse('teams:team_create')
        response = client.get(url)

        assert response.status_code == 200
        assert 'teams/team_create.html' in [t.name for t in response.templates]

    def test_team_create_post_success(self, client, user):
        """정상적으로 팀 생성"""
        client.force_login(user)
        url = reverse('teams:team_create')
        data = {
            'title': '새 테스트 팀',
            'maxuser': 10,
            'teampasswd': 'newteam123',
            'introduction': '새로운 팀입니다'
        }
        response = client.post(url, data)

        # 성공 시 리다이렉트
        assert response.status_code == 302
        assert response.url == reverse('teams:main_page')

        # DB에 팀 생성 확인
        team = Team.objects.get(title='새 테스트 팀')
        assert team.host == user
        assert TeamUser.objects.filter(team=team, user=user).exists()

    def test_team_create_post_invalid_data(self, client, user):
        """유효하지 않은 데이터로 팀 생성 실패"""
        client.force_login(user)
        url = reverse('teams:team_create')
        data = {
            'title': '',  # 빈 제목
            'maxuser': 10,
            'teampasswd': 'password'
        }
        response = client.post(url, data)

        # 폼 에러로 다시 렌더링
        assert response.status_code == 200
        assert not Team.objects.filter(title='').exists()


@pytest.mark.django_db
class TestTeamSearchView:
    """팀 검색 페이지 렌더링 테스트"""

    def test_team_search_get(self, client, user):
        """팀 검색 페이지 렌더링"""
        client.force_login(user)
        url = reverse('teams:team_search')
        response = client.get(url)

        assert response.status_code == 200
        assert 'teams/team_search.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestTeamVerifyCodeAjax:
    """팀 코드 검증 AJAX 엔드포인트 테스트"""

    def test_verify_code_success(self, client, team, another_user):
        """유효한 팀 코드 검증 성공"""
        client.force_login(another_user)
        url = reverse('teams:team_verify_code')
        response = client.post(url, {'invitecode': 'TEST1234'})

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['team']['title'] == '테스트팀'
        assert data['team']['id'] == team.id

    def test_verify_code_invalid(self, client, user):
        """존재하지 않는 팀 코드"""
        client.force_login(user)
        url = reverse('teams:team_verify_code')
        response = client.post(url, {'invitecode': 'INVALID'})

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False
        assert '유효하지 않은' in data['error'] or '존재하지 않는' in data['error']

    def test_verify_code_already_member(self, client, team, user):
        """이미 가입한 팀"""
        client.force_login(user)
        url = reverse('teams:team_verify_code')
        response = client.post(url, {'invitecode': 'TEST1234'})

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False
        assert '이미' in data['error']


@pytest.mark.django_db
class TestTeamJoinProcessAjax:
    """팀 가입 처리 AJAX 엔드포인트 테스트"""

    def test_join_team_success(self, client, team, another_user):
        """정상적으로 팀 가입"""
        client.force_login(another_user)
        url = reverse('teams:team_join_process')
        response = client.post(url, {
            'team_id': team.id,
            'teampasswd': 'teampass123'
        })

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert '성공' in data['message']
        assert TeamUser.objects.filter(team=team, user=another_user).exists()

    def test_join_team_wrong_password(self, client, team, another_user):
        """잘못된 비밀번호로 가입 시도"""
        client.force_login(another_user)
        url = reverse('teams:team_join_process')
        response = client.post(url, {
            'team_id': team.id,
            'teampasswd': 'wrongpassword'
        })

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False
        assert '비밀번호' in data['error']
        assert not TeamUser.objects.filter(team=team, user=another_user).exists()


@pytest.mark.django_db
class TestTeamInfoChangeView:
    """팀 정보 수정 Form 뷰 테스트"""

    def test_team_info_change_by_host(self, client, team, user):
        """팀장이 팀 정보 수정"""
        client.force_login(user)
        url = reverse('teams:team_info_change', kwargs={'pk': team.id})
        data = {
            'title': '수정된 팀 이름',
            'maxuser': 15,
            'introduction': '수정된 소개'
        }
        response = client.post(url, data)

        # 성공 시 팀 메인으로 리다이렉트
        assert response.status_code == 302

        # DB에서 변경 확인
        team.refresh_from_db()
        assert team.title == '수정된 팀 이름'
        assert team.maxuser == 15

    def test_team_info_change_by_non_host(self, client, team, another_user):
        """일반 멤버는 팀 정보 수정 불가"""
        TeamUser.objects.create(team=team, user=another_user)
        client.force_login(another_user)
        url = reverse('teams:team_info_change', kwargs={'pk': team.id})
        response = client.get(url)

        # 권한 없음 (403 또는 리다이렉트)
        assert response.status_code in [302, 403]


@pytest.mark.django_db
class TestTeamDisbandView:
    """팀 해체 뷰 테스트"""

    def test_disband_team_by_host(self, client, team, user):
        """팀장이 팀 해체"""
        client.force_login(user)
        url = reverse('teams:team_disband', kwargs={'pk': team.id})
        response = client.post(url)

        # 성공 시 메인으로 리다이렉트
        assert response.status_code == 302
        assert response.url == reverse('teams:main_page')

        # DB에서 팀 삭제 확인
        assert not Team.objects.filter(id=team.id).exists()

    def test_disband_team_by_non_host(self, client, team, another_user):
        """일반 멤버는 팀 해체 불가"""
        TeamUser.objects.create(team=team, user=another_user)
        client.force_login(another_user)
        url = reverse('teams:team_disband', kwargs={'pk': team.id})
        response = client.post(url)

        # 권한 없음 (403 또는 리다이렉트)
        assert response.status_code in [302, 403]

        # 팀은 여전히 존재
        assert Team.objects.filter(id=team.id).exists()
