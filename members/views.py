from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.views import View
from django.db.models import Count, Q, Prefetch
from members.forms import CreateTodoForm
from members.models import Todo
from teams.models import Team, TeamUser, Milestone
from django.contrib import messages
from common.mixins import TeamMemberRequiredMixin
from django.utils import timezone
from .services import TodoService

# URL 패턴 상수
TEAM_MEMBERS_PAGE = 'members:team_members_page'


class TeamMembersPageView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'members/team_members_page.html'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.todo_service = TodoService()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=kwargs['pk'])
        
        # 서비스에서 최적화된 데이터 조회
        todo_data = self.todo_service.get_team_todos_with_stats(team)
        form = CreateTodoForm()
        
        # 현재 사용자가 팀장인지 확인
        is_host = team.host == self.request.user

        # 마일스톤 목록 조회 (TODO 할당용)
        milestones = Milestone.objects.filter(
            team=team,
            is_completed=False
        ).order_by('enddate', 'priority')

        context.update({
            'team': team,
            'members': todo_data['members'],
            'todos_unassigned': todo_data['todos_unassigned'],
            'todos_done': todo_data['todos_done'],
            'members_data': todo_data['members_data'],
            'milestones': milestones,
            'form': form,
            'is_host': is_host
        })
        return context
    
    def post(self, request, pk):
        form = CreateTodoForm(request.POST)
        if form.is_valid():
            try:
                team = get_object_or_404(Team, pk=pk)
                self.todo_service.create_todo(
                    team=team,
                    content=form.cleaned_data['content'],
                    creator=request.user
                )
                messages.success(request, '할 일이 성공적으로 추가되었습니다.')
            except ValueError as e:
                messages.error(request, str(e))
        return redirect(TEAM_MEMBERS_PAGE, pk=pk)


team_members_page = TeamMembersPageView.as_view()




