from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.


class Team(models.Model):

    title = models.CharField(max_length=64)
    maxuser = models.PositiveIntegerField()
    currentuser = models.PositiveIntegerField()
    
    members = models.ManyToManyField('accounts.User', related_name='joined_teams', through="TeamUser")
    host = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_teams',
        help_text='팀 호스트 (탈퇴 시 NULL, 자동 승계 처리)'
    ) 
    
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
    progress_mode = models.CharField(
        max_length=20,
        choices=[
            ('manual', '수동 입력'),
            ('auto', 'TODO 기반 자동 계산')
        ],
        default='auto',
        help_text='진행률 관리 방식: 수동 입력 또는 TODO 기반 자동 계산'
    )
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

    def calculate_progress_from_todos(self):
        """연결된 TODO들의 완료율을 계산하여 진행률 반환 (0-100)"""
        from django.db.models import Count, Q

        stats = self.todos.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(is_completed=True))
        )

        total = stats['total']
        if total == 0:
            return 0

        completed = stats['completed']
        return int((completed / total) * 100)

    def update_progress_from_todos(self):
        """
        AUTO 모드일 때 TODO 완료율로 진행률 갱신
        Returns: (old_progress, new_progress) or (None, None) if not AUTO mode
        """
        if self.progress_mode != 'auto':
            return None, None

        from django.utils import timezone

        old_progress = self.progress_percentage
        new_progress = self.calculate_progress_from_todos()

        self.progress_percentage = new_progress

        # 100% 도달 시 자동 완료
        if new_progress == 100 and not self.is_completed:
            self.is_completed = True
            self.completed_date = timezone.now()
        # 100% 미만으로 떨어지면 완료 상태 해제
        elif new_progress < 100 and self.is_completed:
            self.is_completed = False
            self.completed_date = None

        self.save()
        return old_progress, new_progress

    def get_todo_stats(self):
        """마일스톤에 연결된 TODO 통계 반환"""
        from django.db.models import Count, Q

        stats = self.todos.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(is_completed=True)),
            in_progress=Count('id', filter=Q(is_completed=False))
        )

        return {
            'total': stats['total'],
            'completed': stats['completed'],
            'in_progress': stats['in_progress'],
            'completion_rate': self.calculate_progress_from_todos()
        }

    def switch_progress_mode(self, new_mode):
        """
        진행률 모드 전환
        - manual → auto: TODO 기반으로 즉시 재계산
        - auto → manual: 기존 진행률 유지
        """
        if new_mode not in ['manual', 'auto']:
            raise ValueError(f"Invalid progress_mode: {new_mode}")

        old_mode = self.progress_mode

        if old_mode == new_mode:
            return  # 변경 없음

        self.progress_mode = new_mode

        # manual → auto: 즉시 재계산
        if new_mode == 'auto':
            old_progress, new_progress = self.update_progress_from_todos()
            self.save()
            return old_progress, new_progress

        # auto → manual: 기존 진행률 유지
        self.save()
        return None, None