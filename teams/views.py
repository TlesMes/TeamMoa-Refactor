from datetime import datetime
import json
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, FormView, UpdateView, DeleteView
from django.views import View
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db import models
from .models import Milestone, Team, TeamUser
from .forms import AddMilestoneForm, ChangeTeamInfoForm, CreateTeamForm, JoinTeamForm, SearchTeamForm
from .services import TeamService, MilestoneService
from common.mixins import TeamMemberRequiredMixin, TeamHostRequiredMixin


class MainPageView(TemplateView):
    """
    통합 메인 화면
    - 미로그인: 사이트 소개 + 로그인/회원가입 안내
    - 로그인: 팀 목록 화면
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team_service = TeamService()
    
    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ['teams/main_authenticated.html']
        return ['teams/main_landing.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['teams'] = self.team_service.get_user_teams(self.request.user)
        return context


main_page = MainPageView.as_view()


class TeamCreateView(LoginRequiredMixin, FormView):
    template_name = 'teams/team_create.html'
    form_class = CreateTeamForm
    success_url = reverse_lazy('teams:main_page')
    login_url = '/accounts/login/'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team_service = TeamService()
    
    def form_valid(self, form):
        try:
            team = self.team_service.create_team(
                host_user=self.request.user,
                title=form.cleaned_data['title'],
                maxuser=form.cleaned_data['maxuser'],
                teampasswd=form.cleaned_data['teampasswd'],
                introduction=form.cleaned_data['introduction']
            )
            messages.success(self.request, '팀이 성공적으로 생성되었습니다.')
            return super().form_valid(form)
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


team_create = TeamCreateView.as_view()


class TeamSearchView(LoginRequiredMixin, TemplateView):
    """
    통합 팀 가입 페이지 - AJAX 방식으로만 처리
    더 이상 POST form을 직접 처리하지 않음
    """
    template_name = 'teams/team_search.html'
    login_url = '/accounts/login/'
    
    def get(self, request, *args, **kwargs):
        # URL에 파라미터가 있으면 깨끗한 URL로 리다이렉트
        if request.GET:
            messages.warning(
                request, 
                '보안을 위해 페이지 내 검색 기능을 이용해주세요.'
            )
            return redirect('teams:team_search')
        return super().get(request, *args, **kwargs)


team_search = TeamSearchView.as_view()


class TeamVerifyCodeView(LoginRequiredMixin, View):
    """
    AJAX 엔드포인트: 팀 코드 검증 및 팀 정보 반환
    """
    login_url = '/accounts/login/'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team_service = TeamService()
    
    def post(self, request):
        try:
            invite_code = request.POST.get('invitecode', '').strip()
            
            team_info = self.team_service.verify_team_code(invite_code, request.user)
            
            return JsonResponse({
                'success': True,
                'team': team_info
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': '서버 오류가 발생했습니다. 다시 시도해주세요.'
            })


team_verify_code = TeamVerifyCodeView.as_view()


class TeamJoinProcessView(LoginRequiredMixin, View):
    """
    AJAX 엔드포인트: 팀 비밀번호 검증 및 최종 가입 처리
    """
    login_url = '/accounts/login/'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team_service = TeamService()
    
    def post(self, request):
        try:
            team_id = request.POST.get('team_id')
            team_password = request.POST.get('teampasswd', '').strip()
            
            team = self.team_service.join_team(
                user=request.user,
                team_id=team_id,
                password=team_password
            )
            
            return JsonResponse({
                'success': True,
                'message': f'{team.title} 팀에 성공적으로 가입했습니다!',
                'team_name': team.title
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': '서버 오류가 발생했습니다. 다시 시도해주세요.'
            })


team_join_process = TeamJoinProcessView.as_view()


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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team_service = TeamService()
        self.milestone_service = MilestoneService()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_object()
        today_date = datetime.now().date()
        
        context['members'] = TeamUser.objects.filter(team=team)
        milestones = self.milestone_service.get_team_milestones(team)
        context['milestones'] = milestones
        context['today_date'] = today_date
        
        # QuerySet 재사용하여 통계 계산 (중복 쿼리 방지)
        stats = self.team_service.get_team_statistics(team, milestones=milestones)
        context.update(stats)
        
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.milestone_service = MilestoneService()
    
    def get_success_url(self):
        return reverse('teams:team_main_page', kwargs={'pk': self.kwargs['pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = get_object_or_404(Team, pk=self.kwargs['pk'])
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        kwargs['team'] = team
        return kwargs
    
    def form_valid(self, form):
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        
        try:
            self.milestone_service.create_milestone(
                team=team,
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                startdate=form.cleaned_data['startdate'],
                enddate=form.cleaned_data['enddate'],
                priority=form.cleaned_data['priority']
            )
            messages.success(self.request, '마일스톤이 성공적으로 추가되었습니다.')
            return super().form_valid(form)
            
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'마일스톤 저장에 실패했습니다: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        # 폼 검증 실패시 구체적 오류 메시지
        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                if field == 'startdate':
                    error_messages.append(f'시작일 오류: {error}')
                elif field == 'enddate':
                    error_messages.append(f'종료일 오류: {error}')
                elif field == 'title':
                    error_messages.append(f'제목 오류: {error}')
                elif field == '__all__':
                    error_messages.append(error)
                else:
                    error_messages.append(f'{field}: {error}')
        
        if error_messages:
            messages.error(self.request, ' / '.join(error_messages))
        
        return super().form_invalid(form)


team_add_milestone = TeamAddMilestoneView.as_view()


class TeamMilestoneTimelineView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'teams/team_milestone_timeline.html'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.milestone_service = MilestoneService()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        
        context.update({
            'team': team,
            'milestones': self.milestone_service.get_team_milestones(
                team, order_by=['startdate', 'enddate']
            ),
        })
        return context


team_milestone_timeline = TeamMilestoneTimelineView.as_view()



class MilestoneUpdateAjaxView(TeamMemberRequiredMixin, View):
    """AJAX를 통한 마일스톤 업데이트"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.milestone_service = MilestoneService()
    
    def post(self, request, pk, milestone_id):
        try:
            team = get_object_or_404(Team, pk=pk)
            
            # JSON 데이터 파싱
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            milestone, updated_fields = self.milestone_service.update_milestone(
                milestone_id=milestone_id,
                team=team,
                **data
            )
            
            return JsonResponse({
                'success': True,
                'message': f"마일스톤 {', '.join(updated_fields)}이(가) 업데이트되었습니다.",
                'milestone': {
                    'id': milestone.id,
                    'title': milestone.title,
                    'startdate': milestone.startdate.isoformat() if milestone.startdate else None,
                    'enddate': milestone.enddate.isoformat() if milestone.enddate else None,
                    'progress_percentage': milestone.progress_percentage,
                    'is_completed': milestone.is_completed,
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '잘못된 JSON 형식입니다.'
            }, status=400)
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'업데이트 중 오류가 발생했습니다: {str(e)}'
            }, status=500)


milestone_update_ajax = MilestoneUpdateAjaxView.as_view()


class MilestoneDeleteAjaxView(TeamMemberRequiredMixin, View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.milestone_service = MilestoneService()
        
    def post(self, request, pk, milestone_id):
        try:
            team = get_object_or_404(Team, pk=pk)
            milestone_title = self.milestone_service.delete_milestone(milestone_id, team)
            
            messages.success(request, f'"{milestone_title}" 마일스톤이 삭제되었습니다.')
            return HttpResponse(status=200)
            
        except Exception as e:
            messages.error(request, f'마일스톤 삭제 중 오류가 발생했습니다: {str(e)}')
            return HttpResponse(status=500)


milestone_delete_ajax = MilestoneDeleteAjaxView.as_view()


class TeamDisbandView(TeamHostRequiredMixin, View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team_service = TeamService()
        
    def post(self, request, pk):
        try:
            team_title = self.team_service.disband_team(pk, request.user)
            messages.success(request, f'"{team_title}" 팀이 성공적으로 해체되었습니다.')
            return redirect('teams:main_page')
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('teams:team_main_page', pk=pk)


team_disband = TeamDisbandView.as_view()
