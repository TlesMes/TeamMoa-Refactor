from dataclasses import field
import datetime
from django import forms

from .models import DevPhase, Team, Team_User

class CreateTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['title','maxuser','teampasswd', 'introduction']


class SearchTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['invitecode']

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