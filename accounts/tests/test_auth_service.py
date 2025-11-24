"""
Accounts 앱 서비스 레이어 테스트 (18개)

역할: HTTP와 무관한 순수 비즈니스 로직 검증
"""
import pytest
from django.core import mail
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from datetime import timedelta

from accounts.models import User
from accounts.tokens import account_activation_token
from accounts.tests.conftest import create_inactive_user, create_active_user, TEST_PASSWORD, RATE_LIMIT_MINUTES


class TestRegistrationAndEmail:
    """회원가입 및 이메일 테스트 (5개)"""

    def test_register_user_creates_inactive_user(self, auth_service, test_site, db):
        """회원가입 시 비활성 계정 생성"""
        from accounts.forms import SignupForm

        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'nickname': '신규유저',
            'password': TEST_PASSWORD,
            'password2': TEST_PASSWORD
        }
        form = SignupForm(data=form_data)
        assert form.is_valid()

        user = auth_service.register_user(form, test_site)

        assert user.username == 'newuser'
        assert user.is_active is False  # 이메일 인증 전이므로 비활성
        assert User.objects.filter(username='newuser').exists()

    def test_send_activation_email_includes_token(self, auth_service, test_site, db):
        """이메일에 uid/token 포함 확인"""
        user = create_inactive_user(username='emailtest', email='emailtest@example.com')

        mail.outbox = []  # 초기화
        auth_service.send_activation_email(user, test_site)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [user.email]
        assert '인증' in mail.outbox[0].subject or '활성화' in mail.outbox[0].subject
        # 활성화 URL이 이메일 본문에 포함되어 있는지 확인 (/accounts/activate/uid/token 형식)
        assert "/accounts/activate/" in mail.outbox[0].body or "/activate/" in mail.outbox[0].body

    def test_activate_account_with_valid_token(self, auth_service, db):
        """유효한 토큰으로 계정 활성화"""
        user = create_inactive_user(username='activate_test')

        # 토큰 생성
        uid64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        activated_user = auth_service.activate_account(uid64, token)

        assert activated_user.is_active is True
        user.refresh_from_db()
        assert user.is_active is True

    def test_activate_account_with_invalid_token(self, auth_service, db):
        """잘못된 토큰 거부"""
        user = create_inactive_user(username='invalid_token_test')
        uid64 = urlsafe_base64_encode(force_bytes(user.pk))
        invalid_token = 'invalid-token-12345'

        with pytest.raises(ValueError, match='잘못된 인증 링크입니다|유효하지 않은 인증 정보입니다'):
            auth_service.activate_account(uid64, invalid_token)

        user.refresh_from_db()
        assert user.is_active is False  # 여전히 비활성

    def test_activate_account_with_nonexistent_uid(self, auth_service, db):
        """존재하지 않는 UID 거부"""
        fake_uid64 = urlsafe_base64_encode(force_bytes(99999))
        fake_token = 'fake-token'

        with pytest.raises(ValueError, match='유효하지 않은 인증 정보입니다'):
            auth_service.activate_account(fake_uid64, fake_token)


class TestResendActivationAndRateLimiting:
    """인증 재발송 및 Rate Limiting 테스트 (4개)"""

    def test_resend_activation_email_success(self, auth_service, test_site, db, rf):
        """재발송 성공"""
        user = create_inactive_user(username='resend_test', email='resend@example.com')

        # RequestFactory로 가짜 request 생성
        request = rf.post('/fake-url/')
        request.session = {}

        mail.outbox = []
        result_user = auth_service.resend_activation_email(request, user.email, test_site)

        assert result_user == user
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [user.email]

    def test_resend_activation_blocks_within_5_minutes(self, auth_service, test_site, db, rf):
        """5분 이내 중복 요청 차단 (Rate limiting)"""
        user = create_inactive_user(username='ratelimit_test', email='ratelimit@example.com')

        request = rf.post('/fake-url/')
        request.session = {}

        # 첫 요청
        auth_service.resend_activation_email(request, user.email, test_site)

        # 5분 이내 재요청 (차단)
        with pytest.raises(ValueError, match='5분마다 한 번씩만'):
            auth_service.resend_activation_email(request, user.email, test_site)

    def test_resend_activation_allowed_after_5_minutes(self, auth_service, test_site, db, rf):
        """5분 경과 후 재발송 허용"""
        user = create_inactive_user(username='timepass_test', email='timepass@example.com')

        request = rf.post('/fake-url/')
        request.session = {}

        # 첫 요청
        mail.outbox = []
        auth_service.resend_activation_email(request, user.email, test_site)
        assert len(mail.outbox) == 1

        # 5분 경과 시뮬레이션 (세션 시간 조작)
        request.session[f'activation_email_sent_{user.id}'] = (
            timezone.now() - timedelta(minutes=RATE_LIMIT_MINUTES + 1)
        ).isoformat()

        # 재요청 성공
        auth_service.resend_activation_email(request, user.email, test_site)
        assert len(mail.outbox) == 2  # 이메일 2개 발송됨

    def test_resend_activation_rejects_active_user(self, auth_service, test_site, db, rf):
        """활성 계정 거부"""
        user = create_active_user(username='active_resend', email='active@example.com')

        request = rf.post('/fake-url/')
        request.session = {}

        with pytest.raises(ValueError, match='미인증 계정을 찾을 수 없습니다'):
            auth_service.resend_activation_email(request, user.email, test_site)


class TestAuthenticationAndLogin:
    """로그인 및 인증 테스트 (3개)"""

    def test_authenticate_user_with_valid_credentials(self, auth_service, db):
        """로그인 성공"""
        user = create_active_user(username='logintest', password=TEST_PASSWORD)

        authenticated_user = auth_service.authenticate_user('logintest', TEST_PASSWORD)

        assert authenticated_user is not None
        assert authenticated_user.username == 'logintest'

    def test_authenticate_user_with_wrong_password(self, auth_service, db):
        """잘못된 비밀번호"""
        user = create_active_user(username='wrongpass', password=TEST_PASSWORD)

        with pytest.raises(ValueError, match='아이디 또는 비밀번호가 올바르지 않습니다'):
            auth_service.authenticate_user('wrongpass', 'WrongPassword123!')

    def test_authenticate_user_rejects_inactive_account(self, auth_service, db):
        """비활성 계정 거부"""
        user = create_inactive_user(username='inactive_login', password=TEST_PASSWORD)

        with pytest.raises(ValueError, match='아이디 또는 비밀번호가 올바르지 않습니다'):
            auth_service.authenticate_user('inactive_login', TEST_PASSWORD)


class TestSessionManagement:
    """세션 관리 테스트 (2개)"""

    def test_store_return_url_from_referer(self, auth_service, rf):
        """이전 URL 세션 저장"""
        request = rf.get('/login/', HTTP_REFERER='http://testserver/teams/')
        request.session = {}

        auth_service.store_return_url(request)

        assert 'return_url' in request.session
        assert '/teams/' in request.session['return_url']

    def test_store_return_url_rejects_external_domain(self, auth_service, rf):
        """외부 도메인 거부 (보안)"""
        request = rf.get('/login/', HTTP_REFERER='http://evil.com/phishing')
        request.session = {}

        auth_service.store_return_url(request)

        # 외부 도메인은 저장되지 않음
        assert 'return_url' not in request.session


class TestUserDeactivation:
    """회원 탈퇴 테스트 (4개)"""

    def test_deactivate_user_anonymizes_personal_info(self, auth_service, db):
        """탈퇴 시 개인정보 익명화"""
        user = create_active_user(username='deactivate_test', email='deactivate@example.com', password=TEST_PASSWORD)
        user_id = user.id

        deactivated_user = auth_service.deactivate_user(user, TEST_PASSWORD)

        # 계정 비활성화
        assert deactivated_user.is_active is False

        # 개인정보 익명화 검증
        assert deactivated_user.username == f"deleted_user_{user_id}"
        assert deactivated_user.email == f"deleted_{user_id}@deleted.local"
        assert deactivated_user.nickname == "탈퇴한 사용자"
        assert deactivated_user.profile == ""
        assert not deactivated_user.has_usable_password()

    def test_deactivate_user_with_wrong_password(self, auth_service, db):
        """잘못된 비밀번호로 탈퇴 실패"""
        user = create_active_user(username='wrong_password_test', password=TEST_PASSWORD)

        with pytest.raises(ValueError, match='비밀번호가 올바르지 않습니다'):
            auth_service.deactivate_user(user, 'WrongPassword123!')

        user.refresh_from_db()
        assert user.is_active is True

    def test_deactivate_social_user_without_password(self, auth_service, db):
        """소셜 로그인 사용자는 비밀번호 없이 탈퇴 가능"""
        user = create_active_user(username='social_user', email='social@example.com')
        user.set_unusable_password()  # 소셜 로그인 사용자
        user.save()

        deactivated_user = auth_service.deactivate_user(user, None)

        assert deactivated_user.is_active is False

    def test_deactivate_user_removes_all_team_memberships(self, auth_service, db):
        """탈퇴 시 모든 팀 멤버십 제거"""
        from teams.models import Team, TeamUser

        user = create_active_user(username='multi_team_user', email='multi@example.com', password=TEST_PASSWORD)

        # 3개 팀에 멤버로 가입
        for i in range(3):
            host = create_active_user(username=f'host_{i}', email=f'host{i}@example.com')
            team = Team.objects.create(
                title=f'Team {i}',
                host=host,
                maxuser=10,
                currentuser=2,
                invitecode=f'code{i}',
                teampasswd='password',
                introduction='Test'
            )
            TeamUser.objects.create(team=team, user=host)
            TeamUser.objects.create(team=team, user=user)

        # 탈퇴 전 멤버십 확인
        assert TeamUser.objects.filter(user=user).count() == 3

        # 탈퇴
        auth_service.deactivate_user(user, TEST_PASSWORD)

        # 모든 멤버십이 제거되었는지 확인
        assert TeamUser.objects.filter(user=user).count() == 0
