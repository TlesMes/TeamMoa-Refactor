from dataclasses import field
import datetime
from django import forms
from django.core.exceptions import ValidationError
from .models import Milestone, Team, TeamUser

class CreateTeamForm(forms.ModelForm):
    # 필수 필드를 JavaScript에서 검증하므로 HTML required 제거
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'create_input'}),
        label='팀명'
    )
    maxuser = forms.IntegerField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'create_input', 'type': 'text'}),
        label='인원수'
    )
    teampasswd = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'create_input'}),
        label='비밀번호'
    )
    introduction = forms.CharField(
        required=False,  # JavaScript에서 검증, HTML required 제거
        widget=forms.Textarea(attrs={
            'class': 'introduction',
            'maxlength': '200',
            'style': 'resize: vertical; min-height: 100px; padding: 12px;'
        }),
        label='팀 소개'
    )

    class Meta:
        model = Team
        fields = ['title', 'maxuser', 'teampasswd', 'introduction']

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or not title.strip():
            raise ValidationError('팀명을 입력해주세요.')
        return title

    def clean_maxuser(self):
        maxuser = self.cleaned_data.get('maxuser')
        if maxuser is None:
            raise ValidationError('최대 인원수를 입력해주세요.')
        if maxuser < 1:
            raise ValidationError('팀 인원수는 1명 이상이어야 합니다.')
        if maxuser > 100:
            raise ValidationError('팀 인원수는 100명을 초과할 수 없습니다.')
        return maxuser

    def clean_teampasswd(self):
        teampasswd = self.cleaned_data.get('teampasswd')
        if not teampasswd or not teampasswd.strip():
            raise ValidationError('팀 비밀번호를 입력해주세요.')
        return teampasswd

    def clean_introduction(self):
        introduction = self.cleaned_data.get('introduction', '')
        if not introduction or not introduction.strip():
            raise ValidationError('팀 소개를 입력해주세요.')
        return introduction.strip()


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
        widgets = {
            'teampasswd': forms.PasswordInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '팀 비밀번호를 입력하세요'
                }
            )
        }
        labels = {
            'teampasswd': '팀 비밀번호'
        }

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
    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop('team', None)
        super().__init__(*args, **kwargs)
    
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
        title = cleaned_data.get('title')
        
        # 날짜 검증
        if startdate and enddate:
            if startdate >= enddate:
                raise ValidationError('시작일은 종료일보다 이전이어야 합니다.')
            
            # 너무 긴 기간 검증 (1년 이상)
            duration = (enddate - startdate).days
            if duration > 365:
                raise ValidationError('마일스톤 기간은 1년을 초과할 수 없습니다.')
            elif duration == 0:
                raise ValidationError('마일스톤은 최소 1일 이상이어야 합니다.')
        
        # 제목 길이 검증
        if title and len(title.strip()) < 2:
            raise ValidationError('마일스톤 제목은 최소 2글자 이상 입력해주세요.')
            
        # 제목 중복 검증 (같은 팀 내에서)
        if title and self.team:
            if Milestone.objects.filter(team=self.team, title=title.strip()).exists():
                raise ValidationError('같은 이름의 마일스톤이 이미 존재합니다.')
        
        return cleaned_data
