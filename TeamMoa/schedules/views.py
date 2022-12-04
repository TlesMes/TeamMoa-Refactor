from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from schedules.forms import ScheduleForm
from teams.models import Team, Team_User
from .models import PersonalDaySchedule, TeamDaySchedule
from datetime import datetime, date, timedelta
from django.utils.dateparse import parse_datetime
import logging
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
    if request.method =='POST':
        week=request.POST["week"]

        date_mon = date.fromisoformat(week)
        date_sun = date_mon + timedelta(days=6)
        logger = logging.getLogger('test')
        logger.error(date_sun)
        
        teamSchedules = TeamDaySchedule.objects.filter(team=team, date__range=[date_mon,date_sun]).order_by('date')
        if teamSchedules.exists():
            return render(request, 'schedules/scheduler_page.html', {'schedules':teamSchedules,'team':team})
        else:
            message = '해당 날짜는 스케줄 X'
            return render(request, 'schedules/scheduler_page.html', {'message':message,'team':team})
    else:
        return render(request, 'schedules/scheduler_page.html',{'team':team})
        



def scheduler_upload_page(request, pk):
    user = request.user
    team = get_object_or_404(Team, pk=pk)
    teamuser = Team_User.objects.get(Team=team,User=user)
    if request.method =='POST':
        form = ScheduleForm(request.POST)           #체크한 구간으로 Schedule 객체를 하나 만듦
        if form.is_valid():
            existSchedule=PersonalDaySchedule.objects.filter(owner=teamuser, date=form.cleaned_data['date'])

            if (existSchedule.exists()): #해당 유저, 날짜의 시간표가 이미 등록되어 있을 때
                existSchedule=PersonalDaySchedule.objects.get(owner=teamuser, date=form.cleaned_data['date'])
                existTeamSchedule = TeamDaySchedule.objects.get(team=team, date=form.cleaned_data['date'])
                # remove_scheduler(existTeamSchedule,existSchedule) #해당 유저로 등록되어 있던 가용인원을 일단 없앰
                if existSchedule.time_0:
                    existTeamSchedule.time_0 -= 1
                if existSchedule.time_1:
                    existTeamSchedule.time_1 -= 1
                if existSchedule.time_2:
                    existTeamSchedule.time_2 -= 1
                if existSchedule.time_3:
                    existTeamSchedule.time_3 -= 1
                if existSchedule.time_4:
                    existTeamSchedule.time_4 -= 1
                if existSchedule.time_5:
                    existTeamSchedule.time_5 -= 1
                if existSchedule.time_6:
                    existTeamSchedule.time_6 -= 1
                if existSchedule.time_7:
                    existTeamSchedule.time_7 -= 1
                if existSchedule.time_8:
                    existTeamSchedule.time_8 -= 1
                if existSchedule.time_9:
                    existTeamSchedule.time_9 -= 1
                if existSchedule.time_10:
                    existTeamSchedule.time_10 -= 1
                if existSchedule.time_11:
                    existTeamSchedule.time_11 -= 1
                if existSchedule.time_12:
                    existTeamSchedule.time_12 -= 1
                if existSchedule.time_13:
                    existTeamSchedule.time_13 -= 1
                if existSchedule.time_14:
                    existTeamSchedule.time_14 -= 1
                if existSchedule.time_15:
                    existTeamSchedule.time_15 -= 1
                if existSchedule.time_16:
                    existTeamSchedule.time_16 -= 1
                if existSchedule.time_17:
                    existTeamSchedule.time_17 -= 1
                if existSchedule.time_18:
                    existTeamSchedule.time_18 -= 1
                if existSchedule.time_19:
                    existTeamSchedule.time_19 -= 1
                if existSchedule.time_20:
                    existTeamSchedule.time_20 -= 1
                if existSchedule.time_21:
                    existTeamSchedule.time_21 -= 1
                if existSchedule.time_22:
                    existTeamSchedule.time_22 -= 1
                if existSchedule.time_23:
                    existTeamSchedule.time_23 -= 1
                existTeamSchedule.save()
                existSchedule.delete()

            userSchedule = PersonalDaySchedule()        
            userSchedule.time_0 = form.cleaned_data['time_0']
            userSchedule.time_1 = form.cleaned_data['time_1']
            userSchedule.time_2 = form.cleaned_data['time_2']
            userSchedule.time_3 = form.cleaned_data['time_3']
            userSchedule.time_4 = form.cleaned_data['time_4']
            userSchedule.time_5 = form.cleaned_data['time_5']
            userSchedule.time_6 = form.cleaned_data['time_6']
            userSchedule.time_7 = form.cleaned_data['time_7']
            userSchedule.time_8 = form.cleaned_data['time_8']
            userSchedule.time_9 = form.cleaned_data['time_9']
            userSchedule.time_10 = form.cleaned_data['time_10']
            userSchedule.time_11 = form.cleaned_data['time_11']
            userSchedule.time_12 = form.cleaned_data['time_12']
            userSchedule.time_13 = form.cleaned_data['time_13']
            userSchedule.time_14 = form.cleaned_data['time_14']
            userSchedule.time_15 = form.cleaned_data['time_15']
            userSchedule.time_16 = form.cleaned_data['time_16']
            userSchedule.time_17 = form.cleaned_data['time_17']
            userSchedule.time_18 = form.cleaned_data['time_18']
            userSchedule.time_19 = form.cleaned_data['time_19']
            userSchedule.time_20 = form.cleaned_data['time_20']
            userSchedule.time_21 = form.cleaned_data['time_21']
            userSchedule.time_22 = form.cleaned_data['time_22']
            userSchedule.time_23 = form.cleaned_data['time_23']
            userSchedule.owner = teamuser
            userSchedule.date = form.cleaned_data['date']
            userSchedule.save()
            
            existTeamSchedule = TeamDaySchedule.objects.filter(team=team, date=form.cleaned_data['date'])
            if existTeamSchedule.exists():
                existTeamSchedule = TeamDaySchedule.objects.get(team=team, date=form.cleaned_data['date'])
                #if로 1씩 더하기
                if userSchedule.time_0:
                    existTeamSchedule.time_0 += 1
                if userSchedule.time_1:
                    existTeamSchedule.time_1 += 1
                if userSchedule.time_2:
                    existTeamSchedule.time_2 += 1
                if userSchedule.time_3:
                    existTeamSchedule.time_3 += 1
                if userSchedule.time_4:
                    existTeamSchedule.time_4 += 1
                if userSchedule.time_5:
                    existTeamSchedule.time_5 += 1
                if userSchedule.time_6:
                    existTeamSchedule.time_6 += 1
                if userSchedule.time_7:
                    existTeamSchedule.time_7 += 1
                if userSchedule.time_8:
                    existTeamSchedule.time_8 += 1
                if userSchedule.time_9:
                    existTeamSchedule.time_9 += 1
                if userSchedule.time_10:
                    existTeamSchedule.time_10 += 1
                if userSchedule.time_11:
                    existTeamSchedule.time_11 += 1
                if userSchedule.time_12:
                    existTeamSchedule.time_12 += 1
                if userSchedule.time_13:
                    existTeamSchedule.time_13 += 1
                if userSchedule.time_14:
                    existTeamSchedule.time_14 += 1
                if userSchedule.time_15:
                    existTeamSchedule.time_15 += 1
                if userSchedule.time_16:
                    existTeamSchedule.time_16 += 1
                if userSchedule.time_17:
                    existTeamSchedule.time_17 += 1
                if userSchedule.time_18:
                    existTeamSchedule.time_18 += 1
                if userSchedule.time_19:
                    existTeamSchedule.time_19 += 1
                if userSchedule.time_20:
                    existTeamSchedule.time_20 += 1
                if userSchedule.time_21:
                    existTeamSchedule.time_21 += 1
                if userSchedule.time_22:
                    existTeamSchedule.time_22 += 1
                if userSchedule.time_23:
                    existTeamSchedule.time_23 += 1
                existTeamSchedule.save()
            else:
                teamSchedule = TeamDaySchedule() #해당 날짜의 팀 스케줄을 만들어서 추가
                if userSchedule.time_0:
                    teamSchedule.time_0 += 1
                if userSchedule.time_1:
                    teamSchedule.time_1 += 1
                if userSchedule.time_2:
                    teamSchedule.time_2 += 1
                if userSchedule.time_3:
                    teamSchedule.time_3 += 1
                if userSchedule.time_4:
                    teamSchedule.time_4 += 1
                if userSchedule.time_5:
                    teamSchedule.time_5 += 1
                if userSchedule.time_6:
                    teamSchedule.time_6 += 1
                if userSchedule.time_7:
                    teamSchedule.time_7 += 1
                if userSchedule.time_8:
                    teamSchedule.time_8 += 1
                if userSchedule.time_9:
                    teamSchedule.time_9 += 1
                if userSchedule.time_10:
                    teamSchedule.time_10 += 1
                if userSchedule.time_11:
                    teamSchedule.time_11 += 1
                if userSchedule.time_12:
                    teamSchedule.time_12 += 1
                if userSchedule.time_13:
                    teamSchedule.time_13 += 1
                if userSchedule.time_14:
                    teamSchedule.time_14 += 1
                if userSchedule.time_15:
                    teamSchedule.time_15 += 1
                if userSchedule.time_16:
                    teamSchedule.time_16 += 1
                if userSchedule.time_17:
                    teamSchedule.time_17 += 1
                if userSchedule.time_18:
                    teamSchedule.time_18 += 1
                if userSchedule.time_19:
                    teamSchedule.time_19 += 1
                if userSchedule.time_20:
                    teamSchedule.time_20 += 1
                if userSchedule.time_21:
                    teamSchedule.time_21 += 1
                if userSchedule.time_22:
                    teamSchedule.time_22 += 1
                if userSchedule.time_23:
                    teamSchedule.time_23 += 1
                teamSchedule.team = team
                teamSchedule.date = userSchedule.date
                teamSchedule.save()
        return redirect(f'/schedules/scheduler_page/{pk}')
        #return render(request, 'schedules/scheduler_page.html', {'team':team})
    form = ScheduleForm()
    return render(request, 'schedules/scheduler_upload_page.html', {'form':form})


        



def upload_scheduler(request, pk):
    pass
    

def remove_scheduler(existTeamSchedule,existSchedule):
    pass

def synthesize_scheduler(team, schedule):
    pass