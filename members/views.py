from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.views import View
from members.forms import CreateTodoForm
from members.models import Todo
from teams.models import Team, TeamUser
from django.http import HttpResponseRedirect, HttpResponse
from common.mixins import TeamMemberRequiredMixin

class TeamMembersPageView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'members/team_members_page.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=kwargs['pk'])
        members = TeamUser.objects.filter(team=team)
        todos = Todo.objects.filter(owner__team=team)
        form = CreateTodoForm()
        
        context.update({
            'team': team,
            'members': members,
            'todos': todos,
            'form': form
        })
        return context
    
    def post(self, request, pk):
        form = CreateTodoForm(request.POST)
        if form.is_valid():
            self.member_add_todo(request, pk, form.cleaned_data['content'])
        return redirect('members:team_members_page', pk=pk)
    
    def member_add_todo(self, request, pk, content):
        user = request.user
        team = get_object_or_404(Team, pk=pk)
        teamuser = TeamUser.objects.get(team=team, user=user)
        todo = Todo()
        todo.content = content
        todo.owner = teamuser
        todo.save()


team_members_page = TeamMembersPageView.as_view()

class MemberCompleteTodoView(TeamMemberRequiredMixin, View):
    def get(self, request, pk, todo_id):
        todo = get_object_or_404(Todo, pk=todo_id)
        todo.is_completed = not todo.is_completed
        todo.save()
        return redirect('members:team_members_page', pk=pk)


class MemberDeleteTodoView(TeamMemberRequiredMixin, View):
    def get(self, request, pk, todo_id):
        todo = get_object_or_404(Todo, pk=todo_id)
        todo.delete()
        return redirect('members:team_members_page', pk=pk)


member_complete_Todo = MemberCompleteTodoView.as_view()
member_delete_Todo = MemberDeleteTodoView.as_view()