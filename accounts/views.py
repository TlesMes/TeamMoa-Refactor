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
# Create your views here.
from . import services


def signup(request):
    if request.method == "POST":
        try:
            password = request.POST["password1"]
            password2 = request.POST["password2"]
            username = request.POST["username"]
            nickname = request.POST["nickname"]
            profile = request.POST["profile"]

            if not all([password, password2, username, nickname, profile]):
                raise ValueError("빈 칸이 존재합니다.")

            if password != password2:
                # Django Form을 사용하면 이 로직을 form.is_valid()에서 처리할 수 있습니다.
                return HttpResponse(
                    '<script>alert("비밀번호가 일치하지 않습니다.")</script><script>location.href="./"</script>'
                )

            current_site = get_current_site(request)
            services.register_user(
                username=username,
                password=password,
                nickname=nickname,
                profile=profile,
                current_site=current_site,
            )

            return HttpResponse(
                '<div style="font-size: 40px; width: 100%; height:100%; display:flex; text-align:center; '
                'justify-content: center; align-items: center;">'
                "입력하신 이메일<span>로 인증 링크가 전송되었습니다.</span>"
                "</div>"
            )
        except ValueError as e:
            return HttpResponse(
                f'<script>alert("{e}")</script><script>location.href="./"</script>'
            )
        except IntegrityError as e:
            return HttpResponse(
                f'<script>alert("{e}")</script><script>location.href="./"</script>'
            )
        except SMTPRecipientsRefused:
            return HttpResponse(
                '<script>alert("이메일 전송 실패")</script><script>location.href="./"</script>'
            )

    return render(request, "accounts/signup.html")



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
    if request.COOKIES.get('username') is not None:
        username = request.COOKIES.get('username')
        password = request.COOKIES.get('password')
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("teams:team_list")
        else:
            return render(request, "accounts/login.html")
    elif request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        # 해당 user가 있으면 username, 없으면 None
        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            auth.login(request, user)
            if request.POST.get("keep_login") == "TRUE":
                response = render(request, 'accounts/home.html')
                response.set_cookie('username',username)
                response.set_cookie('password',password)
                return response
            return HttpResponseRedirect('/teams/team_list')
        else:
            return HttpResponse('<script>alert("계정이 존재하지 않습니다.")</script>''<script>location.href="./"</script>')
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


