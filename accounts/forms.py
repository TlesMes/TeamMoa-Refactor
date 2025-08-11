from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
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
        cd = self.cleaned_data
        if cd.get('password') != cd.get('password2'):
            raise forms.ValidationError('비밀번호가 일치하지 않습니다.')
        return cd.get('password2')

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

#닉네임, 프로필 변경 폼
class CustomUserChangeForm(UserChangeForm):
    password = None
    class Meta:
        model = get_user_model()
        fields = ['nickname', 'profile']
