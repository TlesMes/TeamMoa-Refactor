from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth
from .models import User
# from rest_framework.views import APIView, Response, status
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from .tokens import account_activation_token
from django.utils.encoding import force_bytes, force_str
from django.http import HttpResponseRedirect,HttpResponse
from django.db import IntegrityError
from smtplib import SMTPRecipientsRefused
import re # 정규 표현식 모듈
from .forms import CustomUserChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from accounts.forms import SignupForm
# Create your views here.
from . import services


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                email = form.cleaned_data['email']
                nickname = form.cleaned_data['nickname']
                profile = form.cleaned_data['profile']
                

                current_site = get_current_site(request)
                services.register_user(
                    username=username,
                    password=password,
                    email=email,
                    nickname=nickname,
                    profile=profile,
                    current_site=current_site,
                )

                return render(request, 'accounts/signup_success.html')

            except (IntegrityError, SMTPRecipientsRefused) as e:
                error_message = "알 수 없는 오류가 발생했습니다."
                if isinstance(e, IntegrityError):
                    error_message = "이미 존재하는 계정입니다."
                elif isinstance(e, SMTPRecipientsRefused):
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
        return HttpResponseRedirect('/teams/team_list') #인증 후 연결될 페이지
    else:
        return HttpResponse('비정상적인 접근입니다.')


def login(request):
    # 이미 로그인 된 사용자가 로그인 페이지에 접근 시 패스
    if request.user.is_authenticated:
        return redirect('teams:team_list')
    
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        # 해당 user가 있으면 username, 없으면 None
        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            auth.login(request, user)
            request.session.set_expiry(0)
            return redirect('teams:team_list')
        else:
            return render(request, 'accounts/login.html', {'error': '아이디 또는 비밀번호가 올바르지 않습니다.'})
    else:
        return render(request, 'accounts/login.html')


def logout(request):
    response = render(request, 'accounts/home.html')
    response.delete_cookie('username')
    response.delete_cookie('password')
    auth.logout(request)
    return HttpResponseRedirect('/accounts/home') #로그아웃 후 이동할 페이지, 메인나오면 바꿔줄것

def home(request):
    if request.user.is_authenticated:
        print("2")
        return redirect("teams:team_list")
    print("1")
    return redirect("accounts:login")


#유저 정보 변경
@login_required
def update(request):
    if request.method == 'POST': #post방식이면 전달받은 내용 변경함
        user_change_form = CustomUserChangeForm(request.POST, instance=request.user)
        if user_change_form.is_valid():
            user_change_form.save()
            return HttpResponseRedirect('/teams/team_list')
    
    else: #post방식이 아니면 폼을 전달해서 변경사항을 받음
        user_change_form = CustomUserChangeForm(instance = request.user) 
    return render(request, 'accounts/update.html', {'user_change_form':user_change_form})


#패스워드 변경
@login_required
def password(request):
    if request.method == 'POST':
        password_change_form = PasswordChangeForm(request.user, request.POST)
    
        if password_change_form.is_valid():
            password_change_form.save()
            return HttpResponseRedirect('/teams/team_list')

    else:
        password_change_form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html',{'password_change_form':password_change_form})


