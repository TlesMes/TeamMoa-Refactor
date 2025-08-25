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
from django.contrib.auth.forms import PasswordChangeForm
from accounts.forms import SignupForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from . import services

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
    -> Form을 사용해 데이터만 받고, sevices 사용
    """
    template_name = 'accounts/signup.html'
    form_class = SignupForm
    success_url = reverse_lazy('accounts:signup_success')
    
    def form_valid(self, form):
        try:
            current_site = get_current_site(self.request)
            services.register_user(
                form,
                current_site=current_site,
            )
            return super().form_valid(form)
        except SMTPRecipientsRefused:
            form.add_error(None, "유효하지 않은 이메일 주소입니다.")
            return self.form_invalid(form)


signup = SignupView.as_view()



class ActivateView(TemplateView):
    def get(self, request, uid64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uid64))
            user = User.objects.get(pk=uid)
            
            if user is not None and account_activation_token.check_token(user, token):
                user.is_active = True
                user.save()
                auth.login(request, user)
                messages.success(request, '계정이 성공적으로 활성화되었습니다!')
                return redirect(MAIN_PAGE)
            else:
                messages.error(request, '잘못된 인증 링크입니다.')
                return redirect(LOGIN_PAGE)
        except (User.DoesNotExist, ValueError, TypeError):
            messages.error(request, '유효하지 않은 인증 정보입니다.')
            return redirect(LOGIN_PAGE)


activate = ActivateView.as_view()


class LoginView(TemplateView):
    template_name = 'accounts/login.html'
    
    def dispatch(self, request, *args, **kwargs):
        # 이미 로그인된 사용자는 메인 페이지로 리다이렉트
        if request.user.is_authenticated:
            return redirect(MAIN_PAGE)
        
        # 캐시 방지 헤더 설정
        response = super().dispatch(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        if not username or not password:
            return self.render_to_response({
                'error': '아이디와 비밀번호를 모두 입력해주세요.'
            })
        
        user = auth.authenticate(request, username=username, password=password)
        
        if user is not None:
            auth.login(request, user)
            request.session.set_expiry(0)
            # 로그인 성공 시 환영 메시지
            messages.success(request, f'{user.nickname}님, 환영합니다!')
            return redirect(MAIN_PAGE)
        else:
            print("로그인 실패")
            return self.render_to_response({
                'error': '아이디 또는 비밀번호가 올바르지 않습니다.',
                'username': username  # 실패 시 username 유지
            })


login = LoginView.as_view()


class LogoutView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse(MAIN_PAGE)
    
    def get(self, request, *args, **kwargs):
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
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_change_form'] = context['form']
        return context
    
    def get(self, request, *args, **kwargs):
        services.store_return_url(request)
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, '회원정보가 성공적으로 수정되었습니다.')
        return_url = services.get_return_url(self.request, MAIN_PAGE)
        return redirect(return_url)


update = UserUpdateView.as_view()


class PasswordChangeView(LoginRequiredMixin, FormView):
    template_name = 'accounts/change_password.html'
    form_class = PasswordChangeForm
    login_url = '/accounts/login/'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['password_change_form'] = context['form']
        return context
    
    def get(self, request, *args, **kwargs):
        services.store_return_url(request)
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.save()
        # 비밀번호 변경 후 재로그인 필요없도록 유지
        auth.update_session_auth_hash(self.request, form.user)
        messages.success(self.request, '비밀번호가 성공적으로 변경되었습니다.')
        return_url = services.get_return_url(self.request, MAIN_PAGE)
        return redirect(return_url)


password = PasswordChangeView.as_view()


class ResendActivationEmailView(TemplateView):
    template_name = 'accounts/resend_activation.html'
    
    def post(self, request, *args, **kwargs):
        email_or_username = request.POST.get('email_or_username', '').strip()
        
        # AJAX 요청인지 확인
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not email_or_username:
            message = '이메일 또는 사용자명을 입력해주세요.'
            return self._handle_response(is_ajax, 'error', message)
        
        try:
            # 이메일 또는 사용자명으로 사용자 찾기
            if '@' in email_or_username:
                user = User.objects.get(email=email_or_username, is_active=False)
            else:
                user = User.objects.get(username=email_or_username, is_active=False)
            
            # 스팸 방지 체크
            if self._is_rate_limited(request, user.id):
                remaining_time = self._get_remaining_time(request, user.id)
                message = f'인증 메일은 5분마다 한 번씩만 전송할 수 있습니다. {remaining_time}분 후에 다시 시도해주세요.'
                return self._handle_response(is_ajax, 'warning', message)
            
            # 메일 재전송
            current_site = get_current_site(request)
            services.send_activation_email(user, current_site)
            
            # 전송 시간 기록
            self._record_send_time(request, user.id)
            
            message = f'{user.email}로 인증 메일을 재전송했습니다.'
            if is_ajax:
                return JsonResponse({'status': 'success', 'message': message})
            messages.success(request, message)
            return render(request, 'accounts/resend_success.html', {'email': user.email})
            
        except User.DoesNotExist:
            message = '해당 정보로 가입된 미인증 계정을 찾을 수 없습니다.'
            return self._handle_response(is_ajax, 'error', message)
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


resend_activation_email = ResendActivationEmailView.as_view()


class TestSignupSuccessView(TemplateView):
    template_name = 'accounts/signup_success.html'
    
    def get(self, request, *args, **kwargs):
        # 테스트용 미인증 사용자가 없으면 생성
        if not User.objects.filter(username='testuser', is_active=False).exists():
            User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123',
                is_active=False  # 미인증 상태
            )
            print("테스트용 사용자 생성: testuser / test@example.com")
        
        return super().get(request, *args, **kwargs)


test_signup_success = TestSignupSuccessView.as_view()


