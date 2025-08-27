from datetime import datetime
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, FormView, UpdateView, DeleteView
from django.views import View
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from .models import Milestone, Team, TeamUser
from .forms import AddMilestoneForm, ChangeTeamInfoForm, CreateTeamForm, JoinTeamForm, SearchTeamForm
from common.mixins import TeamMemberRequiredMixin, TeamHostRequiredMixin
import uuid
import base64
import codecs


class MainPageView(TemplateView):
    """
    통합 메인 화면
    - 미로그인: 사이트 소개 + 로그인/회원가입 안내
    - 로그인: 팀 목록 화면
    """
    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ['teams/main_authenticated.html']
        return ['teams/main_landing.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['teams'] = Team.objects.filter(members=self.request.user).order_by('id')
        return context


main_page = MainPageView.as_view()


class TeamCreateView(LoginRequiredMixin, FormView):
    template_name = 'teams/team_create.html'
    form_class = CreateTeamForm
    success_url = reverse_lazy('teams:main_page')
    login_url = '/accounts/login/'
    
    def form_valid(self, form):
        team = Team()
        team.title = form.cleaned_data['title']
        team.maxuser = form.cleaned_data['maxuser']
        team.teampasswd = form.cleaned_data['teampasswd']
        team.introduction = form.cleaned_data['introduction']
        team.host = self.request.user
        team.currentuser = 1
        team.invitecode = base64.urlsafe_b64encode(
                        codecs.encode(uuid.uuid4().bytes, "base64").rstrip()
                        ).decode()[:16]
        team.save()
        team.members.add(self.request.user)
        messages.success(self.request, '팀이 성공적으로 생성되었습니다.')
        return super().form_valid(form)


team_create = TeamCreateView.as_view()


class TeamSearchView(LoginRequiredMixin, FormView):
    template_name = 'teams/team_search.html'
    form_class = SearchTeamForm
    login_url = '/accounts/login/'
    
    def form_valid(self, form):
        code = form.cleaned_data['invitecode']
        try:
            team = get_object_or_404(Team, invitecode=code)
            return redirect('teams:team_join', pk=team.id)
        except:
            messages.error(self.request, '유효하지 않은 초대 코드입니다.')
            return self.form_invalid(form)


team_search = TeamSearchView.as_view()


class TeamJoinView(LoginRequiredMixin, FormView):
    template_name = 'teams/team_join.html'
    form_class = JoinTeamForm
    login_url = '/accounts/login/'
    
    def get_success_url(self):
        return reverse('teams:main_page')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = get_object_or_404(Team, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        passwd = form.cleaned_data['teampasswd']
        
        if team.teampasswd != passwd:
            messages.error(self.request, '패스워드가 다릅니다.')
            return self.form_invalid(form)
        
        if team.maxuser == team.currentuser:
            messages.error(self.request, '팀 최대인원을 초과했습니다.')
            return redirect('teams:main_page')
        
        if self.request.user in team.members.all():
            messages.info(self.request, '이미 가입된 팀입니다.')
            return redirect('teams:main_page')
        
        team.members.add(self.request.user)
        team.currentuser += 1
        team.save()
        messages.success(self.request, f'{team.title} 팀에 성공적으로 가입했습니다.')
        return super().form_valid(form)


team_join = TeamJoinView.as_view()



class TeamMainPageView(TeamMemberRequiredMixin, DetailView):
    model = Team
    template_name = 'teams/team_main_page.html'
    context_object_name = 'team'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_object()
        
        context['members'] = TeamUser.objects.filter(team=team)
        context['milestones'] = Milestone.objects.filter(team=team).order_by('priority', 'enddate')
        context['today_date'] = datetime.now().date()
        
        # 오늘 진행 중인 마일스톤 찾기
        today_milestone = '진행 중인 마일스톤이 없습니다.'
        active_milestones = [m for m in context['milestones'] if not m.is_completed and m.startdate <= context['today_date'] <= m.enddate]
        if active_milestones:
            milestone = active_milestones[0]
            left = milestone.enddate - context['today_date']
            today_milestone = f'{milestone.title}, {left.days}일 남았습니다'
        
        context['today_milestone'] = today_milestone
        return context


team_main_page = TeamMainPageView.as_view()


class TeamInfoChangeView(TeamHostRequiredMixin, UpdateView):
    model = Team
    form_class = ChangeTeamInfoForm
    template_name = 'teams/team_info_change.html'
    context_object_name = 'team'
    
    def get_success_url(self):
        messages.success(self.request, '팀 정보가 성공적으로 수정되었습니다.')
        return reverse('teams:team_main_page', kwargs={'pk': self.object.pk})


team_info_change = TeamInfoChangeView.as_view()



class TeamAddMilestoneView(TeamHostRequiredMixin, FormView):
    template_name = 'teams/team_add_milestone.html'
    form_class = AddMilestoneForm
    
    def get_success_url(self):
        return reverse('teams:team_main_page', kwargs={'pk': self.kwargs['pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = get_object_or_404(Team, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        
        # 새 마일스톤 생성
        Milestone.objects.create(
            team=team,
            title=form.cleaned_data['title'],
            description=form.cleaned_data['description'],
            startdate=form.cleaned_data['startdate'],
            enddate=form.cleaned_data['enddate'],
            priority=form.cleaned_data['priority']
        )
        
        messages.success(self.request, '마일스톤이 성공적으로 추가되었습니다.')
        return super().form_valid(form)


team_add_milestone = TeamAddMilestoneView.as_view()

class TeamDeleteMilestoneView(TeamHostRequiredMixin, View):
    def post(self, request, pk, milestone_id):
        team = get_object_or_404(Team, pk=pk)
        milestone = get_object_or_404(Milestone, pk=milestone_id)
        
        milestone_title = milestone.title
        milestone.delete()
        
        messages.success(request, f'마일스톤 "{milestone_title}"가 성공적으로 삭제되었습니다.')
        return redirect('teams:team_main_page', pk=pk)


team_delete_milestone = TeamDeleteMilestoneView.as_view()


class TeamDisbandView(TeamHostRequiredMixin, View):
    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        team_title = team.title
        team.delete()
        messages.success(request, f'"{team_title}" 팀이 성공적으로 해체되었습니다.')
        return redirect('teams:main_page')


team_disband = TeamDisbandView.as_view()
