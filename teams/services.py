import uuid
import base64
import codecs
from datetime import datetime, date
from django.db import transaction
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from .models import Team, TeamUser, Milestone


class TeamServiceException(Exception):
    """팀 서비스 레이어 기본 예외"""
    pass


class TeamService:
    """팀 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    ERROR_MESSAGES = {
        'INVALID_PASSWORD': '팀 비밀번호가 올바르지 않습니다.',
        'ALREADY_MEMBER': '이미 가입된 팀입니다.',
        'TEAM_FULL': '팀 최대인원을 초과했습니다.',
        'TEAM_NOT_FOUND': '존재하지 않는 팀입니다.',
        'INVALID_CODE': '유효하지 않은 팀 코드입니다.'
    }
    
    @transaction.atomic
    def create_team(self, host_user, title, maxuser, teampasswd, introduction):
        """
        새 팀을 생성하고 호스트를 멤버로 추가합니다.
        
        Args:
            host_user: 팀 호스트가 될 사용자
            title: 팀 제목
            maxuser: 최대 인원수
            teampasswd: 팀 비밀번호
            introduction: 팀 소개
            
        Returns:
            Team: 생성된 팀 객체
            
        Raises:
            ValueError: 입력값 검증 실패 시
        """
        # 입력값 검증
        self._validate_team_creation_data(title, maxuser, teampasswd)
        
        # 초대 코드 생성
        invite_code = self._generate_invite_code()
        
        # 팀 생성 (트랜잭션 보장)
        team = Team.objects.create(
            title=title,
            maxuser=maxuser,
            teampasswd=teampasswd,
            introduction=introduction,
            host=host_user,
            currentuser=1,
            invitecode=invite_code
        )
        
        # 호스트를 멤버로 추가
        TeamUser.objects.create(team=team, user=host_user)
        
        return team
    
    def verify_team_code(self, invite_code, user):
        """
        팀 코드를 검증하고 팀 정보를 반환합니다.
        
        Args:
            invite_code: 팀 초대 코드
            user: 검증하려는 사용자
            
        Returns:
            dict: 팀 정보
            
        Raises:
            ValueError: 검증 실패 시
        """
        if not invite_code:
            raise ValueError('팀 코드를 입력해주세요.')
        
        # 팀 조회
        try:
            team = Team.objects.get(invitecode=invite_code.strip())
        except Team.DoesNotExist:
            raise ValueError(self.ERROR_MESSAGES['INVALID_CODE'])
        
        # 중복 가입 체크
        if TeamUser.objects.filter(team=team, user=user).exists():
            raise ValueError(self.ERROR_MESSAGES['ALREADY_MEMBER'])
        
        # 인원 초과 체크
        current_member_count = team.get_current_member_count()
        if current_member_count >= team.maxuser:
            raise ValueError(self.ERROR_MESSAGES['TEAM_FULL'])
        
        return {
            'id': team.id,
            'title': team.title,
            'current_members': current_member_count,
            'maxuser': team.maxuser,
            'host_name': team.host.nickname if team.host.nickname else team.host.username,
            'introduction': team.introduction if team.introduction else None
        }
    
    @transaction.atomic
    def join_team(self, user, team_id, password):
        """
        팀에 가입 처리를 수행합니다.
        
        Args:
            user: 가입하려는 사용자
            team_id: 가입할 팀 ID
            password: 팀 비밀번호
            
        Returns:
            Team: 가입한 팀 객체
            
        Raises:
            ValueError: 가입 실패 시
        """
        if not team_id or not password:
            raise ValueError('필수 정보가 누락되었습니다.')
        
        # 팀 조회
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            raise ValueError(self.ERROR_MESSAGES['TEAM_NOT_FOUND'])
        
        # 비밀번호 검증
        if team.teampasswd != password.strip():
            raise ValueError(self.ERROR_MESSAGES['INVALID_PASSWORD'])
        
        # 중복 가입 재확인
        if TeamUser.objects.filter(team=team, user=user).exists():
            raise ValueError(self.ERROR_MESSAGES['ALREADY_MEMBER'])
        
        # 인원 초과 재확인
        current_member_count = team.get_current_member_count()
        if current_member_count >= team.maxuser:
            raise ValueError(self.ERROR_MESSAGES['TEAM_FULL'])
        
        # 팀 가입 처리
        TeamUser.objects.create(team=team, user=user)
        
        # 현재 인원수 업데이트
        team.currentuser = team.get_current_member_count()
        team.save()
        
        return team
    
    def get_user_teams(self, user):
        """사용자가 가입한 모든 팀을 반환합니다."""
        return Team.objects.filter(members=user).order_by('id')
    
    def get_team_statistics(self, team, milestones=None):
        """
        팀의 마일스톤 통계를 계산합니다.
        
        Args:
            team: 대상 팀
            milestones: 이미 조회된 마일스톤 QuerySet (선택적)
        
        Returns:
            dict: 마일스톤 상태별 통계 정보
        """
        today_date = date.today()
        if milestones is None:
            milestones = Milestone.objects.filter(team=team).order_by('priority', 'enddate')
        
        # 상태별 카운트
        stats = {
            'not_started': 0,
            'in_progress': 0,
            'completed': 0,
            'overdue': 0
        }
        
        for milestone in milestones:
            status = milestone.get_status(today_date)
            stats[status] += 1
        
        # 기존 변수들 호환성 유지
        stats.update({
            'active_milestones_count': stats['in_progress'] + stats['not_started'],
            'completed_milestones_count': stats['completed'],
            'overdue_milestones_count': stats['overdue'],
            'not_started_count': stats['not_started'],
            'in_progress_count': stats['in_progress'],
            'completed_count': stats['completed'],
            'overdue_count': stats['overdue']
        })
        
        # 오늘 진행 중인 마일스톤
        active_milestones = [m for m in milestones if m.get_status(today_date) == 'in_progress']
        if active_milestones:
            milestone = active_milestones[0]
            left = milestone.enddate - today_date
            stats['today_milestone'] = f'{milestone.title}, {left.days}일 남았습니다'
        else:
            stats['today_milestone'] = '진행 중인 마일스톤이 없습니다.'
        
        return stats
    
    @transaction.atomic
    def disband_team(self, team_id, host_user):
        """
        팀을 해체합니다. (호스트만 가능)
        
        Args:
            team_id: 해체할 팀 ID  
            host_user: 요청한 사용자 (호스트 검증용)
            
        Returns:
            str: 해체된 팀 이름
            
        Raises:
            ValueError: 권한 없음 또는 팀 없음
        """
        team = get_object_or_404(Team, pk=team_id)
        
        if team.host != host_user:
            raise ValueError('팀을 해체할 권한이 없습니다.')
        
        team_title = team.title
        team.delete()
        
        return team_title
    
    def _validate_team_creation_data(self, title, maxuser, teampasswd):
        """팀 생성 데이터 검증"""
        if not title or not title.strip():
            raise ValueError('팀 이름을 입력해주세요.')
        
        if not isinstance(maxuser, int) or maxuser < 1:
            raise ValueError('최대 인원수는 1명 이상이어야 합니다.')
        
        if not teampasswd or not teampasswd.strip():
            raise ValueError('팀 비밀번호를 입력해주세요.')
    
    def _generate_invite_code(self):
        """고유한 초대 코드를 생성합니다."""
        return base64.urlsafe_b64encode(
            codecs.encode(uuid.uuid4().bytes, "base64").rstrip()
        ).decode()[:16]


class MilestoneService:
    """마일스톤 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    def create_milestone(self, team, title, description, startdate, enddate, priority):
        """
        새 마일스톤을 생성합니다.
        
        Args:
            team: 소속 팀
            title: 마일스톤 제목
            description: 설명
            startdate: 시작일
            enddate: 종료일
            priority: 우선순위
            
        Returns:
            Milestone: 생성된 마일스톤
            
        Raises:
            ValueError: 검증 실패 시
        """
        # 날짜 검증
        self._validate_milestone_dates(startdate, enddate)
        
        milestone = Milestone.objects.create(
            team=team,
            title=title,
            description=description,
            startdate=startdate,
            enddate=enddate,
            priority=priority
        )
        
        return milestone
    
    def update_milestone(self, milestone_id, team, **update_data):
        """
        마일스톤을 업데이트합니다.
        
        Args:
            milestone_id: 마일스톤 ID
            team: 소속 팀 (권한 확인용)
            **update_data: 업데이트할 데이터
            
        Returns:
            tuple: (업데이트된 마일스톤, 업데이트된 필드 목록)
            
        Raises:
            ValueError: 검증 실패 시
        """
        milestone = get_object_or_404(Milestone, pk=milestone_id, team=team)
        updated_fields = []
        
        # 시작일 업데이트
        if 'startdate' in update_data:
            startdate = self._parse_date(update_data['startdate'])
            milestone.startdate = startdate
            updated_fields.append('시작일')
        
        # 종료일 업데이트
        if 'enddate' in update_data:
            enddate = self._parse_date(update_data['enddate'])
            milestone.enddate = enddate
            updated_fields.append('종료일')
        
        # 날짜 검증 (둘 다 있는 경우)
        if hasattr(milestone, 'startdate') and hasattr(milestone, 'enddate'):
            if milestone.startdate > milestone.enddate:
                raise ValueError('시작일은 종료일보다 이전이어야 합니다.')
        
        # 진행률 업데이트
        if 'progress_percentage' in update_data:
            progress = int(update_data['progress_percentage'])
            if not (0 <= progress <= 100):
                raise ValueError('진행률은 0-100 사이 값이어야 합니다.')
            
            milestone.progress_percentage = progress
            updated_fields.append('진행률')
            
            # 완료 상태 자동 업데이트
            if progress == 100 and not milestone.is_completed:
                milestone.is_completed = True
                milestone.completed_date = datetime.now()
                updated_fields.append('완료 상태')
            elif progress < 100 and milestone.is_completed:
                milestone.is_completed = False
                milestone.completed_date = None
                updated_fields.append('완료 상태')
        
        milestone.save()
        return milestone, updated_fields
    
    def delete_milestone(self, milestone_id, team):
        """
        마일스톤을 삭제합니다.
        
        Args:
            milestone_id: 삭제할 마일스톤 ID
            team: 소속 팀 (권한 확인용)
            
        Returns:
            str: 삭제된 마일스톤 제목
        """
        milestone = get_object_or_404(Milestone, pk=milestone_id, team=team)
        milestone_title = milestone.title
        milestone.delete()
        return milestone_title
    
    def get_team_milestones(self, team, order_by=None):
        """팀의 마일스톤 목록을 반환합니다."""
        queryset = Milestone.objects.filter(team=team)
        
        if order_by:
            queryset = queryset.order_by(*order_by)
        else:
            queryset = queryset.order_by('priority', 'enddate')
            
        return queryset
    
    def _validate_milestone_dates(self, startdate, enddate):
        """마일스톤 날짜 검증"""
        if startdate and enddate:
            if startdate > enddate:
                raise ValueError('시작일은 종료일보다 이전이어야 합니다.')
    
    def _parse_date(self, date_string):
        """문자열을 날짜 객체로 변환"""
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f'날짜 형식이 올바르지 않습니다. (YYYY-MM-DD 형식 필요)')