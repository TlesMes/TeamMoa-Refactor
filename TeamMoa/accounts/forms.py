from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm

#닉네임, 
class CustomUserChangeForm(UserChangeForm):
    password = None
    class Meta:
        model = get_user_model()
        fields = ['nickname', 'profile']