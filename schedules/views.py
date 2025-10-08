from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from teams.models import Team, TeamUser
from .models import PersonalDaySchedule
from .services import ScheduleService
from datetime import datetime, date, timedelta
from django.utils.dateparse import parse_datetime
from common.mixins import TeamMemberRequiredMixin


class SchedulerPageView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'schedules/scheduler_page.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schedule_service = ScheduleService()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = get_object_or_404(Team, pk=self.kwargs['pk'])

        # 현재 주차를 기본값으로 설정 (ISO 8601 형식: YYYY-Www)
        today = date.today()
        iso_calendar = today.isocalendar()
        current_week = f"{iso_calendar[0]}-W{iso_calendar[1]:02d}"
        context['selected_week'] = current_week

        return context
    
    def post(self, request, *args, **kwargs):
        team = get_object_or_404(Team, pk=kwargs['pk'])
        week = request.POST.get("week")
        
        try:
            if not week:
                raise ValueError(self.schedule_service.ERROR_MESSAGES['INVALID_WEEK'])
            
            date_mon = date.fromisoformat(week)
            date_sun = date_mon + timedelta(days=6)
            
            # 서비스를 통한 팀 가용성 계산
            team_availability = self.schedule_service.get_team_availability(team, date_mon, date_sun)

            return self.render_to_response({
                'schedules': team_availability,
                'team': team,
                'selected_week': week
            })
        except ValueError as e:
            messages.error(request, str(e))
            return self.render_to_response({'team': team})


scheduler_page = SchedulerPageView.as_view()
        



class SchedulerUploadPageView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'schedules/scheduler_upload_page.html'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schedule_service = ScheduleService()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = get_object_or_404(Team, pk=self.kwargs['pk'])
        return context
    
    def post(self, request, *args, **kwargs):
        team = get_object_or_404(Team, pk=kwargs['pk'])
        
        try:
            # TeamMemberRequiredMixin에서 이미 멤버십 검증됨
            teamuser = get_object_or_404(TeamUser, team=team, user=request.user)
            
            week = request.POST.get("week")
            if not week:
                raise ValueError(self.schedule_service.ERROR_MESSAGES['INVALID_WEEK'])

            week_start = date.fromisoformat(week)
            
            # 서비스를 통한 스케줄 저장
            updated_days = self.schedule_service.save_personal_schedule(
                teamuser, week_start, request.POST
            )
            
            if updated_days > 0:
                messages.success(request, '주간 스케줄이 성공적으로 업로드되었습니다.')
            else:
                messages.info(request, '등록된 가능 시간이 없습니다.')
            
            return redirect('schedules:scheduler_page', pk=team.pk)
            
        except ValueError as e:
            messages.error(request, str(e))
            if 'team_user_not_found' in str(e).lower():
                return redirect('teams:team_main_page', pk=team.pk)
            return self.render_to_response({'team': team})


scheduler_upload_page = SchedulerUploadPageView.as_view()