from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.


class Team(models.Model):

    title = models.CharField(max_length=64)
    maxuser = models.PositiveIntegerField()
    currentuser = models.PositiveIntegerField()
    
    members = models.ManyToManyField('accounts.User', related_name='joined_teams', through="TeamUser")
    host = models.ForeignKey('accounts.User', on_delete=models.CASCADE) #호스트 유저 지정 
    
    # milestone은 별도 Milestone 모델로 관리됨

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
            return TeamUser.objects.filter(team=self).count()
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

class TeamUser(models.Model):
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)

    def __str__(self):  # admin에서 표시될 user 필드 정보 설정
        return self.user.nickname

class Milestone(models.Model):
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    startdate = models.DateField()
    enddate = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.IntegerField(default=0)
    priority = models.CharField(max_length=20, choices=[
        ('critical', '최우선'),
        ('high', '중요'), 
        ('medium', '보통'),
        ('low', '낮음'),
        ('minimal', '미미')
    ], default='medium')

    class Meta:
        ordering = ['-priority', 'enddate']

    def __str__(self):
        return self.title
    
    def get_status(self, today_date=None):
        """마일스톤의 현재 상태를 반환 (날짜 + 진행률 기준)"""
        if today_date is None:
            from datetime import date
            today_date = date.today()
        
        # 100% 완료된 경우
        if self.progress_percentage >= 100:
            return 'completed'
        
        # 아직 시작 전
        if today_date < self.startdate:
            return 'not_started'
        
        # 종료일이 지났지만 100% 미완료
        if today_date > self.enddate:
            return 'overdue'
        
        # 진행 기간 내에 있고 진행 중
        return 'in_progress'
    
    @property
    def status_display(self):
        """상태를 한국어로 표시"""
        status = self.get_status()
        status_map = {
            'not_started': '시작 전',
            'in_progress': '진행 중',
            'completed': '완료됨',
            'overdue': '지연됨'
        }
        return status_map.get(status, '알 수 없음')