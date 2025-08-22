from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from teams.models import Team


class TeamMemberRequiredMixin:
    """
    팀 멤버만 접근 가능하도록 하는 Mixin
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/')
        
        team = get_object_or_404(Team, pk=kwargs['pk'])
        if request.user not in team.members.all():
            messages.error(request, "팀원이 아닙니다.")
            return redirect('teams:main_page')
        
        return super().dispatch(request, *args, **kwargs)


class TeamHostRequiredMixin:
    """
    팀장만 접근 가능하도록 하는 Mixin
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/')
        
        team = get_object_or_404(Team, pk=kwargs['pk'])
        if team.host != request.user:
            messages.error(request, "팀장이 아닙니다.")
            return redirect('teams:team_main_page', pk=team.pk)
        
        return super().dispatch(request, *args, **kwargs)