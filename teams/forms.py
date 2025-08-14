from dataclasses import field
import datetime
from django import forms
from django.core.exceptions import ValidationError
from .models import DevPhase, Team, TeamUser

class CreateTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['title', 'maxuser', 'teampasswd', 'introduction']
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'create_input'}
            ),
            'maxuser': forms.TextInput(
                attrs={'class': 'create_input'}
            ),
            'teampasswd': forms.TextInput(
                attrs={'class': 'create_input'}
            ),
            'introduction': forms.Textarea(
                attrs={'class': 'introduction', 'maxlength': '20'}
            )
        }
        labels = {
            'title': '팀명',
            'maxuser': '인원수',
            'teampasswd': '비밀번호',
            'introduction': '팀 소개',
        }


class SearchTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['invitecode']
        widgets = {
            'invitecode': forms.TextInput(
                attrs={'class': 'invitecode'}
            )
        }
        labels = {
            'invitecode' : ''
        }

class JoinTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['teampasswd']

class ChangeTeamInfoForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['title','maxuser','introduction']
    
    def clean_maxuser(self):
        maxuser = self.cleaned_data.get('maxuser')
        if self.instance and self.instance.pk:
            # 모델의 메서드를 사용하여 실제 팀원 수 확인
            current_member_count = self.instance.get_current_member_count()
            if maxuser < current_member_count:
                raise ValidationError(
                    f'최대 인원수는 현재 팀원 수({current_member_count}명)보다 적을 수 없습니다.'
                )
        return maxuser
    

class AddPhaseForm(forms.ModelForm):
    class Meta:
        model = DevPhase
        fields = ['startdate','enddate','content']
        widgets = {
            'startdate' : forms.DateTimeInput(
            attrs={
                'type': 'date',
                'class' : 'form-control'
            }),
            'enddate' : forms.DateTimeInput(
            attrs={
                'type': 'date',
                'class' : 'form-control'
            })
        }
