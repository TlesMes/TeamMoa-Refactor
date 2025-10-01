from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Team, Milestone
from .serializers import (
    MilestoneSerializer, MilestoneCreateSerializer, MilestoneUpdateSerializer
)
from .services import MilestoneService
from api.permissions import IsTeamMember


class MilestoneViewSet(viewsets.ModelViewSet):
    """팀 마일스톤 관리 ViewSet"""
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated, IsTeamMember]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.milestone_service = MilestoneService()

    def get_queryset(self):
        """팀별 마일스톤 목록 반환"""
        team_id = self.kwargs.get('team_pk')
        if team_id:
            return Milestone.objects.filter(team_id=team_id).select_related('team')
        return Milestone.objects.none()

    def get_team(self):
        """현재 팀 객체 반환"""
        team_id = self.kwargs.get('team_pk')
        return get_object_or_404(Team, pk=team_id)

    def get_serializer_class(self):
        """액션별 Serializer 클래스 선택"""
        if self.action == 'create':
            return MilestoneCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MilestoneUpdateSerializer
        return MilestoneSerializer

    def list(self, request, *args, **kwargs):
        """마일스톤 목록 조회 (정렬 기본: 시작일)"""
        team = self.get_team()

        # 서비스 레이어를 통한 조회 (정렬 포함)
        milestones = self.milestone_service.get_team_milestones(
            team, order_by=['startdate', 'enddate']
        )

        serializer = self.get_serializer(milestones, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """마일스톤 생성"""
        team = self.get_team()
        serializer = MilestoneCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            milestone = self.milestone_service.create_milestone(
                team=team,
                title=serializer.validated_data['title'],
                description=serializer.validated_data.get('description', ''),
                startdate=serializer.validated_data['startdate'],
                enddate=serializer.validated_data['enddate'],
                priority=serializer.validated_data['priority']
            )

            # 생성된 마일스톤을 MilestoneSerializer로 직렬화하여 반환
            response_serializer = MilestoneSerializer(milestone)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            raise serializers.ValidationError({'detail': str(e)})

    def update(self, request, *args, **kwargs):
        """마일스톤 전체 업데이트 (PUT)"""
        return self._perform_update(request, partial=False)

    def partial_update(self, request, *args, **kwargs):
        """마일스톤 부분 업데이트 (PATCH) - 드래그앤드롭, 진행률 변경"""
        return self._perform_update(request, partial=True)

    def _perform_update(self, request, partial=False):
        """업데이트 로직 통합"""
        milestone = self.get_object()
        team = self.get_team()

        serializer = MilestoneUpdateSerializer(
            milestone,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)

        try:
            # 서비스 레이어를 통한 업데이트
            updated_milestone, updated_fields = self.milestone_service.update_milestone(
                milestone_id=milestone.id,
                team=team,
                **serializer.validated_data
            )

            # 업데이트된 마일스톤을 MilestoneSerializer로 직렬화하여 반환
            response_serializer = MilestoneSerializer(updated_milestone)

            return Response({
                'success': True,
                'message': f"마일스톤 {', '.join(updated_fields)}이(가) 업데이트되었습니다.",
                'milestone': response_serializer.data
            })

        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """마일스톤 삭제"""
        milestone = self.get_object()
        team = self.get_team()

        try:
            milestone_title = self.milestone_service.delete_milestone(
                milestone_id=milestone.id,
                team=team
            )

            return Response({
                'success': True,
                'message': f'"{milestone_title}" 마일스톤이 삭제되었습니다.'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)