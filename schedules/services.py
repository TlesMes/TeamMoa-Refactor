from django.shortcuts import get_object_or_404
from django.db import transaction
from datetime import datetime, date, timedelta
from teams.models import Team, TeamUser
from .models import PersonalDaySchedule


class ScheduleService:
    """스케줄 관리를 위한 서비스 클래스"""
    
    ERROR_MESSAGES = {
        'INVALID_DATE': '유효하지 않은 날짜 형식입니다.',
        'INVALID_WEEK': '주간을 선택해주세요.',
    }
    
    def save_personal_schedule(self, team_user, week_start, schedule_data):
        """개인 주간 스케줄을 저장합니다."""
        if not isinstance(week_start, date):
            raise ValueError(self.ERROR_MESSAGES['INVALID_DATE'])
        
        # 팀 멤버십 검증은 TeamMemberRequiredMixin에서 이미 수행됨
        return self._bulk_process_weekly_schedule(team_user, week_start, schedule_data)
    
    
    def get_team_availability(self, team, start_date, end_date):
        """팀의 주간 가용성을 실시간 계산합니다. (기존 모델 메서드에서 이동)"""
        # 전체 기간의 스케줄을 한 번에 가져오기 (성능 최적화)
        schedules = PersonalDaySchedule.objects.filter(
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
    
    
    @transaction.atomic
    def _bulk_process_weekly_schedule(self, team_user, week_start, schedule_data):
        """주간 스케줄을 일괄 처리합니다."""
        updated_days = 0
        
        # 7일간 스케줄 처리
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            
            # 기존 스케줄 삭제 (중복 방지)
            PersonalDaySchedule.objects.filter(
                owner=team_user,
                date=current_date
            ).delete()
            
            # 새 스케줄 생성
            available_hours = []
            for hour in range(24):
                checkbox_name = f'time_{hour}-{day_offset + 1}'
                if schedule_data.get(checkbox_name):
                    available_hours.append(hour)
            
            # 가능한 시간이 있을 때만 저장
            if available_hours:
                PersonalDaySchedule.objects.create(
                    owner=team_user,
                    date=current_date,
                    available_hours=available_hours
                )
                updated_days += 1
        
        return updated_days