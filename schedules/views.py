from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from teams.models import Team, Team_User
from .models import PersonalDaySchedule, TeamDaySchedule
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
    if request.method =='POST':
        week=request.POST["week"]

        date_mon = date.fromisoformat(week)
        date_sun = date_mon + timedelta(days=6)

        
        teamSchedules = TeamDaySchedule.objects.filter(team=team, date__range=[date_mon,date_sun]).order_by('date')
        if teamSchedules.exists():
            return render(request, 'schedules/scheduler_page.html', {'schedules':teamSchedules,'team':team})
        else:
            for i in range(7):
                teamSchedule = TeamDaySchedule()
                teamSchedule.date = date_mon + timedelta(days=i)
                teamSchedule.team = team
                teamSchedule.save()
            teamSchedules = TeamDaySchedule.objects.filter(team=team, date__range=[date_mon,date_sun]).order_by('date')
            return render(request, 'schedules/scheduler_page.html', {'schedules':teamSchedules,'team':team})
    else:
        return render(request, 'schedules/scheduler_page.html',{'team':team})
        



def scheduler_upload_page(request, pk):
    user = request.user
    team = get_object_or_404(Team, pk=pk)
    teamuser = Team_User.objects.get(Team=team,User=user)
    if request.method =='POST':
        week=request.POST["week"]
        week_day = date.fromisoformat(week)
        identifier = 1
        for form in range(7):
            existSchedule=PersonalDaySchedule.objects.filter(owner=teamuser, date=week_day)

            if (existSchedule.exists()): #해당 유저, 날짜의 시간표가 이미 등록되어 있을 때
                existSchedule = PersonalDaySchedule.objects.get(owner=teamuser, date=week_day)
                existTeamSchedule = TeamDaySchedule.objects.get(team=team, date=week_day)
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

            request.POST.get('time_0'+f'-{identifier}')
            userSchedule = PersonalDaySchedule()    
            userSchedule.time_0 = False if request.POST.get('time_0'+f'-{identifier}') == None else True
            userSchedule.time_1 = False if request.POST.get('time_1'+f'-{identifier}') == None else True
            userSchedule.time_2 = False if request.POST.get('time_2'+f'-{identifier}') == None else True
            userSchedule.time_3 = False if request.POST.get('time_3'+f'-{identifier}') == None else True
            userSchedule.time_4 = False if request.POST.get('time_4'+f'-{identifier}') == None else True
            userSchedule.time_5 = False if request.POST.get('time_5'+f'-{identifier}') == None else True
            userSchedule.time_6 = False if request.POST.get('time_6'+f'-{identifier}') == None else True
            userSchedule.time_7 = False if request.POST.get('time_7'+f'-{identifier}') == None else True
            userSchedule.time_8 = False if request.POST.get('time_8'+f'-{identifier}') == None else True
            userSchedule.time_9 = False if request.POST.get('time_9'+f'-{identifier}') == None else True
            userSchedule.time_10 = False if request.POST.get('time_10'+f'-{identifier}') == None else True
            userSchedule.time_11 = False if request.POST.get('time_11'+f'-{identifier}') == None else True
            userSchedule.time_12 = False if request.POST.get('time_12'+f'-{identifier}') == None else True
            userSchedule.time_13 = False if request.POST.get('time_13'+f'-{identifier}') == None else True
            userSchedule.time_14 = False if request.POST.get('time_14'+f'-{identifier}') == None else True
            userSchedule.time_15 = False if request.POST.get('time_15'+f'-{identifier}') == None else True
            userSchedule.time_16 = False if request.POST.get('time_16'+f'-{identifier}') == None else True
            userSchedule.time_17 = False if request.POST.get('time_17'+f'-{identifier}') == None else True
            userSchedule.time_18 = False if request.POST.get('time_18'+f'-{identifier}') == None else True
            userSchedule.time_19 = False if request.POST.get('time_19'+f'-{identifier}') == None else True
            userSchedule.time_20 = False if request.POST.get('time_20'+f'-{identifier}') == None else True
            userSchedule.time_21 = False if request.POST.get('time_21'+f'-{identifier}') == None else True
            userSchedule.time_22 = False if request.POST.get('time_22'+f'-{identifier}') == None else True
            userSchedule.time_23 = False if request.POST.get('time_23'+f'-{identifier}') == None else True
            userSchedule.owner = teamuser
            userSchedule.date = week_day
            userSchedule.save()
            identifier = identifier + 1
            
            existTeamSchedule = TeamDaySchedule.objects.filter(team=team, date=week_day)
            if existTeamSchedule.exists():
                existTeamSchedule = TeamDaySchedule.objects.get(team=team, date=week_day)
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
            week_day = week_day + timedelta(days=1)

        return redirect(f'/schedules/scheduler_page/{pk}')
        #return render(request, 'schedules/scheduler_page.html', {'team':team})

    return render(request, 'schedules/scheduler_upload_page.html', {'team':team})


        



def upload_scheduler(request, pk):
    pass
    

def remove_scheduler(existTeamSchedule,existSchedule):
    pass

def synthesize_scheduler(team, schedule):
    pass