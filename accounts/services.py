from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from accounts.forms import SignupForm
from .tokens import account_activation_token


def register_user(form:SignupForm, current_site):
    """
    사용자를 등록하고 활성화 이메일을 발송합니다.
    """
    # 유저 생성 및 필드 설정    
    user = form.save(commit=False)
    user.is_active = False

    # 인증 메일 전송
    message = render_to_string('accounts/user_activate_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)).encode().decode(),
        'token': account_activation_token.make_token(user),
    })
    mail_subject = "[TeamMoa] 회원가입 인증 메일입니다."
    email_message = EmailMessage(mail_subject, message, to=[user.email])
    email_message.send()

    user.save()
    return user
