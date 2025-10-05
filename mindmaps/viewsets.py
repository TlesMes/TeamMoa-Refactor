from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib import messages

from .models import Mindmap, Node, NodeConnection, Comment
from .serializers import (
    MindmapSerializer, MindmapCreateSerializer,
    NodeSerializer, NodeCreateSerializer, NodeUpdateSerializer,
    NodeConnectionSerializer, NodeConnectionCreateSerializer,
    CommentSerializer, CommentCreateSerializer,
    NodeRecommendSerializer
)
from .services import MindmapService, DuplicateTitleError
from teams.models import Team
from api.permissions import IsTeamMember
from api.utils import api_response, api_success_response, api_error_response


class MindmapViewSet(viewsets.ModelViewSet):
    """마인드맵 관리 ViewSet"""
    serializer_class = MindmapSerializer
    permission_classes = [IsAuthenticated, IsTeamMember]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mindmap_service = MindmapService()

    def get_queryset(self):
        """팀별 마인드맵 목록 반환"""
        team_id = self.kwargs.get('team_pk')
        if team_id:
            return Mindmap.objects.filter(team_id=team_id).select_related('team')
        return Mindmap.objects.none()

    def get_team(self):
        """현재 팀 객체 반환"""
        team_id = self.kwargs.get('team_pk')
        return get_object_or_404(Team, pk=team_id)

    def list(self, request, *args, **kwargs):
        """마인드맵 목록 조회"""
        team = self.get_team()
        mindmaps = self.mindmap_service.get_team_mindmaps(team.id)
        serializer = self.get_serializer(mindmaps, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """마인드맵 상세 조회 (노드 및 연결선 포함)"""
        mindmap_id = kwargs.get('pk')
        mindmap_data = self.mindmap_service.get_mindmap_with_nodes(mindmap_id)

        # 마인드맵 직렬화
        mindmap_serializer = MindmapSerializer(mindmap_data['mindmap'])
        nodes_serializer = NodeSerializer(mindmap_data['nodes'], many=True)
        lines_serializer = NodeConnectionSerializer(mindmap_data['lines'], many=True)

        return Response({
            'success': True,
            'mindmap': mindmap_serializer.data,
            'nodes': nodes_serializer.data,
            'lines': lines_serializer.data
        })

    def create(self, request, *args, **kwargs):
        """마인드맵 생성"""
        team = self.get_team()
        serializer = MindmapCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            mindmap = self.mindmap_service.create_mindmap(
                team_id=team.id,
                title=serializer.validated_data['title'],
                creator=request.user
            )

            response_serializer = MindmapSerializer(mindmap)
            return Response({
                'success': True,
                'message': f'마인드맵 "{mindmap.title}"이 생성되었습니다.',
                'mindmap': response_serializer.data
            }, status=status.HTTP_201_CREATED)

        except DuplicateTitleError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """마인드맵 삭제"""
        mindmap_id = kwargs.get('pk')

        try:
            mindmap_title = self.mindmap_service.delete_mindmap(
                mindmap_id=mindmap_id,
                user=request.user
            )

            return Response({
                'success': True,
                'message': f'마인드맵 "{mindmap_title}"이 삭제되었습니다.'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NodeViewSet(viewsets.ModelViewSet):
    """노드 관리 ViewSet"""
    serializer_class = NodeSerializer
    permission_classes = [IsAuthenticated, IsTeamMember]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mindmap_service = MindmapService()

    def get_queryset(self):
        """마인드맵별 노드 목록 반환"""
        mindmap_id = self.kwargs.get('mindmap_pk')
        if mindmap_id:
            return Node.objects.filter(mindmap_id=mindmap_id).select_related('mindmap')
        return Node.objects.none()

    def get_mindmap(self):
        """현재 마인드맵 객체 반환"""
        mindmap_id = self.kwargs.get('mindmap_pk')
        return get_object_or_404(Mindmap, pk=mindmap_id)

    def create(self, request, *args, **kwargs):
        """노드 생성"""
        mindmap = self.get_mindmap()
        serializer = NodeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            node, connection_message = self.mindmap_service.create_node(
                mindmap_id=mindmap.id,
                node_data=serializer.validated_data,
                creator=request.user
            )

            message = f'노드 "{node.title}"이 생성되었습니다.'
            if connection_message:
                message += connection_message

            response_serializer = NodeSerializer(node)
            return Response({
                'success': True,
                'message': message,
                'node': response_serializer.data
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """노드 부분 업데이트 (위치 이동 등)"""
        node = self.get_object()
        serializer = NodeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # 직접 업데이트 (간단한 필드만)
        for field, value in serializer.validated_data.items():
            setattr(node, field, value)
        node.save()

        response_serializer = NodeSerializer(node)
        return Response({
            'success': True,
            'message': '노드가 업데이트되었습니다.',
            'node': response_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        """노드 삭제"""
        node = self.get_object()

        try:
            node_title, mindmap_id = self.mindmap_service.delete_node(
                node_id=node.id,
                user=request.user
            )

            return Response({
                'success': True,
                'message': f'노드 "{node_title}"이 삭제되었습니다.'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='recommend')
    def recommend(self, request, team_pk=None, mindmap_pk=None, pk=None):
        """노드 추천 토글"""
        node = self.get_object()

        try:
            action_type, count = self.mindmap_service.toggle_node_recommendation(
                node_id=node.id,
                user_id=request.user.id
            )

            action_text = "추가" if action_type == "added" else "취소"
            return Response({
                'success': True,
                'message': f'추천이 {action_text}되었습니다.',
                'action': action_type,
                'recommendation_count': count
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def comments(self, request, team_pk=None, mindmap_pk=None, pk=None):
        """노드 댓글 조회 및 생성"""
        node = self.get_object()

        if request.method == 'GET':
            # 댓글 목록 조회
            node_data = self.mindmap_service.get_node_with_comments(node.id)
            comments_serializer = CommentSerializer(node_data['comments'], many=True)

            return Response({
                'success': True,
                'data': comments_serializer.data
            })

        else:  # POST
            # 댓글 생성
            serializer = CommentCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            try:
                comment = self.mindmap_service.create_comment(
                    node_id=node.id,
                    comment_text=serializer.validated_data['comment'],
                    user=request.user
                )

                response_serializer = CommentSerializer(comment)
                return Response({
                    'success': True,
                    'message': '댓글이 등록되었습니다.',
                    'comment': response_serializer.data
                }, status=status.HTTP_201_CREATED)

            except ValueError as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)


class NodeConnectionViewSet(viewsets.ModelViewSet):
    """노드 연결선 관리 ViewSet"""
    serializer_class = NodeConnectionSerializer
    permission_classes = [IsAuthenticated, IsTeamMember]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mindmap_service = MindmapService()

    def get_queryset(self):
        """마인드맵별 연결선 목록 반환"""
        mindmap_id = self.kwargs.get('mindmap_pk')
        if mindmap_id:
            return NodeConnection.objects.filter(
                mindmap_id=mindmap_id
            ).select_related('from_node', 'to_node', 'mindmap')
        return NodeConnection.objects.none()

    def get_mindmap(self):
        """현재 마인드맵 객체 반환"""
        mindmap_id = self.kwargs.get('mindmap_pk')
        return get_object_or_404(Mindmap, pk=mindmap_id)

    def create(self, request, *args, **kwargs):
        """노드 연결 생성"""
        mindmap = self.get_mindmap()
        serializer = NodeConnectionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            connection = self.mindmap_service.create_node_connection(
                from_node_id=serializer.validated_data['from_node_id'],
                to_node_id=serializer.validated_data['to_node_id'],
                mindmap_id=mindmap.id
            )

            response_serializer = NodeConnectionSerializer(connection)
            return Response({
                'success': True,
                'message': '노드가 연결되었습니다.',
                'connection': response_serializer.data
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
