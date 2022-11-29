from django.db import models

# Create your models here.


class Team(models.Model):

    title = models.CharField(max_length=64)
    maxuser = models.PositiveIntegerField()
    currentuser = models.PositiveIntegerField()
    
    members = models.ManyToManyField('accounts.User', related_name='joined_teams', through = "Team_User")
    host = models.ForeignKey('accounts.User', on_delete=models.CASCADE) #호스트 유저 지정 
    
    invitecode = models.CharField(max_length=16)
    teampasswd = models.TextField()
    introduction = models.TextField()
    #스케줄 - TeamSchedule 모델 쪽에서 Foreignkey
    #마인드맵
    #게시판
    #파일 업로드
    def __str__(self): #어드민 페이지에서 username으로 표시
        return self.title

class Team_User(models.Model):
    Team = models.ForeignKey('Team',on_delete = models.CASCADE)
    User = models.ForeignKey('accounts.User',on_delete = models.CASCADE)

    Todo = models.TextField(null=True, blank=True) # todolist 모델을 새로 만들어서 연결할 듯
    # schedule = models.ForeignKey('schedules.WeekSchedule',on_delete = models.CASCADE) #유저-팀간의 스케줄, 스케줄 쪽에서 foreignkey로 갖고 있음

    def __str__(self):  # admin에서 표시될 user 필드 정보 설정
        return self.User.nickname
