from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django import forms
from .models import User
import re # 이메일 유효성 검사를 위해 re 모듈 추가


class SignupForm(forms.ModelForm):
    password2 = forms.CharField(
        label = 'Confirm Password',
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'nickname', 'profile']
        widgets = {
            'password': forms.PasswordInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 원하는 순서로 필드 재배치
        new_order = ['username', 'password', 'password2', 'email', 'nickname', 'profile']
        self.fields = {k: self.fields[k] for k in new_order if k in self.fields}

    def clean_password2(self):
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        
        # 1. 비밀번호 일치 검사
        if password1 != password2:
            raise forms.ValidationError('비밀번호가 일치하지 않습니다.')
        
        # 2. Django AUTH_PASSWORD_VALIDATORS 검증 추가
        if password1:
            try:
                password_validation.validate_password(password1, self.instance)
            except forms.ValidationError as error:
                # Django 검증 에러를 한글로 변환
                korean_messages = []
                for message in error.messages:
                    if 'password is too short' in message or 'must contain at least' in message:
                        korean_messages.append('비밀번호는 최소 8자 이상이어야 합니다.')
                    elif 'password is too common' in message or 'common password' in message:
                        korean_messages.append('너무 일반적인 비밀번호입니다.')
                    elif 'password is entirely numeric' in message or 'entirely numeric' in message:
                        korean_messages.append('비밀번호가 모두 숫자로만 구성되어 있습니다.')
                    elif 'similar to the' in message or 'too similar' in message:
                        korean_messages.append('비밀번호가 개인 정보와 너무 유사합니다.')
                    else:
                        korean_messages.append(str(message))
                
                raise forms.ValidationError(korean_messages)
        
        return password2

    def clean_username(self):
        # username (로그인 ID) 중복 검사
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('이미 사용중인 사용자 ID입니다.') # 메시지 변경
        return username

    def clean_email(self):
        # email 필드 유효성 및 중복 검사
        email = self.cleaned_data.get('email')
        REGEX_EMAIL = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.fullmatch(REGEX_EMAIL, email):
            raise forms.ValidationError("이메일 형식이 맞지 않습니다.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('이미 사용중인 이메일입니다.')
        return email
    
    def save(self, commit=True):
        # form.save()를 사용하기 위해 create_user에서 처리하던 암호화처리를 사용
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_active = False 
        if commit:
            user.save()
        return user

# 닉네임, 프로필 변경 폼
class CustomUserChangeForm(UserChangeForm):
    password = None
    class Meta:
        model = get_user_model()
        fields = ['nickname', 'profile']


# 비밀번호 변경 폼 - 한글 메시지로 커스터마이징
class CustomPasswordChangeForm(PasswordChangeForm):
    error_messages = dict(PasswordChangeForm.error_messages, **{
        'password_incorrect': "현재 비밀번호가 올바르지 않습니다. 다시 입력해주세요.",
    })
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = "현재 비밀번호"
        self.fields['new_password1'].label = "새 비밀번호"
        self.fields['new_password2'].label = "새 비밀번호 확인"
        
        # 도움말 텍스트도 한글로
        self.fields['new_password1'].help_text = None
        self.fields['new_password2'].help_text = "확인을 위해 새 비밀번호를 다시 입력해주세요."
