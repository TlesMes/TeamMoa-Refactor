from django.db import models
from datetime import timedelta

# Create your models here.

class PersonalDaySchedule(models.Model):
    """개인별 날짜별 가능한 시간대 저장"""
    date = models.DateField()
    owner = models.ForeignKey('teams.TeamUser', on_delete=models.CASCADE)
    available_hours = models.JSONField(default=list)  # [0, 9, 14, 18] 형태로 가능한 시간 저장
    
    class Meta:
        unique_together = ['date', 'owner']  # 같은 날짜에 중복 스케줄 방지
    
    def __str__(self):
        return f"{self.owner.user.nickname} - {self.date}"
    
    
    def is_available_at(self, hour):
        """특정 시간에 가능한지 확인"""
        return hour in self.available_hours


