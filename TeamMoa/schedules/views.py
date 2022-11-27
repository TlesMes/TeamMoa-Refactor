from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from teams.models import Team, Team_User
from .models import DaySchedule
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


def upload_scheduler(request, pk):
    pass
    
