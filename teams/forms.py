from dataclasses import field
import datetime
from django import forms
from django.core.exceptions import ValidationError
from .models import Milestone, Team, TeamUser

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
    
    def clean_maxuser(self):
        maxuser = self.cleaned_data.get('maxuser')
        if maxuser is not None:
            if maxuser < 1:
                raise ValidationError('팀 인원수는 1명 이상이어야 합니다.')
            if maxuser > 100:
                raise ValidationError('팀 인원수는 100명을 초과할 수 없습니다.')
        return maxuser


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
    

class AddMilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'description', 'startdate', 'enddate', 'priority']
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '마일스톤 제목'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control', 
                    'rows': 3,
                    'placeholder': '마일스톤 설명'
                }
            ),
            'startdate': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'enddate': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'priority': forms.Select(
                attrs={'class': 'form-control'}
            )
        }
    
    def clean(self):
        cleaned_data = super().clean()
        startdate = cleaned_data.get('startdate')
        enddate = cleaned_data.get('enddate')
        
        if startdate and enddate:
            if startdate >= enddate:
                raise ValidationError('시작일은 종료일보다 이전이어야 합니다.')
        
        return cleaned_data
