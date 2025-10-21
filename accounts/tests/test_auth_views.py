"""
Accounts 앱 SSR 뷰 테스트 (10개)

역할: 폼, 리다이렉트, 템플릿, 세션 플로우 검증
"""
import pytest
from django.urls import reverse
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from accounts.tokens import account_activation_token
from accounts.tests.conftest import create_inactive_user, create_active_user, TEST_PASSWORD


@pytest.fixture
def client_with_user(client, db):
    """로그인된 클라이언트 (재사용 fixture)"""
    user = create_active_user(username='loggedin', email='loggedin@example.com')
    client.force_login(user)
    return client, user


class TestSignupFlow:
    """회원가입 플로우 테스트 (3개)"""

    def test_signup_view_renders_form(self, client, db):
        """GET 요청 시 폼 렌더링"""
        url = reverse('accounts:signup')
        response = client.get(url)

        assert response.status_code == 200
        assert 'form' in response.context
        assert 'username' in response.content.decode()

    def test_signup_view_redirects_on_success(self, client, db):
        """POST 성공 → signup_success로 리다이렉트"""
        url = reverse('accounts:signup')
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'nickname': '신규유저',
            'password': TEST_PASSWORD,
            'password2': TEST_PASSWORD
        }

        mail.outbox = []
        response = client.post(url, data=form_data)

        assert response.status_code == 302
        assert reverse('accounts:signup_success') in response.url
        assert len(mail.outbox) == 1  # 이메일 발송 확인

    def test_activation_view_activates_and_redirects(self, client, db):
        """인증 링크 클릭 → 활성화 + 리다이렉트"""
        user = create_inactive_user(username='activate_view_test')

        uid64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        url = reverse('accounts:activate', kwargs={'uid64': uid64, 'token': token})

        response = client.get(url)

        assert response.status_code == 302  # 리다이렉트
        user.refresh_from_db()
        assert user.is_active is True


class TestLoginLogoutFlow:
    """로그인/로그아웃 플로우 테스트 (4개)"""

    def test_login_view_renders_form(self, client, db):
        """GET 요청 시 폼 렌더링"""
        url = reverse('accounts:login')
        response = client.get(url)

        assert response.status_code == 200
        assert 'form' in response.context or 'username' in response.content.decode()

    def test_login_view_creates_session_on_success(self, client, db):
        """POST 성공 → 세션 생성"""
        user = create_active_user(username='sessiontest', password=TEST_PASSWORD)
        url = reverse('accounts:login')

        credentials = {
            'username': 'sessiontest',
            'password': TEST_PASSWORD
        }
        response = client.post(url, data=credentials)

        assert response.status_code == 302  # 성공 시 리다이렉트
        assert '_auth_user_id' in client.session
        assert int(client.session['_auth_user_id']) == user.pk

    def test_logout_view_destroys_session(self, client_with_user):
        """로그아웃 → 세션 삭제"""
        client, user = client_with_user
        url = reverse('accounts:logout')

        # 로그인 상태 확인
        assert '_auth_user_id' in client.session

        response = client.get(url)

        assert response.status_code == 302  # 리다이렉트
        assert '_auth_user_id' not in client.session

    def test_protected_view_redirects_after_logout(self, client_with_user):
        """로그아웃 후 보호 페이지 차단"""
        client, user = client_with_user
        profile_url = reverse('accounts:update')

        # 로그인 상태에서 접근 가능
        response = client.get(profile_url)
        assert response.status_code == 200

        # 로그아웃
        client.logout()

        # 로그아웃 후 접근 차단
        response = client.get(profile_url)
        assert response.status_code == 302  # 로그인 페이지로 리다이렉트
        assert '/accounts/login' in response.url


class TestProfileAndPasswordManagement:
    """프로필 및 비밀번호 관리 테스트 (3개)"""

    def test_profile_update_view_requires_login(self, client, db):
        """로그인 없이 접근 차단"""
        url = reverse('accounts:update')
        response = client.get(url)

        assert response.status_code == 302  # 로그인 페이지로 리다이렉트
        assert '/accounts/login' in response.url

    def test_profile_update_view_changes_nickname(self, client_with_user):
        """프로필 수정 성공"""
        client, user = client_with_user
        url = reverse('accounts:update')

        new_data = {
            'nickname': '변경된닉네임',
            'profile': '새로운 프로필 설명'
        }
        response = client.post(url, data=new_data)

        assert response.status_code in [200, 302]  # 성공 또는 리다이렉트
        user.refresh_from_db()
        assert user.nickname == '변경된닉네임'

    def test_password_change_invalidates_old_password(self, client, db):
        """비밀번호 변경 후 이전 비밀번호 불가"""
        user = create_active_user(username='passchange', password=TEST_PASSWORD)
        client.force_login(user)

        password_change_url = reverse('accounts:password')
        new_password = 'NewPassword456!'

        # 비밀번호 변경
        change_data = {
            'old_password': TEST_PASSWORD,
            'new_password1': new_password,
            'new_password2': new_password
        }
        response = client.post(password_change_url, data=change_data)
        assert response.status_code in [200, 302]  # 성공

        # 로그아웃
        client.logout()

        # 이전 비밀번호로 로그인 시도 (실패)
        login_url = reverse('accounts:login')
        old_credentials = {
            'username': 'passchange',
            'password': TEST_PASSWORD
        }
        response = client.post(login_url, data=old_credentials)
        assert response.status_code == 200  # 실패, 폼 재표시
        assert '_auth_user_id' not in client.session

        # 새 비밀번호로 로그인 (성공)
        new_credentials = {
            'username': 'passchange',
            'password': new_password
        }
        response = client.post(login_url, data=new_credentials)
        assert response.status_code == 302  # 성공
        assert '_auth_user_id' in client.session
