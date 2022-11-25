from dataclasses import field
import datetime
from django import forms

from .models import Team, Team_User

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