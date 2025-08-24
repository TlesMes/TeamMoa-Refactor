from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from teams.models import Team, TeamUser
from .models import PersonalDaySchedule
from datetime import datetime, date, timedelta
from django.utils.dateparse import parse_datetime
from common.mixins import TeamMemberRequiredMixin


class SchedulerPageView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'schedules/scheduler_page.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = get_object_or_404(Team, pk=self.kwargs['pk'])
        return context
    
    def post(self, request, *args, **kwargs):
        team = get_object_or_404(Team, pk=kwargs['pk'])
        week = request.POST.get("week")
        
        if not week:
            messages.error(request, '주간을 선택해주세요.')
            return self.render_to_response({'team': team})
        
        try:
            date_mon = date.fromisoformat(week)
            date_sun = date_mon + timedelta(days=6)
            
            # 실시간 집계로 팀 가용성 계산
            team_availability = PersonalDaySchedule.get_team_availability(team, date_mon, date_sun)
            
            return self.render_to_response({
                'schedules': team_availability,
                'team': team,
                'selected_week': week
            })
        except ValueError:
            messages.error(request, '유효하지 않은 날짜 형식입니다.')
            return self.render_to_response({'team': team})


scheduler_page = SchedulerPageView.as_view()
        



class SchedulerUploadPageView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'schedules/scheduler_upload_page.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = get_object_or_404(Team, pk=self.kwargs['pk'])
        return context
    
    def post(self, request, *args, **kwargs):
        team = get_object_or_404(Team, pk=kwargs['pk'])
        
        try:
            teamuser = TeamUser.objects.get(team=team, user=request.user)
        except TeamUser.DoesNotExist:
            messages.error(request, '팀 멤버 정보를 찾을 수 없습니다.')
            return redirect('teams:team_main_page', pk=team.pk)
        
        week = request.POST.get("week")
        if not week:
            messages.error(request, '주간을 선택해주세요.')
            return self.render_to_response({'team': team})
        
        try:
            week_start = date.fromisoformat(week)
        except ValueError:
            messages.error(request, '유효하지 않은 날짜 형식입니다.')
            return self.render_to_response({'team': team})
        
        # 7일간 스케줄 처리
        updated_days = 0
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            
            # 기존 스케줄 삭제 (중복 방지)
            PersonalDaySchedule.objects.filter(
                owner=teamuser,
                date=current_date
            ).delete()
            
            # 새 스케줄 생성
            available_hours = []
            for hour in range(24):
                checkbox_name = f'time_{hour}-{day_offset + 1}'
                if request.POST.get(checkbox_name):
                    available_hours.append(hour)
            
            # 가능한 시간이 있을 때만 저장
            if available_hours:
                PersonalDaySchedule.objects.create(
                    owner=teamuser,
                    date=current_date,
                    available_hours=available_hours
                )
                updated_days += 1
        
        if updated_days > 0:
            messages.success(request, f'{updated_days}일의 스케줄이 성공적으로 등록되었습니다.')
        else:
            messages.info(request, '등록된 가능 시간이 없습니다.')
        
        return redirect('schedules:scheduler_page', pk=team.pk)


scheduler_upload_page = SchedulerUploadPageView.as_view()