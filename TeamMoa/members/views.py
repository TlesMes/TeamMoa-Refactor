from django.shortcuts import render,redirect,get_object_or_404
from members.forms import CreateTodoForm
from members.models import Todo
from teams.models import Team, Team_User
from django.http import HttpResponseRedirect,HttpResponse
# Create your views here.

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


def team_members_page(request, pk):
    if not is_member(request, pk):
        return HttpResponse('<script>alert("팀원이 아닙니다.")</script>''<script>location.href="/teams/team_list"</script>')
    else:
        team = get_object_or_404(Team, pk=pk)
        members = Team_User.objects.filter(Team=team)
        todos = Todo.objects.filter(team = team)
        return render(request, 'members/team_members_page.html', {'members':members, 'todos':todos, 'team':team})

def member_add_Todo(request, pk):
    user = request.user
    team = get_object_or_404(Team, pk=pk)
    teamuser = Team_User.objects.get(Team=team,User=user)
    members = Team_User.objects.filter(Team=team)
    todos = Todo.objects.filter(team = team)
    if request.method =='POST':
        form = CreateTodoForm(request.POST)
        if form.is_valid():
            todo = Todo()
            todo.content = form.cleaned_data['content']
            todo.team = team
            todo.owner = teamuser
            todo.save()
        return redirect(f'/members/team_members_page/{pk}')
    form = CreateTodoForm()
    return render(request, 'members/member_add_Todo.html', {'form':form})
    
def member_complete_Todo(request, pk, todo_id):
    user = request.user
    team = get_object_or_404(Team, pk=pk)
    todo = Todo.objects.get(pk=todo_id)
    todo.is_completed = not todo.is_completed
    todo.save()
    return redirect(f'/members/team_members_page/{pk}')

def member_delete_Todo(request, pk, todo_id):
    user = request.user
    team = get_object_or_404(Team, pk=pk)
    todo = Todo.objects.get(pk=todo_id)
    todo.delete()
    return redirect(f'/members/team_members_page/{pk}')