from dataclasses import field
import datetime
from django import forms

from .models import DevPhase, Team, Team_User

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
        fields = ['maxuser','introduction']

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
