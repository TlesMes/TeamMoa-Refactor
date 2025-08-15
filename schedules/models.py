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
    
    @classmethod
    def get_team_availability(cls, team, start_date, end_date):
        """팀의 주간 가용성 실시간 계산 (SQLite 호환)"""
        # 전체 기간의 스케줄을 한 번에 가져오기 (성능 최적화)
        schedules = cls.objects.filter(
            owner__team=team, 
            date__range=[start_date, end_date]
        ).select_related('owner')
        
        # 날짜별로 그룹화
        schedules_by_date = {}
        for schedule in schedules:
            if schedule.date not in schedules_by_date:
                schedules_by_date[schedule.date] = []
            schedules_by_date[schedule.date].append(schedule)
        
        # 결과 생성
        result = []
        current_date = start_date
        while current_date <= end_date:
            day_schedules = schedules_by_date.get(current_date, [])
            day_availability = {}
            
            for hour in range(24):
                # SQLite 호환: Python에서 직접 처리
                count = sum(1 for schedule in day_schedules 
                           if hour in schedule.available_hours)
                day_availability[hour] = count
                
            result.append({
                'date': current_date,
                'availability': day_availability
            })
            current_date += timedelta(days=1)
            
        return result
    
    def is_available_at(self, hour):
        """특정 시간에 가능한지 확인"""
        return hour in self.available_hours


