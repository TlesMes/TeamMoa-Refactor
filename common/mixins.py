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

        # Team 객체를 select_related/prefetch_related로 최적화하여 조회
        team = get_object_or_404(
            Team.objects.select_related('host').prefetch_related('members'),
            pk=kwargs['pk']
        )
        if request.user not in team.members.all():
            messages.error(request, "팀원이 아닙니다.")
            return redirect('teams:main_page')

        # View에서 재사용할 수 있도록 캐시에 저장
        self._team_cache = team

        return super().dispatch(request, *args, **kwargs)


class TeamHostRequiredMixin:
    """
    팀장만 접근 가능하도록 하는 Mixin
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/')

        # Team 객체를 select_related/prefetch_related로 최적화하여 조회
        team = get_object_or_404(
            Team.objects.select_related('host').prefetch_related('members'),
            pk=kwargs['pk']
        )
        if team.host != request.user:
            messages.error(request, "팀장이 아닙니다.")
            return redirect('teams:team_main_page', pk=team.pk)

        # View에서 재사용할 수 있도록 캐시에 저장
        self._team_cache = team

        return super().dispatch(request, *args, **kwargs)