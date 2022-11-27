from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.core.paginator import Paginator
from .models import Team, Team_User
from .forms import CreateTeamForm, JoinTeamForm, SearchTeamForm
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

def team_list(request):
    user = request.user
    if user.is_authenticated:
        joined_teams = Team.objects.filter(members=user).order_by('id')
        page = request.GET.get('page',1)
        mypaginator = Paginator(joined_teams, 5)
        myteams = mypaginator.get_page(page)
    return render(request, 'teams/team_list.html', {'teams': myteams})


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
            return redirect('/teams/team_list')
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
                team.members.add(user)
                team.currentuser += 1
                team.save()
                return redirect('/teams/team_list')
            else:
                return HttpResponse('<script>alert("패스워드 다름.")</script>''<script>location.href="/teams/team_list"</script>')
    else:
        form = JoinTeamForm()
    return render(request, 'teams/team_join.html', {'form':form, 'team':team})



def team_main_page(request, pk):
    if not is_member(request, pk):
        return HttpResponse('<script>alert("팀원이 아닙니다.")</script>''<script>location.href="/teams/team_list"</script>')
    else:
        team = get_object_or_404(Team, pk=pk)
        members = Team_User.objects.filter(Team=team)
        return render(request, 'teams/team_main_page.html', {'team':team, 'members':members})





def team_mindmap(request, pk):
    pass

def team_schedule(request, pk):
    pass