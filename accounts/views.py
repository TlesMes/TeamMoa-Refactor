from django.shortcuts import redirect
from django.contrib import auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, TemplateView, RedirectView, View
from django.urls import reverse_lazy, reverse
from .models import User
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode
from .tokens import account_activation_token
from django.utils.encoding import force_str
from django.http import HttpResponse
from smtplib import SMTPRecipientsRefused
from .forms import CustomUserChangeForm
from django.contrib.auth.decorators import login_required
from accounts.forms import SignupForm, CustomPasswordChangeForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from . import services
from .services import AuthService

# URL 패턴 상수
MAIN_PAGE = 'teams:main_page'
LOGIN_PAGE = 'accounts:login'
HOME_PAGE = 'accounts:home'


class SignupSuccessView(TemplateView):
    template_name = 'accounts/signup_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 세션에서 성공 메시지 가져오기
        signup_email = self.request.session.pop('signup_email', None)
        email_sent = self.request.session.pop('email_sent', False)

        if signup_email and email_sent:
            context['signup_email'] = signup_email
            context['show_success_message'] = True

        # 세션에서 에러 메시지 가져오기
        resend_error = self.request.session.pop('resend_error', None)
        resend_error_level = self.request.session.pop('resend_error_level', None)

        if resend_error:
            context['resend_error'] = resend_error
            context['resend_error_level'] = resend_error_level

        return context


signup_success = SignupSuccessView.as_view()

class SignupView(FormView):
    """
    회원가입 뷰
    - 유저객체를 생성하지만, FormView
    -> 단순 객체 생성 이상의 로직(인증 토큰, 이메일 전송)을 포함
    -> Form을 사용해 데이터만 받고, AuthService 사용
    """
    template_name = 'accounts/signup.html'
    form_class = SignupForm
    success_url = reverse_lazy('accounts:signup_success')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthService()
    
    def form_valid(self, form):
        try:
            current_site = get_current_site(self.request)
            user = self.auth_service.register_user(form, current_site)
            # 세션에 이메일 정보 저장 (signup_success 페이지에서 표시용)
            self.request.session['signup_email'] = user.email
            self.request.session['email_sent'] = True
            return redirect('accounts:signup_success')
        except SMTPRecipientsRefused:
            form.add_error(None, "유효하지 않은 이메일 주소입니다.")
            return self.form_invalid(form)
        except Exception:
            form.add_error(None, "회원가입 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
            return self.form_invalid(form)


signup = SignupView.as_view()



class ActivateView(TemplateView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthService()
    
    def get(self, request, uid64, token, *args, **kwargs):
        try:
            user = self.auth_service.activate_account(uid64, token)
            # 백엔드 명시 (ModelBackend 사용)
            auth.login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, '계정이 성공적으로 활성화되었습니다!')
            return redirect(MAIN_PAGE)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect(LOGIN_PAGE)


activate = ActivateView.as_view()


class LoginView(TemplateView):
    template_name = 'accounts/login.html'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthService()
    
    def dispatch(self, request, *args, **kwargs):
        # 이미 로그인된 사용자는 메인 페이지로 리다이렉트
        if request.user.is_authenticated:
            return redirect(MAIN_PAGE)
        
        # 캐시 방지 헤더 설정
        # 로그인 상태로 뒤로가기 등 로그인 시도를 다시 할 수 없도록
        response = super().dispatch(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        try:
            user = self.auth_service.authenticate_user(username, password)
            # HTTP 처리는 뷰에서 담당
            # authenticate()가 설정한 backend 속성 사용
            auth.login(request, user, backend=user.backend)
            request.session.set_expiry(0)  # 브라우저 종료시 세션 만료
            messages.success(request, f'{user.nickname}님, 환영합니다!')
            return redirect(MAIN_PAGE)
        except ValueError as e:
            return self.render_to_response({
                'error': str(e),
                'username': username  # 실패 시 username 유지
            })


login = LoginView.as_view()


class LogoutView(RedirectView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthService()
    
    def get_redirect_url(self, *args, **kwargs):
        return reverse(MAIN_PAGE)
    
    def get(self, request, *args, **kwargs):
        # HTTP 세션 처리는 뷰에서 직접
        if request.user.is_authenticated:
            auth.logout(request)
        return super().get(request, *args, **kwargs)


logout = LogoutView.as_view()


class HomeView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse(MAIN_PAGE)
        return reverse(LOGIN_PAGE)


home = HomeView.as_view()


class UserUpdateView(LoginRequiredMixin, FormView):
    template_name = 'accounts/update.html'
    form_class = CustomUserChangeForm
    login_url = '/accounts/login/'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthService()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_change_form'] = context['form']
        return context
    
    def get(self, request, *args, **kwargs):
        self.auth_service.store_return_url(request)
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, '회원정보가 성공적으로 수정되었습니다.')
        return_url = self.auth_service.get_return_url(self.request, MAIN_PAGE)
        return redirect(return_url)


update = UserUpdateView.as_view()


class PasswordChangeView(LoginRequiredMixin, FormView):
    template_name = 'accounts/change_password.html'
    form_class = CustomPasswordChangeForm
    login_url = '/accounts/login/'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthService()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['password_change_form'] = context['form']
        return context
    
    def get(self, request, *args, **kwargs):
        self.auth_service.store_return_url(request)
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.save()
        # 비밀번호 변경 후 재로그인 필요없도록 유지
        auth.update_session_auth_hash(self.request, form.user)
        messages.success(self.request, '비밀번호가 성공적으로 변경되었습니다.')
        return_url = self.auth_service.get_return_url(self.request, MAIN_PAGE)
        return redirect(return_url)


password = PasswordChangeView.as_view()


class ResendActivationEmailView(TemplateView):
    """
    인증 메일 재전송 뷰
    - AJAX 요청: JSON 응답 반환
    - 일반 요청: 메시지와 함께 signup_success로 리다이렉트
    """
    template_name = 'accounts/signup_success.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthService()

    def post(self, request, *args, **kwargs):
        email_or_username = request.POST.get('email_or_username', '').strip()

        # AJAX 요청인지 확인
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            current_site = get_current_site(request)
            user = self.auth_service.resend_activation_email(request, email_or_username, current_site)

            message = f'{user.email}로 인증 메일을 재전송했습니다.'
            if is_ajax:
                return JsonResponse({'status': 'success', 'message': message})

            # 일반 요청: 세션에 저장 후 리다이렉트
            request.session['signup_email'] = user.email
            request.session['email_sent'] = True
            return redirect('accounts:signup_success')

        except ValueError as e:
            return self._handle_response(is_ajax, 'warning', str(e))
        except SMTPRecipientsRefused:
            message = '유효하지 않은 이메일 주소입니다.'
            return self._handle_response(is_ajax, 'error', message)
        except Exception:
            message = '메일 전송 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
            return self._handle_response(is_ajax, 'error', message)

    def _handle_response(self, is_ajax, status, message):
        """응답 처리 헬퍼 메서드"""
        if is_ajax:
            return JsonResponse({'status': status, 'message': message})

        # 일반 요청은 세션에 에러 정보 저장 후 리다이렉트
        self.request.session['resend_error'] = message
        self.request.session['resend_error_level'] = status
        return redirect('accounts:signup_success')


resend_activation_email = ResendActivationEmailView.as_view()


class TestSignupSuccessView(TemplateView):
    template_name = 'accounts/signup_success.html'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthService()
    
    def get(self, request, *args, **kwargs):
        # 테스트용 미인증 사용자가 없으면 생성
        user = self.auth_service.create_test_user()

        return super().get(request, *args, **kwargs)


test_signup_success = TestSignupSuccessView.as_view()


class SocialConnectionsView(LoginRequiredMixin, TemplateView):
    """소셜 계정 연결 관리 페이지"""
    template_name = 'accounts/social_connections.html'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 연결된 소셜 계정 가져오기
        from allauth.socialaccount.models import SocialAccount
        social_accounts = SocialAccount.objects.filter(user=self.request.user)
        context['social_accounts'] = social_accounts

        # 이미 연결된 프로바이더 목록
        connected_providers = [account.provider for account in social_accounts]
        context['has_google'] = 'google' in connected_providers
        context['has_github'] = 'github' in connected_providers

        return context

    def post(self, request, *args, **kwargs):
        """소셜 계정 연결 해제 처리"""
        from allauth.socialaccount.models import SocialAccount

        account_id = request.POST.get('account')

        if not account_id:
            messages.error(request, '잘못된 요청입니다.')
            return redirect('accounts:social_connections')

        try:
            social_account = SocialAccount.objects.get(id=account_id, user=request.user)

            # 최소 1개 로그인 방법 유지 검증
            can_disconnect, error_message = self._can_disconnect_account(request.user, social_account)

            if not can_disconnect:
                messages.warning(request, error_message)
                return redirect('accounts:social_connections')

            # 연결 해제
            provider_names = {'google': 'Google', 'github': 'GitHub'}
            provider_name = provider_names.get(social_account.provider, social_account.provider.title())

            # EmailAddress 테이블에서도 해당 이메일 삭제 (소셜 계정 이메일만)
            from allauth.account.models import EmailAddress
            social_email = social_account.extra_data.get('email')
            if social_email:
                EmailAddress.objects.filter(user=request.user, email=social_email).delete()

            social_account.delete()
            messages.success(request, f'{provider_name} 계정 연결이 해제되었습니다.')

        except SocialAccount.DoesNotExist:
            messages.error(request, '존재하지 않는 소셜 계정입니다.')

        return redirect('accounts:social_connections')

    def _can_disconnect_account(self, user, social_account):
        """
        소셜 계정 연결 해제 가능 여부 검증
        최소 1개의 로그인 방법(비밀번호 또는 소셜 계정) 유지 필요
        """
        from allauth.socialaccount.models import SocialAccount

        # 연결된 소셜 계정 수
        social_count = SocialAccount.objects.filter(user=user).count()

        # 사용 가능한 비밀번호 있는지 확인
        has_password = user.has_usable_password()

        # 마지막 소셜 계정이고 비밀번호도 없으면 연결 해제 불가
        if social_count == 1 and not has_password:
            return False, "최소 1개의 로그인 방법이 필요합니다. 비밀번호를 설정하거나 다른 소셜 계정을 연결한 후 해제할 수 있습니다."

        return True, None


social_connections = SocialConnectionsView.as_view()


class DeactivateConfirmView(LoginRequiredMixin, TemplateView):
    """회원 탈퇴 확인 페이지"""
    template_name = 'accounts/deactivate_confirm.html'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 소유한 팀 개수 조회
        from teams.models import Team
        owned_teams_count = Team.objects.filter(host=self.request.user).count()
        context['owned_teams_count'] = owned_teams_count
        return context


deactivate_confirm = DeactivateConfirmView.as_view()


class DeactivateUserView(LoginRequiredMixin, View):
    """회원 탈퇴 처리"""
    login_url = '/accounts/login/'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthService()

    def post(self, request, *args, **kwargs):
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')

        # 확인 체크박스 검증
        if not confirm:
            messages.error(request, '탈퇴 동의에 체크해주세요.')
            return redirect('accounts:deactivate_confirm')

        try:
            # 회원 탈퇴 처리
            self.auth_service.deactivate_user(request.user, password)

            # 로그아웃
            auth.logout(request)

            # 성공 메시지
            messages.success(request, '회원 탈퇴가 완료되었습니다. 그동안 이용해주셔서 감사합니다.')
            return redirect('accounts:login')

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('accounts:deactivate_confirm')
        except Exception as e:
            messages.error(request, '탈퇴 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.')
            return redirect('accounts:deactivate_confirm')


deactivate_user = DeactivateUserView.as_view()


