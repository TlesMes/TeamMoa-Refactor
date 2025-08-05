from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from django.db import IntegrityError
import re

from .models import User
from .tokens import account_activation_token


def register_user(username, password, nickname, profile, current_site):
    """
    사용자를 등록하고 활성화 이메일을 발송합니다.
    """
    # 이메일 형식 검사
    REGEX_EMAIL = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.fullmatch(REGEX_EMAIL, username):
        raise ValueError("이메일 형식이 맞지 않습니다.")

    try:
        # 유저 생성 및 필드 설정
        user = User.objects.create_user(username=username, password=password)
        user.is_active = False
        user.nickname = nickname
        user.profile = profile
        user.save()
    except IntegrityError:
        raise IntegrityError("존재하는 계정입니다.")

    # 인증 메일 전송
    message = render_to_string('accounts/user_activate_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)).encode().decode(),
        'token': account_activation_token.make_token(user),
    })
    mail_subject = "[TeamMoa] 회원가입 인증 메일입니다."
    email = EmailMessage(mail_subject, message, to=[username])
    email.send()

    return user
