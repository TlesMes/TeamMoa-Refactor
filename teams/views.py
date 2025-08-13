from datetime import datetime
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.core.paginator import Paginator
from .models import DevPhase, Team, Team_User
from .forms import AddPhaseForm, ChangeTeamInfoForm, CreateTeamForm, JoinTeamForm, SearchTeamForm
import uuid
import base64
import codecs
# Create your views here.

#해당 팀 멤버가 아니면 차단
def is_member(request, pk) -> bool:
    user = request.user
    if not user.is_authenticated:
        return redirect('/accounts/login')

    if user.is_authenticated:
        team = get_object_or_404(Team, pk=pk)
        if user in team.members.all():
            return True
        else:
            return False

def main_page(request):
    """
    통합 메인 화면
    - 미로그인: 사이트 소개 + 로그인/회원가입 안내
    - 로그인: 팀 목록 화면
    """
    user = request.user
    if user.is_authenticated:
        # 로그인 상태: 팀 목록 표시
        joined_teams = Team.objects.filter(members=user).order_by('id')
        return render(request, 'teams/main_authenticated.html', {
            'teams': joined_teams
        })
    else:
        # 미로그인 상태: 랜딩 페이지
        return render(request, 'teams/main_landing.html')


def team_create(request):
    if request.method =='POST':
        form = CreateTeamForm(request.POST)
        if form.is_valid():
            user = request.user

            team = Team()
            team.title = form.cleaned_data['title']
            team.maxuser = form.cleaned_data['maxuser']
            team.teampasswd = form.cleaned_data['teampasswd']
            team.introduction = form.cleaned_data['introduction']
            team.host = user
            team.currentuser = 1
            team.invitecode = base64.urlsafe_b64encode(
                            codecs.encode(uuid.uuid4().bytes, "base64").rstrip()
                            ).decode()[:16]
            team.save()
            team.members.add(user)
            return redirect('teams:main_page')
    else:
        form = CreateTeamForm()
    return render(request,'teams/team_create.html',{'form':form})


def team_search(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('/accounts/login')
    
    if request.method =='POST':
        form = SearchTeamForm(request.POST)
        if form.is_valid():
            code=form.cleaned_data['invitecode']
            team = get_object_or_404(Team, invitecode=code)
            
            return redirect(f"/teams/team_join/{team.id}")   ##team id 넣어서 리다이렉트
    else:
        form = SearchTeamForm()
    return render(request, 'teams/team_search.html', {'form':form})


def team_join(request, pk):
    user = request.user
    team = get_object_or_404(Team, pk=pk)

    if not user.is_authenticated:
        return redirect('/accounts/login')

    if request.method =='POST':
        form = JoinTeamForm(request.POST)
        if form.is_valid():
            passwd=form.cleaned_data['teampasswd']
            team = get_object_or_404(Team, pk=pk)
            if team.teampasswd == passwd:
                if team.maxuser == team.currentuser:
                    return HttpResponse('<script>alert("팀 최대인원 초과.")</script>''<script>location.href="/teams/"</script>')
                team.members.add(user)
                team.currentuser += 1
                team.save()
                return redirect('teams:main_page')
            else:
                return HttpResponse('<script>alert("패스워드 다름.")</script>''<script>location.href="/teams/"</script>')
    else:
        form = JoinTeamForm()
    return render(request, 'teams/team_join.html', {'form':form, 'team':team})



def team_main_page(request, pk):
    if not is_member(request, pk):
        return HttpResponse('<script>alert("팀원이 아닙니다.")</script>''<script>location.href="/teams/"</script>')
    else:
        team = get_object_or_404(Team, pk=pk)
        members = Team_User.objects.filter(Team=team)
        phases = DevPhase.objects.filter(team=team).order_by('startdate')
        
        today_date = datetime.now().date()
        today_phase='일정이 없습니다.'
        for phase in phases:
            if (phase.startdate <= today_date) & (phase.enddate > today_date):
                left = phase.enddate-today_date
                today_phase = f'{phase.content}, {left.days}일 남았습니다'
                break
            else:
                today_phase = "일정이 없습니다."
        
        return render(request, 'teams/team_main_page.html', {'team':team, 'members':members,'phases':phases, 'today_date':today_date, 'today_phase':today_phase})


def team_info_change(request, pk):
    team = get_object_or_404(Team, pk=pk)
    user = request.user

    if team.host != user:
        return HttpResponse('<script>alert("팀장이 아닙니다.")</script>'f'<script>location.href="/teams/team_main_page/{pk}"</script>')
    else:
        if request.method =='POST':
            form = ChangeTeamInfoForm(request.POST)
            if form.is_valid():
                team.title = form.cleaned_data['title']
                team.maxuser = form.cleaned_data['maxuser']
                team.introduction = form.cleaned_data['introduction']
                team.save()
                return redirect(f'/teams/team_main_page/{pk}')
        else:
            form = ChangeTeamInfoForm()
        return render(request, 'teams/team_info_change.html', {'form':form, 'team':team})



def team_add_devPhase(request,pk):
    team = get_object_or_404(Team, pk=pk)
    user = request.user
    if team.host != user:
        return HttpResponse('<script>alert("팀장이 아닙니다.")</script>'f'<script>location.href="/teams/team_main_page/{pk}"</script>')
    else:
        if request.method =='POST':
            form = AddPhaseForm(request.POST)
            if form.is_valid():

                #겹치는 부분이 있는지 검사해야 함
                start=form.cleaned_data['startdate']
                end=form.cleaned_data['enddate']
                devphases = DevPhase.objects.filter(team=team)
                for p in devphases:
                    if (p.startdate < start) & (p.enddate > start):
                        return HttpResponse('<script>alert("개발 기간 중복.")</script>'f'<script>location.href="/teams/team_add_devPhase/{pk}"</script>')
                    if (p.startdate < end) & (p.enddate > end):
                        return HttpResponse('<script>alert("개발 기간 중복.")</script>'f'<script>location.href="/teams/team_add_devPhase/{pk}"</script>')
                    if (p.startdate > start) & (p.startdate < end):
                        return HttpResponse('<script>alert("개발 기간 중복.")</script>'f'<script>location.href="/teams/team_add_devPhase/{pk}"</script>')
                    
                
                phase = DevPhase()
                phase.team = team
                phase.content = form.cleaned_data['content']
                phase.startdate = form.cleaned_data['startdate']
                phase.enddate = form.cleaned_data['enddate']
                phase.save()

                return redirect(f'/teams/team_main_page/{pk}')
        else:
            form = AddPhaseForm()
        return render(request, 'teams/team_add_devPhase.html', {'form':form, 'team':team})

def team_delete_devPhase(request, pk, phase_id):
    team = get_object_or_404(Team, pk=pk)
    user = request.user
    if team.host != user:
        return HttpResponse('<script>alert("팀장이 아닙니다.")</script>'f'<script>location.href="/teams/team_main_page/{pk}"</script>')
    else:
        phase = DevPhase.objects.get(pk=phase_id)
        phase.delete()
        return redirect(f'/teams/team_main_page/{pk}')


def team_disband(request, pk):
    team = get_object_or_404(Team, pk=pk)
    user = request.user

    if team.host != user:
        return HttpResponse('<script>alert("팀장이 아닙니다.")</script>'f'<script>location.href="/teams/team_main_page/{pk}"</script>')
    else:
        team.delete()
        return redirect('teams:main_page')
