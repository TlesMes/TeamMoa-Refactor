from django.shortcuts import redirect, render
from django.contrib import auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, TemplateView, RedirectView
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
            self.auth_service.register_user(form, current_site)
            return super().form_valid(form)
        except SMTPRecipientsRefused:
            form.add_error(None, "유효하지 않은 이메일 주소입니다.")
            return self.form_invalid(form)


signup = SignupView.as_view()



class ActivateView(TemplateView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthService()
    
    def get(self, request, uid64, token, *args, **kwargs):
        try:
            user = self.auth_service.activate_account(uid64, token)
            auth.login(request, user)
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
            auth.login(request, user)
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
    template_name = 'accounts/resend_activation.html'
    
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
            messages.success(request, message)
            return render(request, 'accounts/resend_success.html', {'email': user.email})
            
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
        
        if status == 'error':
            messages.error(self.request, message)
        elif status == 'warning':
            messages.warning(self.request, message)
        
        return self.render_to_response({})


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


