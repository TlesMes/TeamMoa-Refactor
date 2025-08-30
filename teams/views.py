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
    
    def post(self, request):
        try:
            invite_code = request.POST.get('invitecode', '').strip()
            
            if not invite_code:
                return JsonResponse({
                    'success': False,
                    'error': '팀 코드를 입력해주세요.'
                })
            
            try:
                team = Team.objects.get(invitecode=invite_code)
            except Team.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '유효하지 않은 팀 코드입니다.'
                })
            
            # 현재 사용자가 이미 팀 멤버인지 확인
            if TeamUser.objects.filter(team=team, user=request.user).exists():
                return JsonResponse({
                    'success': False,
                    'error': '이미 가입된 팀입니다.'
                })
            
            # 팀 인원이 가득 찼는지 확인
            current_member_count = team.get_current_member_count()
            if current_member_count >= team.maxuser:
                return JsonResponse({
                    'success': False,
                    'error': '팀 최대인원을 초과했습니다.'
                })
            
            return JsonResponse({
                'success': True,
                'team': {
                    'id': team.id,
                    'title': team.title,
                    'current_members': current_member_count,
                    'maxuser': team.maxuser,
                    'host_name': team.host.nickname if team.host.nickname else team.host.username,
                    'introduction': team.introduction if team.introduction else None
                }
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
    
    def post(self, request):
        try:
            team_id = request.POST.get('team_id')
            team_password = request.POST.get('teampasswd', '').strip()
            
            if not team_id or not team_password:
                return JsonResponse({
                    'success': False,
                    'error': '필수 정보가 누락되었습니다.'
                })
            
            try:
                team = Team.objects.get(id=team_id)
            except Team.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '존재하지 않는 팀입니다.'
                })
            
            # 비밀번호 확인
            if team.teampasswd != team_password:
                return JsonResponse({
                    'success': False,
                    'error': '팀 비밀번호가 올바르지 않습니다.'
                })
            
            # 다시 한번 중복 가입 체크
            if TeamUser.objects.filter(team=team, user=request.user).exists():
                return JsonResponse({
                    'success': False,
                    'error': '이미 가입된 팀입니다.'
                })
            
            # 다시 한번 인원 체크
            current_member_count = team.get_current_member_count()
            if current_member_count >= team.maxuser:
                return JsonResponse({
                    'success': False,
                    'error': '팀 최대인원을 초과했습니다.'
                })
            
            # 팀 가입 처리
            TeamUser.objects.create(
                team=team,
                user=request.user
            )
            
            # 현재 인원수 업데이트 (기존 로직 유지)
            team.currentuser = team.get_current_member_count()
            team.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{team.title} 팀에 성공적으로 가입했습니다!',
                'team_name': team.title
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_object()
        today_date = datetime.now().date()
        
        context['members'] = TeamUser.objects.filter(team=team)
        milestones = Milestone.objects.filter(team=team).order_by('priority', 'enddate')
        context['milestones'] = milestones
        context['today_date'] = today_date
        
        # 마일스톤 통계 계산 (새로운 상태 기준)
        not_started_count = 0
        in_progress_count = 0
        completed_count = 0
        overdue_count = 0
        
        for milestone in milestones:
            status = milestone.get_status(today_date)
            if status == 'not_started':
                not_started_count += 1
            elif status == 'in_progress':
                in_progress_count += 1
            elif status == 'completed':
                completed_count += 1
            elif status == 'overdue':
                overdue_count += 1
        
        # 각 상태별 개수를 개별적으로 전달
        context['not_started_count'] = not_started_count
        context['in_progress_count'] = in_progress_count
        context['completed_count'] = completed_count
        context['overdue_count'] = overdue_count
        
        # 기존 변수들도 유지 (호환성)
        context['active_milestones_count'] = in_progress_count + not_started_count
        context['completed_milestones_count'] = completed_count
        context['overdue_milestones_count'] = overdue_count
        
        # 오늘 진행 중인 마일스톤 찾기
        today_milestone = '진행 중인 마일스톤이 없습니다.'
        active_milestones = [m for m in milestones if m.get_status(today_date) == 'in_progress']
        if active_milestones:
            milestone = active_milestones[0]
            left = milestone.enddate - today_date
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
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        kwargs['team'] = team
        return kwargs
    
    def form_valid(self, form):
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        
        try:
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
            
        except Exception as e:
            # DB 저장 실패시 사용자 친화적 메시지
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        
        # 팀의 모든 마일스톤을 날짜순으로 정렬
        milestones = Milestone.objects.filter(team=team).order_by('startdate', 'enddate')
        
        context.update({
            'team': team,
            'milestones': milestones,
        })
        return context


team_milestone_timeline = TeamMilestoneTimelineView.as_view()



class MilestoneUpdateAjaxView(TeamMemberRequiredMixin, View):
    """AJAX를 통한 마일스톤 업데이트"""
    
    def post(self, request, pk, milestone_id):
        try:
            team = get_object_or_404(Team, pk=pk)
            milestone = get_object_or_404(Milestone, pk=milestone_id, team=team)
            
            # JSON 데이터 파싱
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            # 업데이트할 필드들 처리
            updated_fields = []
            
            if 'startdate' in data:
                try:
                    milestone.startdate = datetime.strptime(data['startdate'], '%Y-%m-%d').date()
                    updated_fields.append('시작일')
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': '시작일 형식이 올바르지 않습니다. (YYYY-MM-DD 형식 필요)'
                    }, status=400)
                
            if 'enddate' in data:
                try:
                    milestone.enddate = datetime.strptime(data['enddate'], '%Y-%m-%d').date()
                    updated_fields.append('종료일')
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': '종료일 형식이 올바르지 않습니다. (YYYY-MM-DD 형식 필요)'
                    }, status=400)
                
            if 'progress_percentage' in data:
                progress = int(data['progress_percentage'])
                if 0 <= progress <= 100:
                    milestone.progress_percentage = progress
                    updated_fields.append('진행률')
                    
                    # 진행률이 100%이면 완료 처리
                    if progress == 100 and not milestone.is_completed:
                        milestone.is_completed = True
                        milestone.completed_date = datetime.now()
                        updated_fields.append('완료 상태')
                    elif progress < 100 and milestone.is_completed:
                        milestone.is_completed = False
                        milestone.completed_date = None
                        updated_fields.append('완료 상태')
            
            # 데이터 검증
            if hasattr(milestone, 'startdate') and hasattr(milestone, 'enddate'):
                if milestone.startdate > milestone.enddate:
                    return JsonResponse({
                        'success': False,
                        'message': '시작일은 종료일보다 이전이어야 합니다.'
                    }, status=400)
            
            # 저장
            milestone.save()
            
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
                'message': f'잘못된 값입니다: {str(e)}'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'업데이트 중 오류가 발생했습니다: {str(e)}'
            }, status=500)


milestone_update_ajax = MilestoneUpdateAjaxView.as_view()


class MilestoneDeleteAjaxView(TeamMemberRequiredMixin, View):
    def post(self, request, pk, milestone_id):
        try:
            milestone = get_object_or_404(Milestone, pk=milestone_id, team_id=pk)
            milestone_title = milestone.title
            milestone.delete()
            
            messages.success(request, f'"{milestone_title}" 마일스톤이 삭제되었습니다.')
            return HttpResponse(status=200)
            
        except Exception as e:
            messages.error(request, f'마일스톤 삭제 중 오류가 발생했습니다: {str(e)}')
            return HttpResponse(status=500)


milestone_delete_ajax = MilestoneDeleteAjaxView.as_view()


class TeamDisbandView(TeamHostRequiredMixin, View):
    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        team_title = team.title
        team.delete()
        messages.success(request, f'"{team_title}" 팀이 성공적으로 해체되었습니다.')
        return redirect('teams:main_page')


team_disband = TeamDisbandView.as_view()
