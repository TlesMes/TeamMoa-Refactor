from django.shortcuts import render,redirect,get_object_or_404
from members.forms import CreateTodoForm
from members.models import Todo
from teams.models import Team, TeamUser
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
        return HttpResponse('<script>alert("팀원이 아닙니다.")</script>''<script>location.href="/teams/"</script>')
    else:
        team = get_object_or_404(Team, pk=pk)
        members = TeamUser.objects.filter(team=team)
        todos = Todo.objects.filter(owner__team=team)
        if request.method =='POST':
            form = CreateTodoForm(request.POST)
            if form.is_valid():
                member_add_Todo(request, pk ,form.cleaned_data['content'])
            return redirect(f'/members/team_members_page/{pk}')
        
        form = CreateTodoForm()
        return render(request, 'members/team_members_page.html', {'members':members, 'todos':todos, 'team':team, 'form':form})

def member_add_Todo(request, pk, content):
    user = request.user
    team = get_object_or_404(Team, pk=pk)
    teamuser = TeamUser.objects.get(team=team, user=user)
    todo = Todo()
    todo.content = content
    todo.owner = teamuser
    todo.save()
    
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