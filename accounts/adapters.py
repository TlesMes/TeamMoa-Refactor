from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    소셜 로그인 커스텀 어댑터
    - Google OAuth로 회원가입 시 nickname 및 username 자동 생성
    - 동일 이메일 계정 자동 연결
    """

    def populate_user(self, request, sociallogin, data):
        """
        OAuth 프로필 정보로 User 인스턴스 채우기
        username, nickname 자동 생성
        """
        user = super().populate_user(request, sociallogin, data)

        # username 자동 생성 (이메일 기반)
        if not user.username:
            email = data.get('email', '')
            if email:
                user.username = self.generate_unique_username(email)
            else:
                # 이메일이 없으면 Google ID 사용
                uid = sociallogin.account.uid
                user.username = f"user_{uid[:10]}"

        # nickname 자동 생성 (Google 프로필 기반)
        extra_data = sociallogin.account.extra_data

        if not user.nickname:
            # 1순위: Google의 given_name (예: "길동")
            given_name = extra_data.get('given_name', '')
            if given_name:
                user.nickname = given_name[:10]
            # 2순위: Google의 name (예: "홍길동")
            elif extra_data.get('name'):
                user.nickname = extra_data['name'][:10]
            # 3순위: username에서 생성
            else:
                user.nickname = user.username[:10]

        # profile은 빈 값으로 초기화 (나중에 사용자가 직접 입력)
        if not user.profile:
            user.profile = ""

        return user

    def generate_unique_username(self, email):
        """
        이메일에서 고유한 username 생성
        - @ 앞부분 사용
        - 특수문자 제거 (_, -, . 제외)
        - 중복 시 숫자 추가
        """
        # @ 앞부분 추출
        base_username = email.split('@')[0]

        # 특수문자 제거 (ASCIIUsernameValidator 규칙: 영문, 숫자, ., _, - 만 허용)
        base_username = ''.join(c for c in base_username if c.isalnum() or c in '._-')

        # 최소 3자 보장
        if len(base_username) < 3:
            base_username = 'user'

        # 최대 150자 제한
        base_username = base_username[:147]  # _숫자를 위해 여유 공간

        # 고유성 보장 (이미 존재하면 숫자 추가)
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        return username

    def pre_social_login(self, request, sociallogin):
        """
        소셜 로그인 전 처리
        동일한 이메일을 가진 사이트 계정이 있으면 자동 연결

        중요:
        - 로그인 모드: 비로그인 상태에서만 이메일 기반 자동 연결
        - 연결 모드: 현재 로그인한 사용자에게만 연결 (이메일 무관)
        """
        # 이미 연결된 계정이면 스킵
        if sociallogin.is_existing:
            return

        # 이메일 주소 가져오기
        if not sociallogin.email_addresses:
            return

        email = sociallogin.email_addresses[0].email

        # 로그인 상태 확인
        if request.user.is_authenticated:
            # 연결 모드: 현재 로그인한 사용자에게 연결
            # 이메일이 달라도 허용 (사용자가 여러 Google 계정 가질 수 있음)

            # 1. 다른 사람이 이미 연결한 Google 계정(UID)이면 차단
            from allauth.socialaccount.models import SocialAccount
            from allauth.exceptions import ImmediateHttpResponse
            from django.shortcuts import redirect

            existing_social = SocialAccount.objects.filter(
                provider=sociallogin.account.provider,
                uid=sociallogin.account.uid
            ).exclude(user=request.user).first()

            if existing_social:
                request.session['_oauth_connection_blocked'] = True
                request.session.modified = True  # 강제로 session 저장
                messages.error(request, '이미 다른 계정에 연결된 Google 계정입니다.')
                raise ImmediateHttpResponse(redirect('accounts:social_connections'))

            # 2. 해당 Google 이메일을 다른 사용자가 사용 중이면 차단
            existing_email_user = User.objects.filter(email=email).exclude(id=request.user.id).first()

            if existing_email_user:
                request.session['_oauth_connection_blocked'] = True
                request.session.modified = True  # 강제로 session 저장
                messages.error(request, f'이미 다른 계정에서 사용 중인 이메일({email})입니다. 해당 계정으로 로그인 후 연결해주세요.')
                raise ImmediateHttpResponse(redirect('accounts:social_connections'))

            # 안전하면 현재 사용자에게 연결
            sociallogin.connect(request, request.user)
            # EmailAddress 테이블에도 저장 (중복 체크 위함)
            self._ensure_email_address(request, sociallogin)
            return

        # 비로그인 상태: 이메일 기반 자동 연결 (로그인 모드)
        try:
            user = User.objects.get(email=email)

            # 활성화된 계정에만 자동 연결
            if user.is_active:
                # 기존 계정에 소셜 계정 연결 후 로그인
                sociallogin.connect(request, user)
                # EmailAddress 테이블에도 저장 (중복 체크 위함)
                self._ensure_email_address(request, sociallogin)
        except User.DoesNotExist:
            # 신규 회원가입 진행
            pass

    def _ensure_email_address(self, request, sociallogin):  # noqa: ARG002
        """
        EmailAddress 테이블에 소셜 계정 이메일 저장
        회원가입 폼에서 중복 체크 가능하도록 보장
        """
        from allauth.account.models import EmailAddress

        if not sociallogin.email_addresses:
            return

        email = sociallogin.email_addresses[0].email
        user = sociallogin.user

        # 이미 존재하면 스킵
        if EmailAddress.objects.filter(user=user, email=email).exists():
            return

        # EmailAddress 생성
        EmailAddress.objects.create(
            user=user,
            email=email,
            verified=True,  # OAuth 이메일은 검증된 것으로 간주
            primary=True
        )

    def get_connect_redirect_url(self, request, socialaccount):
        """
        소셜 계정 연결 후 리다이렉트 URL
        allauth 기본 페이지 대신 커스텀 페이지로 이동
        """
        from django.urls import reverse
        return reverse('accounts:social_connections')

    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        """
        OAuth 인증 오류 처리
        예: 사용자가 Google 동의 화면에서 취소 버튼 클릭
        """
        print(f"[CustomSocialAccountAdapter] authentication_error: provider={provider.name}, error={error}, exception={exception}")

        # 사용자 취소
        if error == 'cancelled' or (exception and 'cancelled' in str(exception).lower()):
            messages.info(request, "소셜 로그인이 취소되었습니다.")
        # 기타 인증 오류
        else:
            messages.error(request, "소셜 로그인 중 오류가 발생했습니다. 다시 시도해주세요.")

    def add_message(self, request, level, message_template, message_context=None, extra_tags=""):
        """
        소셜 계정 연결 차단 메시지 필터링
        pre_social_login()에서 차단된 경우 성공 메시지 무시
        """
        # 디버깅
        print(f"[CustomSocialAccountAdapter] template={message_template}, level={level}, blocked={request.session.get('_oauth_connection_blocked', False)}")

        # 연결이 차단된 경우 성공 메시지 무시
        if request.session.get('_oauth_connection_blocked') and 'account_connected' in str(message_template):
            print(f"[CustomSocialAccountAdapter] 성공 메시지 차단!")
            request.session.pop('_oauth_connection_blocked', None)  # 플래그 제거
            return

        # 기본 처리 (다른 메시지는 CustomAccountAdapter에서 처리)
        super().add_message(request, level, message_template, message_context, extra_tags)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    일반 계정 관리 커스텀 어댑터
    - allauth 메시지 커스터마이징
    """

    def add_message(self, request, level, message_template, message_context=None, extra_tags=""):
        print(f"[AccountAdapter] template={message_template}, level={level}")

        # 소셜 계정 연결 성공
        if "socialaccount/messages/account_connected_updated.txt" in str(message_template):
            messages.success(request, "소셜 계정이 성공적으로 연결되었습니다.")
            return

        # 소셜 계정 연결 실패 (다른 계정에 이미 연결됨)
        if "socialaccount/messages/account_connected_other.txt" in str(message_template):
            messages.error(request, "이미 다른 계정에 연결된 소셜 계정입니다.")
            return

        # 소셜 계정 연결 해제
        if "socialaccount/messages/account_disconnected.txt" in str(message_template):
            messages.warning(request, "소셜 계정 연결이 해제되었습니다.")
            return

        # 소셜 로그인 (OAuth 자동 회원가입/로그인)
        if "account/messages/logged_in.txt" in str(message_template):
            user = getattr(request, "user", None)
            if user and user.is_authenticated:
                messages.success(request, f"{user.nickname}님, 환영합니다!")
            return

        # 기본 메시지는 그대로 유지
        super().add_message(request, level, message_template, message_context, extra_tags)