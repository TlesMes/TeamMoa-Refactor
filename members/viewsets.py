from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Todo
from .serializers import (
    TodoSerializer, TodoCreateSerializer, TodoMoveSerializer,
    TodoAssignSerializer, TodoCompleteSerializer, TodoReturnSerializer,
    TeamMemberSerializer
)
from .services import TodoService
from teams.models import Team, TeamUser
from api.permissions import IsTeamMember


class TodoViewSet(viewsets.ModelViewSet):
    """팀 TODO 관리 ViewSet"""
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

    @action(detail=True, methods=['post'])
    def move(self, request, team_pk=None, pk=None):
        """TODO 상태/순서 이동"""
        todo = self.get_object()
        team = self.get_team()

        serializer = TodoMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_todo = self.todo_service.move_todo(
                todo_id=todo.id,
                new_status=serializer.validated_data['new_status'],
                team=team,
                requester=request.user,
                new_order=serializer.validated_data['new_order']
            )

            status_display = self.todo_service.get_status_display(
                serializer.validated_data['new_status']
            )

            return Response({
                'success': True,
                'message': f'할 일이 {status_display}(으)로 이동되었습니다.',
                'todo': TodoSerializer(updated_todo).data
            })

        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

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
            message = f'{updated_todo.content}이(가) {assignee_name}님에게 할당되었습니다.'

            return Response({
                'success': True,
                'message': message,
                'todo': TodoSerializer(updated_todo).data
            })

        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def complete(self, request, team_pk=None, pk=None):
        """TODO 완료 토글"""
        todo = self.get_object()
        team = self.get_team()

        # 완료 토글은 추가 데이터 검증 불필요
        serializer = TodoCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_todo, new_status = self.todo_service.complete_todo(
                todo_id=todo.id,
                team=team,
                requester=request.user
            )

            status_message = '완료되었습니다.' if new_status == 'done' else '미완료로 변경되었습니다.'

            return Response({
                'success': True,
                'message': status_message,
                'new_status': new_status,
                'todo': TodoSerializer(updated_todo).data
            })

        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def return_to_board(self, request, team_pk=None, pk=None):
        """TODO 보드로 되돌리기"""
        todo = self.get_object()
        team = self.get_team()

        serializer = TodoReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_todo = self.todo_service.return_to_board(
                todo_id=todo.id,
                team=team,
                requester=request.user
            )

            message = '할일이 보드로 되돌려졌습니다.'

            return Response({
                'success': True,
                'message': message,
                'todo': TodoSerializer(updated_todo).data
            })

        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


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