from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.


class Team(models.Model):

    title = models.CharField(max_length=64)
    maxuser = models.PositiveIntegerField()
    currentuser = models.PositiveIntegerField()
    
    members = models.ManyToManyField('accounts.User', related_name='joined_teams', through = "Team_User")
    host = models.ForeignKey('accounts.User', on_delete=models.CASCADE) #호스트 유저 지정 
    
    dev_phase = models.DateTimeField

    invitecode = models.CharField(max_length=16)
    teampasswd = models.TextField()
    introduction = models.TextField()
    #스케줄 - TeamSchedule 모델 쪽에서 Foreignkey
    #마인드맵
    #게시판
    #파일 업로드
    
    def get_current_member_count(self):
        """현재 팀의 실제 팀원 수를 반환"""
        if self.pk:
            return Team_User.objects.filter(Team=self).count()
        return 0
    
    def clean(self):
        """모델 검증 로직"""
        super().clean()
        
        # 기존 팀 수정 시에만 검증 (새 팀 생성 시에는 검증하지 않음)
        if self.pk:
            current_member_count = self.get_current_member_count()
            
            if self.maxuser < current_member_count:
                raise ValidationError({
                    'maxuser': f'최대 인원수는 현재 팀원 수({current_member_count}명)보다 적을 수 없습니다.'
                })
    
    def save(self, *args, **kwargs):
        """저장 전 검증 실행"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class Team_User(models.Model):
    Team = models.ForeignKey('Team',on_delete = models.CASCADE)
    User = models.ForeignKey('accounts.User',on_delete = models.CASCADE)

    Todo = models.TextField(null=True, blank=True) # todolist 모델을 새로 만들어서 연결할 듯
    # schedule = models.ForeignKey('schedules.WeekSchedule',on_delete = models.CASCADE) #유저-팀간의 스케줄, 스케줄 쪽에서 foreignkey로 갖고 있음

    def __str__(self):  # admin에서 표시될 user 필드 정보 설정
        return self.User.nickname

class DevPhase(models.Model):
    team = models.ForeignKey('Team',on_delete = models.CASCADE)
    content = models.TextField()
    startdate = models.DateField()
    enddate = models.DateField()

    def __str__(self):
        return self.content