from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from .tokens import account_activation_token
from django.db import transaction

def register_user(form, current_site):
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
        message = render_to_string('accounts/user_activate_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode('utf-8'),
            'token': account_activation_token.make_token(user),
        })
        mail_subject = "[TeamMoa] 회원가입 인증 메일입니다."
        email_message = EmailMessage(mail_subject, message, to=[user.email])
        email_message.send()

    # 3. with 블록이 예외 없이 성공적으로 끝나면, DB에 저장된 user가 최종 확정(commit)
    return user