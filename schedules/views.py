from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from teams.models import Team, TeamUser
from .models import PersonalDaySchedule
from datetime import datetime, date, timedelta
from django.utils.dateparse import parse_datetime
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

def scheduler_page(request, pk):
    user = request.user
    team = get_object_or_404(Team, pk=pk)
    
    if request.method == 'POST':
        week = request.POST["week"]
        date_mon = date.fromisoformat(week)
        date_sun = date_mon + timedelta(days=6)
        
        # 실시간 집계로 팀 가용성 계산
        team_availability = PersonalDaySchedule.get_team_availability(team, date_mon, date_sun)
        
        return render(request, 'schedules/scheduler_page.html', {
            'schedules': team_availability,
            'team': team, 
            'selected_week': week
        })
    else:
        return render(request, 'schedules/scheduler_page.html', {'team': team})
        



def scheduler_upload_page(request, pk):
    user = request.user
    team = get_object_or_404(Team, pk=pk)
    teamuser = TeamUser.objects.get(team=team, user=user)
    
    if request.method == 'POST':
        week = request.POST["week"]
        week_start = date.fromisoformat(week)
        
        # 7일간 스케줄 처리
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

        return redirect(f'/schedules/scheduler_page/{pk}')

    return render(request, 'schedules/scheduler_upload_page.html', {'team': team})