from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q, Prefetch, Max
from .models import Todo
from teams.models import Team, TeamUser, Milestone


class TodoServiceException(Exception):
    """Todo 서비스 레이어 기본 예외"""
    pass


class TodoService:
    """Todo 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    ERROR_MESSAGES = {
        'NO_PERMISSION': '권한이 없습니다.',
        'TODO_NOT_FOUND': '할 일을 찾을 수 없습니다.',
        'TEAM_NOT_FOUND': '팀을 찾을 수 없습니다.',
        'MEMBER_NOT_FOUND': '팀 멤버를 찾을 수 없습니다.',
        'ALREADY_ASSIGNED': '이미 할당된 할 일입니다.',
        'SELF_ASSIGN_ONLY': '본인에게만 할당할 수 있습니다.',
        'MILESTONE_NOT_FOUND': '마일스톤을 찾을 수 없습니다.',
        'TODO_ALREADY_ASSIGNED_TO_MILESTONE': '이미 해당 마일스톤에 할당된 TODO입니다.',
        'TODO_NOT_IN_MILESTONE': 'TODO가 마일스톤에 할당되어 있지 않습니다.',
        'MILESTONE_NOT_IN_SAME_TEAM': '마일스톤과 TODO가 같은 팀에 속해야 합니다.',
    }
    
    def create_todo(self, team, content, creator):
        """
        새 Todo를 생성합니다.
        
        Args:
            team: 대상 팀
            content: Todo 내용
            creator: 생성자 (임시)
            
        Returns:
            Todo: 생성된 Todo 객체
            
        Raises:
            ValueError: 입력값 검증 실패 시
        """
        if not content or not content.strip():
            raise ValueError('할 일 내용을 입력해주세요.')

        todo = Todo.objects.create(
            content=content.strip(),
            team=team,
            is_completed=False
        )

        return todo
    
    @transaction.atomic
    def assign_todo(self, todo_id, assignee_id, team, requester):
        """
        Todo를 팀원에게 할당합니다.
        해당 멤버 보드의 마지막 순서로 이동

        Args:
            todo_id: Todo ID
            assignee_id: 할당받을 TeamUser ID
            team: 대상 팀
            requester: 요청자

        Returns:
            Todo: 업데이트된 Todo 객체

        Raises:
            ValueError: 권한 없음 또는 검증 실패
        """
        todo = get_object_or_404(Todo, pk=todo_id, team=team)
        assignee = get_object_or_404(TeamUser, pk=assignee_id, team=team)

        # 권한 검증
        if not self._can_assign_todo(todo, assignee, requester, team):
            raise ValueError(self.ERROR_MESSAGES['NO_PERMISSION'])

        # 해당 멤버 보드의 마지막 order 계산
        max_order = Todo.objects.filter(
            team=team,
            assignee=assignee
        ).aggregate(Max('order'))['order__max'] or 0

        # 할당 처리
        todo.assignee = assignee
        todo.order = max_order + 1
        todo.save()

        return todo

    @transaction.atomic
    def complete_todo(self, todo_id, team, requester):
        """
        Todo 완료 상태를 토글합니다.

        Args:
            todo_id: Todo ID
            team: 대상 팀
            requester: 요청자

        Returns:
            tuple: (Todo, dict)
                - Todo: 업데이트된 TODO
                - dict: {
                    'was_completed': bool,
                    'is_completed': bool,
                    'milestone_updated': bool,
                    'milestone_id': int or None,
                    'milestone_progress': int or None
                }

        Raises:
            ValueError: 권한 없음
        """
        todo = get_object_or_404(Todo, pk=todo_id, team=team)
        current_teamuser = self._get_current_teamuser(team, requester)

        # 권한 검증: 팀장이거나 자신에게 할당된 할일
        if not (self._is_team_host(team, requester) or todo.assignee == current_teamuser):
            raise ValueError(self.ERROR_MESSAGES['NO_PERMISSION'])

        # 이전 완료 상태 저장
        was_completed = todo.is_completed

        # 완료 상태 토글
        todo.is_completed = not todo.is_completed
        todo.completed_at = timezone.now() if todo.is_completed else None

        todo.save()  # save() 훅이 자동으로 마일스톤 진행률 갱신

        # 마일스톤 정보 수집
        milestone_updated = False
        milestone_progress = None
        milestone_id = None

        if todo.milestone:
            milestone_id = todo.milestone.id
            if todo.milestone.progress_mode == 'auto':
                milestone_updated = True
                milestone_progress = todo.milestone.progress_percentage

        # 확장된 반환값
        return todo, {
            'was_completed': was_completed,
            'is_completed': todo.is_completed,
            'milestone_updated': milestone_updated,
            'milestone_id': milestone_id,
            'milestone_progress': milestone_progress
        }
    
    @transaction.atomic
    def move_to_todo(self, todo_id, team, requester):
        """
        Todo를 TODO 보드로 이동합니다.
        assignee=null, is_completed=false
        해당 보드의 마지막 순서로 이동

        Args:
            todo_id: Todo ID
            team: 대상 팀
            requester: 요청자

        Returns:
            Todo: 업데이트된 Todo 객체

        Raises:
            ValueError: 권한 없음
        """
        todo = get_object_or_404(Todo, pk=todo_id, team=team)

        # 권한 검증
        if not self._can_move_todo(todo, requester, team):
            raise ValueError(self.ERROR_MESSAGES['NO_PERMISSION'])

        # TODO 보드의 마지막 order 계산
        max_order = Todo.objects.filter(
            team=team,
            assignee__isnull=True,
            is_completed=False
        ).aggregate(Max('order'))['order__max'] or 0

        todo.assignee = None
        todo.is_completed = False
        todo.completed_at = None
        todo.order = max_order + 1
        todo.save()

        return todo

    @transaction.atomic
    def move_to_done(self, todo_id, team, requester):
        """
        Todo를 DONE 보드로 이동합니다.
        assignee=null, is_completed=true
        해당 보드의 마지막 순서로 이동

        Args:
            todo_id: Todo ID
            team: 대상 팀
            requester: 요청자

        Returns:
            Todo: 업데이트된 Todo 객체

        Raises:
            ValueError: 권한 없음
        """
        todo = get_object_or_404(Todo, pk=todo_id, team=team)

        # 권한 검증
        if not self._can_move_todo(todo, requester, team):
            raise ValueError(self.ERROR_MESSAGES['NO_PERMISSION'])

        # DONE 보드의 마지막 order 계산
        max_order = Todo.objects.filter(
            team=team,
            assignee__isnull=True,
            is_completed=True
        ).aggregate(Max('order'))['order__max'] or 0

        todo.assignee = None
        # is_completed가 false->true로 변하는 경우만 completed_at 설정
        if not todo.is_completed:
            todo.completed_at = timezone.now()
        todo.is_completed = True
        todo.order = max_order + 1
        todo.save()

        return todo
    
    def delete_todo(self, todo_id, team):
        """
        Todo를 삭제합니다.

        Args:
            todo_id: Todo ID
            team: 대상 팀

        Returns:
            str: 삭제된 Todo 내용
        """
        todo = get_object_or_404(Todo, pk=todo_id, team=team)
        todo_content = todo.content
        todo.delete()

        return todo_content

    @transaction.atomic
    def assign_to_milestone(self, todo_id, milestone_id, team):
        """
        TODO를 마일스톤에 할당 (할당/변경/해제 모두 처리)

        Args:
            todo_id: TODO ID
            milestone_id: 마일스톤 ID (None이면 연결 해제)
            team: Team 인스턴스

        Returns:
            tuple: (Todo, dict)
                - Todo: 업데이트된 TODO
                - dict: {
                    'milestone_changed': bool,
                    'old_milestone_id': int or None,
                    'new_milestone_id': int or None,
                    'old_milestone_updated': bool,
                    'new_milestone_updated': bool
                }

        Raises:
            ValueError: TODO 또는 마일스톤을 찾을 수 없음

        Examples:
            # 할당
            >>> assign_to_milestone(1, 5, team)
            # 변경 (5 → 10)
            >>> assign_to_milestone(1, 10, team)
            # 해제
            >>> assign_to_milestone(1, None, team)  # detach_from_milestone() 호출
        """
        # 1. TODO 조회
        todo = get_object_or_404(Todo, pk=todo_id, team=team)

        # 2. None이면 연결 해제 (detach 메서드 위임)
        if milestone_id is None:
            return self.detach_from_milestone(todo_id, team)

        # 3. 마일스톤 조회 및 검증
        milestone = get_object_or_404(Milestone, pk=milestone_id, team=team)

        # 4. 이미 동일한 마일스톤에 할당됨
        if todo.milestone and todo.milestone.id == milestone_id:
            raise ValueError(self.ERROR_MESSAGES['TODO_ALREADY_ASSIGNED_TO_MILESTONE'])

        # 5. 기존 마일스톤 저장
        old_milestone = todo.milestone
        old_milestone_id = old_milestone.id if old_milestone else None

        # 6. 새 마일스톤 할당
        todo.milestone = milestone
        todo.save()  # save() 훅이 자동으로 이전/새 마일스톤 진행률 모두 갱신

        # 7. 메타데이터 반환
        return todo, {
            'milestone_changed': True,
            'old_milestone_id': old_milestone_id,
            'new_milestone_id': milestone_id,
            'old_milestone_updated': old_milestone and old_milestone.progress_mode == 'auto',
            'new_milestone_updated': milestone.progress_mode == 'auto'
        }

    @transaction.atomic
    def detach_from_milestone(self, todo_id, team):
        """
        TODO의 마일스톤 연결 해제 (명시적 해제 전용)

        Args:
            todo_id: TODO ID
            team: Team 인스턴스

        Returns:
            tuple: (Todo, dict)
                - Todo: 업데이트된 TODO
                - dict: {'detached': bool, 'old_milestone_id': int or None}

        Raises:
            ValueError: TODO를 찾을 수 없음 또는 이미 연결 해제 상태

        Examples:
            # 연결 해제
            >>> detach_from_milestone(1, team)
            # 이미 연결 해제 상태면 에러
            >>> detach_from_milestone(1, team)  # ValueError 발생
        """
        # 1. TODO 조회
        todo = get_object_or_404(Todo, pk=todo_id, team=team)

        # 2. 이미 연결 해제 상태
        if not todo.milestone:
            raise ValueError(self.ERROR_MESSAGES['TODO_NOT_IN_MILESTONE'])

        # 3. 기존 마일스톤 저장
        old_milestone_id = todo.milestone.id

        # 4. detach_from_milestone() 메서드 호출 (모델 메서드 활용)
        todo.detach_from_milestone()

        return todo, {
            'detached': True,
            'old_milestone_id': old_milestone_id
        }
    
    def get_team_todos_with_stats(self, team):
        """
        팀의 모든 Todo와 멤버별 통계를 최적화된 쿼리로 조회합니다.

        Args:
            team: 대상 팀

        Returns:
            dict: 멤버 데이터, 미할당 Todo, 완료된 Todo
        """
        # 🚀 최적화: 단일 쿼리로 모든 멤버 데이터 + 통계 조회
        members_with_stats = TeamUser.objects.filter(team=team).annotate(
            todo_count=Count('todo_set', filter=Q(todo_set__team=team)),
            completed_count=Count('todo_set',
                filter=Q(todo_set__team=team, todo_set__is_completed=True)),
            in_progress_count=Count('todo_set',
                filter=Q(todo_set__team=team, todo_set__is_completed=False))
        ).select_related('user').prefetch_related(
            Prefetch('todo_set',
                queryset=Todo.objects.filter(team=team).select_related('milestone').order_by('order', 'created_at'))
        )

        # 미할당 TODO를 한 번에 조회 후 Python에서 분리 (쿼리 1개 절약)
        todos_unassigned_all = list(Todo.objects.filter(
            team=team,
            assignee__isnull=True
        ).select_related('milestone').order_by('order', 'created_at'))

        # Python에서 완료 여부로 분리 (추가 쿼리 없음)
        todos_unassigned = [todo for todo in todos_unassigned_all if not todo.is_completed]
        todos_done = [todo for todo in todos_unassigned_all if todo.is_completed]

        # 🎯 최적화된 데이터 구조 - 이미 prefetch된 데이터 활용
        members_data = []
        for member in members_with_stats:
            members_data.append({
                'member': member,
                'todos': member.todo_set.all(),  # prefetch된 데이터 사용
                'todo_count': member.todo_count,  # annotate된 값 사용
                'completed_count': member.completed_count,  # annotate된 값 사용
                'in_progress_count': member.in_progress_count,  # 추가 통계
            })

        return {
            'members': members_with_stats,
            'todos_unassigned': todos_unassigned,
            'todos_done': todos_done,
            'members_data': members_data
        }

    # Private 헬퍼 메서드들
    def _can_assign_todo(self, todo, assignee, requester, team):
        """Todo 할당 권한 검증"""
        # 팀장은 모든 할일 할당 가능
        if self._is_team_host(team, requester):
            return True
        
        # 미할당 할일을 본인에게만 할당 가능
        if todo.assignee is None and assignee.user == requester:
            return True
        
        return False
    
    def _can_move_todo(self, todo, requester, team):
        """Todo 이동 권한 검증"""
        # 팀장은 모든 할일 조작 가능
        if self._is_team_host(team, requester):
            return True
        
        # 자신에게 할당된 할일만 조작 가능
        current_teamuser = self._get_current_teamuser(team, requester)
        if todo.assignee == current_teamuser or todo.assignee is None:
            return True
        
        return False
    
    def _is_team_host(self, team, user):
        """팀장 권한 확인"""
        return team.host == user
    
    def _get_current_teamuser(self, team, user):
        """현재 사용자의 TeamUser 객체 조회"""
        try:
            return TeamUser.objects.select_related('user').get(team=team, user=user)
        except TeamUser.DoesNotExist:
            raise ValueError(self.ERROR_MESSAGES['MEMBER_NOT_FOUND'])