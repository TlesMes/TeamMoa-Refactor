from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib import messages

from .models import Todo
from .serializers import (
    TodoSerializer, TodoCreateSerializer,
    TodoAssignSerializer, TodoCompleteSerializer,
    TeamMemberSerializer, TodoMilestoneAssignSerializer
)
from .services import TodoService
from teams.models import Team, TeamUser, Milestone
from api.permissions import IsTeamMember
from api.utils import api_response, api_success_response, api_error_response


class TodoViewSet(viewsets.ModelViewSet):
    """
    팀 TODO 관리 ViewSet

    참고:
    - list, create, retrieve, update 액션은 구현되어 있지만 프론트엔드에서 미사용
    - TODO 생성은 SSR Form 방식 사용 (TeamMembersPageView POST)
    - TODO 목록은 초기 렌더링 시 서버에서 제공
    - 실제 사용 중인 액션: destroy, assign, complete, move_to_todo, move_to_done
    """
    serializer_class = TodoSerializer
    permission_classes = [IsAuthenticated, IsTeamMember]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.todo_service = TodoService()

    def get_queryset(self):
        """팀별 TODO 목록 반환"""
        team_id = self.kwargs.get('team_pk')
        if team_id:
            return Todo.objects.filter(team_id=team_id).select_related('assignee__user')
        return Todo.objects.none()

    def get_team(self):
        """현재 팀 객체 반환"""
        team_id = self.kwargs.get('team_pk')
        return get_object_or_404(Team, pk=team_id)

    def perform_create(self, serializer):
        """TODO 생성 시 팀 설정"""
        team = self.get_team()
        try:
            todo = self.todo_service.create_todo(
                team=team,
                content=serializer.validated_data['content'],
                creator=self.request.user
            )
            # 생성된 객체로 serializer instance 설정
            serializer.instance = todo
        except ValueError as e:
            raise serializers.ValidationError({'content': str(e)})

    def create(self, request, *args, **kwargs):
        """TODO 생성"""
        serializer = TodoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # 생성된 TODO를 TodoSerializer로 직렬화하여 반환
        todo_serializer = TodoSerializer(serializer.instance)
        return Response(todo_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='move-to-todo')
    def move_to_todo(self, request, team_pk=None, pk=None):
        """TODO 보드로 이동"""
        todo = self.get_object()
        team = self.get_team()

        try:
            updated_todo = self.todo_service.move_to_todo(
                todo_id=todo.id,
                team=team,
                requester=request.user
            )

            return Response({
                'success': True,
                'message': '할 일이 TODO 보드로 이동되었습니다.',
                'todo': TodoSerializer(updated_todo).data
            })

        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='move-to-done')
    def move_to_done(self, request, team_pk=None, pk=None):
        """DONE 보드로 이동"""
        todo = self.get_object()
        team = self.get_team()

        try:
            updated_todo = self.todo_service.move_to_done(
                todo_id=todo.id,
                team=team,
                requester=request.user
            )

            return api_success_response(
                request,
                '할 일이 DONE 보드로 이동되었습니다.',
                data={'todo': TodoSerializer(updated_todo).data}
            )

        except ValueError as e:
            return api_error_response(request, str(e))

    @action(detail=True, methods=['post'])
    def assign(self, request, team_pk=None, pk=None):
        """TODO 팀원 할당"""
        todo = self.get_object()
        team = self.get_team()

        serializer = TodoAssignSerializer(data=request.data, context={'team': team})
        serializer.is_valid(raise_exception=True)

        try:
            updated_todo = self.todo_service.assign_todo(
                todo_id=todo.id,
                assignee_id=serializer.validated_data['member_id'],
                team=team,
                requester=request.user
            )

            assignee_name = updated_todo.assignee.user.nickname or updated_todo.assignee.user.username
            message = f'할 일이 {assignee_name}님에게 할당되었습니다.'

            return api_success_response(
                request,
                message,
                data={'todo': TodoSerializer(updated_todo).data}
            )

        except ValueError as e:
            return api_error_response(request, str(e))

    @action(detail=True, methods=['post'])
    def complete(self, request, team_pk=None, pk=None):
        """TODO 완료 토글"""
        todo = self.get_object()
        team = self.get_team()

        # 완료 토글은 추가 데이터 검증 불필요
        serializer = TodoCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_todo, metadata = self.todo_service.complete_todo(
                todo_id=todo.id,
                team=team,
                requester=request.user
            )

            is_completed = metadata['is_completed']
            status_message = '완료되었습니다.' if is_completed else '미완료로 변경되었습니다.'

            return api_success_response(
                request,
                status_message,
                data={
                    'is_completed': is_completed,
                    'todo': TodoSerializer(updated_todo).data,
                    # 마일스톤 관련 추가 정보 (Phase 2)
                    'milestone_updated': metadata.get('milestone_updated', False),
                    'milestone_id': metadata.get('milestone_id'),
                    'milestone_progress': metadata.get('milestone_progress')
                }
            )

        except ValueError as e:
            return api_error_response(request, str(e))

    @action(detail=True, methods=['patch'], url_path='assign-milestone')
    def assign_milestone(self, request, team_pk=None, pk=None):
        """
        TODO를 마일스톤에 할당/변경/해제

        요청 본문:
        {
            "milestone_id": 5  # 또는 null (해제)
        }

        응답:
        {
            "todo": {...},
            "metadata": {
                "milestone_changed": true,
                "old_milestone_id": 3,
                "new_milestone_id": 5,
                "old_milestone_updated": true,
                "new_milestone_updated": true
            }
        }
        """
        todo = self.get_object()
        team = self.get_team()
        serializer = TodoMilestoneAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        milestone_id = serializer.validated_data.get('milestone_id')

        try:
            # 마일스톤이 같은 팀 소속인지 검증 (None 아닌 경우)
            if milestone_id is not None:
                try:
                    milestone = Milestone.objects.get(pk=milestone_id, team=team)
                except Milestone.DoesNotExist:
                    return api_error_response(
                        request,
                        '마일스톤을 찾을 수 없거나 같은 팀에 속하지 않습니다.',
                        status_code=status.HTTP_404_NOT_FOUND
                    )
            else:
                milestone = None

            # 서비스 레이어 호출
            updated_todo, metadata = self.todo_service.assign_to_milestone(
                todo_id=todo.id,
                milestone_id=milestone.id if milestone else None,
                team=team
            )

            return api_success_response(
                request,
                '마일스톤 할당이 완료되었습니다.',
                data={
                    'todo': TodoSerializer(updated_todo).data,
                    'metadata': metadata
                }
            )

        except ValueError as e:
            return api_error_response(request, str(e))

    @action(detail=True, methods=['delete'], url_path='milestone')
    def detach_milestone(self, request, team_pk=None, pk=None):
        """
        TODO를 마일스톤에서 분리

        응답:
        {
            "todo": {...},
            "metadata": {
                "detached": true,
                "old_milestone_id": 5
            }
        }
        """
        todo = self.get_object()
        team = self.get_team()

        try:
            # 서비스 레이어 호출
            updated_todo, metadata = self.todo_service.detach_from_milestone(
                todo_id=todo.id,
                team=team
            )

            return api_success_response(
                request,
                '마일스톤 연결이 해제되었습니다.',
                data={
                    'todo': TodoSerializer(updated_todo).data,
                    'metadata': metadata
                }
            )

        except ValueError as e:
            return api_error_response(request, str(e))


class TeamMemberViewSet(viewsets.ReadOnlyModelViewSet):
    """팀 멤버 조회 ViewSet"""
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAuthenticated, IsTeamMember]

    def get_queryset(self):
        """팀별 멤버 목록 반환"""
        team_id = self.kwargs.get('team_pk')
        if team_id:
            return TeamUser.objects.filter(team_id=team_id).select_related('user')
        return TeamUser.objects.none()