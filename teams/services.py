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

    @transaction.atomic
    def remove_member(self, team_id, target_user_id, requesting_user):
        """
        팀에서 멤버를 제거합니다. (팀장의 추방 or 본인의 탈퇴)

        Args:
            team_id: 팀 ID
            target_user_id: 제거할 사용자 ID
            requesting_user: 요청한 사용자

        Returns:
            dict: 제거된 사용자 정보 및 액션 타입

        Raises:
            ValueError: 권한 없음, 팀장 탈퇴 시도 등
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        team = get_object_or_404(Team, pk=team_id)
        target_user = get_object_or_404(User, pk=target_user_id)

        # TeamUser 관계 확인
        try:
            team_user = TeamUser.objects.get(team=team, user=target_user)
        except TeamUser.DoesNotExist:
            raise ValueError('해당 사용자는 팀에 속해있지 않습니다.')

        is_host = team.host == requesting_user
        is_self = requesting_user.id == int(target_user_id)

        # 권한 검증
        if not (is_host or is_self):
            raise ValueError('권한이 없습니다.')

        # 팀장 본인 탈퇴 방지
        if team.host == target_user:
            raise ValueError('팀장은 탈퇴할 수 없습니다. 팀을 해체해주세요.')

        # 멤버 제거
        username = target_user.nickname if target_user.nickname else target_user.username
        team_user.delete()

        # currentuser 업데이트
        team.currentuser = team.get_current_member_count()
        team.save()

        action_type = 'leave' if is_self else 'remove'

        return {
            'username': username,
            'action_type': action_type,
            'remaining_members': team.currentuser
        }
    
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

    @transaction.atomic
    def transfer_ownership_on_user_deactivation(self, user):
        """
        사용자 탈퇴 시 소유 팀의 호스트 권한을 자동 이전합니다.

        전략:
        1. 가장 오래된 멤버에게 자동 승계 (TeamUser.id 오름차순)
        2. 멤버가 없으면 팀 삭제

        Args:
            user: 탈퇴하는 사용자

        Returns:
            dict: 처리 결과 (이전된 팀 수, 삭제된 팀 수)
        """
        owned_teams = Team.objects.filter(host=user)
        transferred_count = 0
        deleted_count = 0

        for team in owned_teams:
            # 다음 호스트 후보 찾기 (자신 제외, 가입일 순)
            next_host_membership = TeamUser.objects.filter(team=team)\
                                                   .exclude(user=user)\
                                                   .order_by('id')\
                                                   .first()

            if next_host_membership:
                # 호스트 자동 승계
                team.host = next_host_membership.user
                team.save()
                transferred_count += 1
            else:
                # 혼자인 팀은 삭제
                team.delete()
                deleted_count += 1

        return {
            'transferred': transferred_count,
            'deleted': deleted_count
        }

    @transaction.atomic
    def transfer_host(self, team_id, current_host, new_host_user_id):
        """
        팀 호스트 권한을 다른 팀원에게 수동으로 양도합니다.

        Args:
            team_id: 팀 ID
            current_host: 현재 호스트 (권한 검증용)
            new_host_user_id: 새 호스트가 될 User ID

        Returns:
            Team: 업데이트된 팀 객체

        Raises:
            ValueError: 권한 없음, 대상이 팀원 아님 등
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # 팀 조회
        team = get_object_or_404(Team, pk=team_id)

        # 권한 검증: 현재 호스트만 양도 가능
        if team.host != current_host:
            raise ValueError('팀장만 권한을 양도할 수 있습니다.')

        # 새 호스트 조회
        new_host = get_object_or_404(User, pk=new_host_user_id)

        # 자기 자신에게 양도 방지
        if team.host == new_host:
            raise ValueError('이미 팀장입니다.')

        # 새 호스트가 팀 멤버인지 확인
        if not TeamUser.objects.filter(team=team, user=new_host).exists():
            raise ValueError('팀 멤버에게만 권한을 양도할 수 있습니다.')

        # 호스트 변경
        team.host = new_host
        team.save()

        return team


class MilestoneService:
    """마일스톤 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    ERROR_MESSAGES = {
        'MILESTONE_NOT_FOUND': '마일스톤을 찾을 수 없습니다.',
        'MILESTONE_PERMISSION_DENIED': '마일스톤을 수정할 권한이 없습니다.',
        'INVALID_PROGRESS_MODE': '유효하지 않은 진행률 모드입니다.',
        'CANNOT_SET_PROGRESS_IN_AUTO': 'AUTO 모드에서는 진행률을 수동으로 설정할 수 없습니다.',
    }

    def create_milestone(self, team, title, description, startdate, enddate, priority, progress_mode='auto'):
        """
        새 마일스톤을 생성합니다.

        Args:
            team: 소속 팀
            title: 마일스톤 제목
            description: 설명
            startdate: 시작일
            enddate: 종료일
            priority: 우선순위
            progress_mode: 진행률 모드 ('manual' 또는 'auto', 기본값: 'auto')

        Returns:
            Milestone: 생성된 마일스톤

        Raises:
            ValueError: 검증 실패 시
        """
        # 날짜 검증
        self._validate_milestone_dates(startdate, enddate)

        # progress_mode 검증
        if progress_mode not in ['manual', 'auto']:
            raise ValueError(self.ERROR_MESSAGES['INVALID_PROGRESS_MODE'])

        milestone = Milestone.objects.create(
            team=team,
            title=title,
            description=description,
            startdate=startdate,
            enddate=enddate,
            priority=priority,
            progress_mode=progress_mode
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

        # AUTO 모드 보호: progress_percentage 수동 설정 방지
        if 'progress_percentage' in update_data and milestone.progress_mode == 'auto':
            raise ValueError(self.ERROR_MESSAGES['CANNOT_SET_PROGRESS_IN_AUTO'])

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
        from django.db.models import Case, When, IntegerField

        # 우선순위를 숫자로 변환 (critical=1, minimal=5)
        queryset = Milestone.objects.filter(team=team).annotate(
            priority_order=Case(
                When(priority='critical', then=1),
                When(priority='high', then=2),
                When(priority='medium', then=3),
                When(priority='low', then=4),
                When(priority='minimal', then=5),
                default=6,
                output_field=IntegerField(),
            )
        )

        if order_by:
            # order_by에 'priority' 포함 시 priority_order로 치환
            processed_order = []
            for field in order_by:
                if field == 'priority':
                    processed_order.append('priority_order')
                elif field == '-priority':
                    processed_order.append('-priority_order')
                else:
                    processed_order.append(field)
            queryset = queryset.order_by(*processed_order)
        else:
            queryset = queryset.order_by('priority_order', 'enddate')

        return queryset
    
    def _validate_milestone_dates(self, startdate, enddate):
        """마일스톤 날짜 검증"""
        if startdate and enddate:
            if startdate > enddate:
                raise ValueError('시작일은 종료일보다 이전이어야 합니다.')
    
    def _parse_date(self, date_input):
        """문자열 또는 날짜 객체를 날짜 객체로 변환"""
        # 이미 date 객체인 경우 그대로 반환 (DRF Serializer에서 파싱된 경우)
        if isinstance(date_input, date):
            return date_input

        # 문자열인 경우 파싱
        if isinstance(date_input, str):
            try:
                return datetime.strptime(date_input, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(f'날짜 형식이 올바르지 않습니다. (YYYY-MM-DD 형식 필요)')

        raise ValueError(f'날짜는 문자열 또는 date 객체여야 합니다. (받은 타입: {type(date_input)})')

    @transaction.atomic
    def toggle_progress_mode(self, milestone_id, team, new_mode):
        """
        마일스톤 진행률 모드 전환

        Args:
            milestone_id: 마일스톤 ID
            team: Team 인스턴스
            new_mode: 전환할 모드 ('manual' 또는 'auto')

        Returns:
            tuple: (Milestone, dict)
                - Milestone: 업데이트된 마일스톤
                - dict: {'old_mode': str, 'new_mode': str, 'progress_recalculated': bool, 'new_progress': int}

        Raises:
            ValueError: 유효하지 않은 모드 또는 권한 없음
        """
        # 1. 마일스톤 조회
        milestone = get_object_or_404(Milestone, pk=milestone_id, team=team)

        # 2. 모드 검증
        if new_mode not in ['manual', 'auto']:
            raise ValueError(self.ERROR_MESSAGES['INVALID_PROGRESS_MODE'])

        old_mode = milestone.progress_mode

        # 3. 이미 동일한 모드면 조기 반환
        if old_mode == new_mode:
            return milestone, {
                'old_mode': old_mode,
                'new_mode': new_mode,
                'progress_recalculated': False,
                'new_progress': milestone.progress_percentage
            }

        # 4. 모드 전환
        milestone.progress_mode = new_mode
        progress_recalculated = False

        # 5. manual → auto: TODO 기반 즉시 재계산
        if new_mode == 'auto':
            milestone.update_progress_from_todos()
            progress_recalculated = True

        # 6. auto → manual: 기존 진행률 유지
        milestone.save()

        return milestone, {
            'old_mode': old_mode,
            'new_mode': new_mode,
            'progress_recalculated': progress_recalculated,
            'new_progress': milestone.progress_percentage
        }

    def get_milestone_with_todo_stats(self, milestone_id, team):
        """
        마일스톤과 연결된 TODO 통계 조회

        Args:
            milestone_id: 마일스톤 ID
            team: Team 인스턴스

        Returns:
            dict: {
                'milestone': Milestone,
                'todo_stats': {
                    'total': int,
                    'completed': int,
                    'in_progress': int,
                    'completion_rate': int (0-100)
                }
            }

        Raises:
            ValueError: 마일스톤을 찾을 수 없음
        """
        milestone = get_object_or_404(Milestone, pk=milestone_id, team=team)

        stats = milestone.get_todo_stats()

        return {
            'milestone': milestone,
            'todo_stats': stats
        }