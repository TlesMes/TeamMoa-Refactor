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
        'NO_PERMISSION': '권한이 없습니다.',
        'TEAM_USER_NOT_FOUND': '팀 멤버 정보를 찾을 수 없습니다.',
        'INVALID_SCHEDULE_DATA': '잘못된 스케줄 데이터입니다.',
    }
    
    def save_personal_schedule(self, team_user, week_start, schedule_data):
        """개인 주간 스케줄을 저장합니다."""
        if not isinstance(week_start, date):
            raise ValueError(self.ERROR_MESSAGES['INVALID_DATE'])
        
        if not self.can_edit_schedule(team_user.user, team_user.team):
            raise ValueError(self.ERROR_MESSAGES['NO_PERMISSION'])
        
        return self._bulk_process_weekly_schedule(team_user, week_start, schedule_data)
    
    def get_personal_schedule(self, team_user, start_date, end_date):
        """개인 스케줄을 조회합니다. (미사용)"""
        return PersonalDaySchedule.objects.filter(
            owner=team_user,
            date__range=[start_date, end_date]
        ).order_by('date')
    
    def delete_personal_schedule(self, team_user, target_date):
        """특정 날짜의 개인 스케줄을 삭제합니다. (미사용)"""
        if not self.can_edit_schedule(team_user.user, team_user.team):
            raise ValueError(self.ERROR_MESSAGES['NO_PERMISSION'])
        
        deleted_count, _ = PersonalDaySchedule.objects.filter(
            owner=team_user,
            date=target_date
        ).delete()
        
        return deleted_count > 0
    
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
    
    def get_team_schedule_summary(self, team, week_start):
        """팀의 주간 스케줄 요약을 반환합니다. (미사용)"""
        week_end = week_start + timedelta(days=6)
        availability = self.get_team_availability(team, week_start, week_end)
        
        # 요약 통계 계산
        total_members = team.teamuser_set.count()
        peak_availability = 0
        best_time_slot = None
        
        for day_data in availability:
            for hour, count in day_data['availability'].items():
                if count > peak_availability:
                    peak_availability = count
                    best_time_slot = {
                        'date': day_data['date'],
                        'hour': hour,
                        'available_count': count,
                        'availability_rate': (count / total_members * 100) if total_members > 0 else 0
                    }
        
        return {
            'availability_data': availability,
            'summary': {
                'total_members': total_members,
                'peak_availability': peak_availability,
                'best_time_slot': best_time_slot,
                'week_range': f"{week_start} ~ {week_end}"
            }
        }
    
    def validate_schedule_data(self, schedule_data):
        """스케줄 데이터의 유효성을 검증합니다. (미사용)"""
        if not isinstance(schedule_data, dict):
            return False
        
        # 기본적인 검증 로직
        for day_offset in range(7):
            for hour in range(24):
                checkbox_name = f'time_{hour}-{day_offset + 1}'
                if checkbox_name in schedule_data:
                    # 체크박스 값이 유효한지 확인
                    if schedule_data[checkbox_name] not in ['on', True, '1']:
                        continue
        
        return True
    
    def can_edit_schedule(self, user, team):
        """사용자가 해당 팀의 스케줄을 편집할 수 있는지 확인합니다."""
        try:
            TeamUser.objects.get(team=team, user=user)
            return True
        except TeamUser.DoesNotExist:
            return False
    
    def get_team_user_or_error(self, user, team):
        """팀 사용자 객체를 가져오거나 에러를 발생시킵니다."""
        try:
            return TeamUser.objects.get(team=team, user=user)
        except TeamUser.DoesNotExist:
            raise ValueError(self.ERROR_MESSAGES['TEAM_USER_NOT_FOUND'])
    
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