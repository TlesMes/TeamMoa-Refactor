from django.test import TestCase, Client
from django.urls import reverse
from .models import User
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

class AccountFlowTest(TestCase):

    def test_signup_and_activation_flow(self):
        """
        회원가입부터 활성화까지 전체 흐름(통합 테스트)을 테스트합니다.
        form.save()로 생성된 사용자가 올바르게 활성화되는지 확인합니다.
        """
        # 1. 준비: 회원가입에 사용할 유효한 폼 데이터
        signup_data = {
            'username': 'shdkseho',
            'password': '123',
            'password2': '123',
            'email': 'shdkseho@naver.com',
            'nickname': '싱생송',
            'profile': '테스트 프로필'
        }

        # 2. 실행 1단계: 가상 클라이언트로 회원가입(POST) 요청을 보냄
        # 이 요청으로 views.signup -> services.register_user -> forms.SignupForm.save()가 순서대로 호출됩니다.
        signup_url = reverse('accounts:signup')
        self.client.post(signup_url, signup_data)

        # 3. 중간 검증: form.save()로 생성된 사용자를 DB에서 가져와 상태를 확인
        user = User.objects.get(username=signup_data['username'])
        self.assertFalse(user.is_active) # 생성 직후에는 반드시 비활성 상태여야 합니다.

        # 4. 실행 2단계: 위 사용자를 위한 활성화 링크를 만들고, 가상 클라이언트로 접속
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        activation_url = reverse('accounts:activate', kwargs={'uid64': uid, 'token': token})
        print(activation_url)
        response = self.client.get(activation_url)

        # 5. 최종 결과 검증: 사용자가 성공적으로 활성화되었는지 확인
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('teams:main_page'))
