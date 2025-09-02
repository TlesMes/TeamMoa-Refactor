from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.contrib import auth
from django.utils import timezone
from datetime import timedelta
from smtplib import SMTPRecipientsRefused
from .tokens import account_activation_token
from .models import User
from django.db import transaction


class AuthService:
    """인증 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    @transaction.atomic
    def register_user(self, form, current_site):
        """
        사용자를 등록하고 활성화 이메일을 발송합니다.
        이메일 발송 실패 시 사용자 생성도 취소됩니다.
        """
        # pk는 commit되어야 db에 저장되고 부여받는 값
        # 따라서 email로 pk를 전송하려면, db에 user가 저장되어야 한다.
        # 그러나 email이 유효하지 않아, 전송이 실패하면 db에 저장된 user는 더미가 되어버린다.
        # 따라서 transcation.atomic을 통해 원자성을 확보
        with transaction.atomic():
            # 1. 유저를 db에 임시 저장, pk부여
            user = form.save()

            # 2. 이메일을 전송
            self.send_activation_email(user, current_site)

        # 3. with 블록이 예외 없이 성공적으로 끝나면, DB에 저장된 user가 최종 확정(commit)
        return user

    def send_activation_email(self, user, current_site):
        """인증 메일 전송 (재사용 가능한 함수)"""
        message = render_to_string('accounts/user_activate_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        mail_subject = "[TeamMoa] 회원가입 인증 메일입니다."
        email_message = EmailMessage(mail_subject, message, to=[user.email])
        email_message.send()

    def store_return_url(self, request):
        """
        GET 요청시 이전 페이지를 세션에 안전하게 저장합니다.
        같은 도메인인지 검증하여 Open Redirect 취약점을 방지합니다.
        """
        referer = request.META.get('HTTP_REFERER')
        if referer:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            # 같은 도메인인지 검증 (도메인이 없거나 현재 호스트와 같은 경우만)
            if not parsed.netloc or parsed.netloc == request.get_host():
                request.session['return_url'] = referer

    def get_return_url(self, request, default_url='teams:main_page'):
        """
        세션에서 안전한 이전 페이지 URL을 가져오고 세션에서 제거합니다.
        저장된 URL이 없으면 기본 URL을 반환합니다.
        """
        return request.session.pop('return_url', default_url)

    def login_user(self, request, username, password):
        """
        사용자 로그인을 처리합니다.
        성공시 로그인된 사용자를, 실패시 None을 반환합니다.
        """
        if not username or not password:
            raise ValueError('아이디와 비밀번호를 모두 입력해주세요.')
        
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            request.session.set_expiry(0)  # 브라우저 종료시 세션 만료
            return user
        else:
            raise ValueError('아이디 또는 비밀번호가 올바르지 않습니다.')

    def activate_account(self, uid64, token):
        """
        계정 활성화를 처리합니다.
        성공시 활성화된 사용자를, 실패시 예외를 발생시킵니다.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uid64))
            user = User.objects.get(pk=uid)
            
            if user is not None and account_activation_token.check_token(user, token):
                user.is_active = True
                user.save()
                return user
            else:
                raise ValueError('잘못된 인증 링크입니다.')
        except (User.DoesNotExist, ValueError, TypeError):
            raise ValueError('유효하지 않은 인증 정보입니다.')

    def logout_user(self, request):
        """사용자 로그아웃을 처리합니다."""
        if request.user.is_authenticated:
            auth.logout(request)

    def resend_activation_email(self, request, email_or_username, current_site):
        """
        인증 메일을 재전송합니다.
        스팸 방지를 위한 제한 시간을 확인합니다.
        """
        if not email_or_username:
            raise ValueError('이메일 또는 사용자명을 입력해주세요.')
        
        # 이메일 또는 사용자명으로 사용자 찾기
        try:
            if '@' in email_or_username:
                user = User.objects.get(email=email_or_username, is_active=False)
            else:
                user = User.objects.get(username=email_or_username, is_active=False)
        except User.DoesNotExist:
            raise ValueError('해당 정보로 가입된 미인증 계정을 찾을 수 없습니다.')
        
        # 스팸 방지 체크
        if self._is_rate_limited(request, user.id):
            remaining_time = self._get_remaining_time(request, user.id)
            raise ValueError(f'인증 메일은 5분마다 한 번씩만 전송할 수 있습니다. {remaining_time}분 후에 다시 시도해주세요.')
        
        # 메일 재전송
        self.send_activation_email(user, current_site)
        
        # 전송 시간 기록
        self._record_send_time(request, user.id)
        
        return user

    def create_test_user(self):
        """테스트용 미인증 사용자를 생성합니다."""
        if not User.objects.filter(username='testuser', is_active=False).exists():
            user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123',
                is_active=False  # 미인증 상태
            )
            return user
        return None

    def _is_rate_limited(self, request, user_id):
        """스팸 방지 체크"""
        last_sent_key = f'activation_email_sent_{user_id}'
        last_sent = request.session.get(last_sent_key)
        
        if not last_sent:
            return False
        
        last_sent_time = timezone.datetime.fromisoformat(last_sent)
        return timezone.now() - last_sent_time < timedelta(minutes=5)
    
    def _get_remaining_time(self, request, user_id):
        """남은 대기 시간 계산"""
        last_sent_key = f'activation_email_sent_{user_id}'
        last_sent = request.session.get(last_sent_key)
        last_sent_time = timezone.datetime.fromisoformat(last_sent)
        return 5 - (timezone.now() - last_sent_time).seconds // 60
    
    def _record_send_time(self, request, user_id):
        """전송 시간 기록"""
        last_sent_key = f'activation_email_sent_{user_id}'
        request.session[last_sent_key] = timezone.now().isoformat()


