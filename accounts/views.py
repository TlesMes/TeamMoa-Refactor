from django.shortcuts import redirect, render
from django.contrib import auth
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
# Create your views here.
from . import services

TEAM_LIST_URL_NAME = 'teams:main_page'
LOGIN_URL_NAME = 'accounts:login'
HOME_URL_NAME = 'accounts:home'

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                current_site = get_current_site(request)
                services.register_user(
                    form,
                    current_site=current_site,
                )
                return render(request, 'accounts/signup_success.html')

            except (SMTPRecipientsRefused) as e:
                error_message = "유효하지 않은 이메일 주소입니다."
                form.add_error(None, error_message)
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})



def activate(request, uid64, token):
    uid = force_str(urlsafe_base64_decode(uid64))
    user = User.objects.get(pk=uid)

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        auth.login(request, user)
        return redirect(TEAM_LIST_URL_NAME)
    else:
        return HttpResponse('비정상적인 접근입니다.')


def login(request):
    # 이미 로그인 된 사용자가 로그인 페이지에 접근 시 패스
    if request.user.is_authenticated:
        return redirect(TEAM_LIST_URL_NAME)
    
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        # 해당 user가 있으면 username, 없으면 None
        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            auth.login(request, user)
            request.session.set_expiry(0)
            return redirect(TEAM_LIST_URL_NAME)
        else:
            return render(request, 'accounts/login.html', {'error': '아이디 또는 비밀번호가 올바르지 않습니다.'})
    else:
        return render(request, 'accounts/login.html')


def logout(request):
    auth.logout(request)
    return redirect(HOME_URL_NAME) #로그아웃 후 이동할 페이지, 메인나오면 바꿔줄것


def home(request):
    if request.user.is_authenticated:
        return redirect(TEAM_LIST_URL_NAME)
    return redirect(LOGIN_URL_NAME)


#유저 정보 변경
@login_required
def update(request):
    if request.method == 'GET':
        services.store_return_url(request)
        user_change_form = CustomUserChangeForm(instance=request.user)
    
    elif request.method == 'POST':
        user_change_form = CustomUserChangeForm(request.POST, instance=request.user)
        if user_change_form.is_valid():
            user_change_form.save()
            return_url = services.get_return_url(request, TEAM_LIST_URL_NAME)
            return redirect(return_url)
    
    return render(request, 'accounts/update.html', {'user_change_form': user_change_form})


#패스워드 변경
@login_required
def password(request):
    if request.method == 'GET':
        services.store_return_url(request)
        password_change_form = PasswordChangeForm(request.user)
    
    elif request.method == 'POST':
        password_change_form = PasswordChangeForm(request.user, request.POST)
        if password_change_form.is_valid():
            password_change_form.save()
            return_url = services.get_return_url(request, TEAM_LIST_URL_NAME)
            return redirect(return_url)
    
    return render(request, 'accounts/change_password.html', {'password_change_form': password_change_form})


def resend_activation_email(request):
    """인증 메일 재전송 기능"""
    if request.method == 'POST':
        email_or_username = request.POST.get('email_or_username', '').strip()
        
        # AJAX 요청인지 확인
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not email_or_username:
            message = '이메일 또는 사용자명을 입력해주세요.'
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': message})
            messages.error(request, message)
            return render(request, 'accounts/resend_activation.html')
        
        try:
            # 이메일 또는 사용자명으로 사용자 찾기
            if '@' in email_or_username:
                user = User.objects.get(email=email_or_username, is_active=False)
            else:
                user = User.objects.get(username=email_or_username, is_active=False)
            
            # 마지막 전송 시간 체크 (스팸 방지 - 5분 제한)
            last_sent_key = f'activation_email_sent_{user.id}'
            last_sent = request.session.get(last_sent_key)
            
            if last_sent:
                last_sent_time = timezone.datetime.fromisoformat(last_sent)
                if timezone.now() - last_sent_time < timedelta(minutes=5):
                    remaining_time = 5 - (timezone.now() - last_sent_time).seconds // 60
                    message = f'인증 메일은 5분마다 한 번씩만 전송할 수 있습니다. {remaining_time}분 후에 다시 시도해주세요.'
                    if is_ajax:
                        return JsonResponse({'status': 'warning', 'message': message})
                    messages.warning(request, message)
                    return render(request, 'accounts/resend_activation.html')
            
            # 메일 재전송
            current_site = get_current_site(request)
            services.send_activation_email(user, current_site)
            
            # 전송 시간 기록
            request.session[last_sent_key] = timezone.now().isoformat()
            
            message = f'{user.email}로 인증 메일을 재전송했습니다.'
            if is_ajax:
                return JsonResponse({'status': 'success', 'message': message})
            messages.success(request, message)
            return render(request, 'accounts/resend_success.html', {'email': user.email})
            
        except User.DoesNotExist:
            message = '해당 정보로 가입된 미인증 계정을 찾을 수 없습니다.'
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': message})
            messages.error(request, message)
        except SMTPRecipientsRefused:
            message = '유효하지 않은 이메일 주소입니다.'
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': message})
            messages.error(request, message)
        except Exception as e:
            message = '메일 전송 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': message})
            messages.error(request, message)
    
    return render(request, 'accounts/resend_activation.html')


def test_signup_success(request):
    """테스트용 회원가입 성공 페이지"""
    # 테스트용 미인증 사용자가 없으면 생성
    if not User.objects.filter(username='testuser', is_active=False).exists():
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=False  # 미인증 상태
        )
        print("테스트용 사용자 생성: testuser / test@example.com")
    
    return render(request, 'accounts/signup_success.html')


