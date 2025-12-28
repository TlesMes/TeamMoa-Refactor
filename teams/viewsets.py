from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib import messages
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Team, Milestone
from .serializers import (
    TeamListSerializer, TeamDetailSerializer, TeamCreateSerializer,
    TeamUpdateSerializer,
    MilestoneSerializer, MilestoneCreateSerializer, MilestoneUpdateSerializer,
    MilestoneProgressModeSerializer
)
from .services import TeamService, MilestoneService
from api.permissions import IsTeamMember
from api.utils import api_response, api_success_response, api_error_response


class TeamViewSet(viewsets.ModelViewSet):
    """팀 관리 ViewSet"""
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team_service = TeamService()

    def get_queryset(self):
        """사용자가 속한 팀 목록 반환"""
        return Team.objects.filter(
            teamuser__user=self.request.user
        ).select_related('host').distinct()

    def get_serializer_class(self):
        """액션별 Serializer 클래스 선택"""
        if self.action == 'list':
            return TeamListSerializer
        elif self.action == 'retrieve':
            return TeamDetailSerializer
        elif self.action == 'create':
            return TeamCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TeamUpdateSerializer
        return TeamDetailSerializer

    def list(self, request, *args, **kwargs):
        """사용자가 속한 팀 목록 조회"""
        teams = self.team_service.get_user_teams(request.user)
        serializer = TeamListSerializer(teams, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """팀 상세 조회"""
        team = self.get_object()
        serializer = TeamDetailSerializer(team)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """팀 생성"""
        serializer = TeamCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            team = self.team_service.create_team(
                host_user=request.user,
                title=serializer.validated_data['title'],
                maxuser=serializer.validated_data['maxuser'],
                teampasswd=serializer.validated_data['teampasswd'],
                introduction=serializer.validated_data.get('introduction', '')
            )

            response_serializer = TeamDetailSerializer(team)
            return api_success_response(
                request,
                f'"{team.title}" 팀이 생성되었습니다.',
                data={'team': response_serializer.data},
                status_code=status.HTTP_201_CREATED
            )

        except ValueError as e:
            return api_error_response(request, str(e))

    def partial_update(self, request, *args, **kwargs):
        """팀 정보 수정 (PATCH)"""
        team = self.get_object()

        # 팀장만 수정 가능
        if team.host != request.user:
            return api_error_response(
                request,
                '팀장만 팀 정보를 수정할 수 있습니다.',
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = TeamUpdateSerializer(team, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # 팀 정보 업데이트
        for field, value in serializer.validated_data.items():
            setattr(team, field, value)
        team.save()

        response_serializer = TeamDetailSerializer(team)
        return api_success_response(
            request,
            '팀 정보가 수정되었습니다.',
            data={'team': response_serializer.data}
        )

    def destroy(self, request, *args, **kwargs):
        """팀 해체"""
        team = self.get_object()

        try:
            team_title = self.team_service.disband_team(team.id, request.user)
            return api_success_response(
                request,
                f'"{team_title}" 팀이 해체되었습니다.'
            )

        except ValueError as e:
            return api_error_response(request, str(e), status_code=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return api_error_response(request, str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """팀 통계 조회"""
        team = self.get_object()

        try:
            stats = self.team_service.get_team_statistics(team)
            return Response({
                'success': True,
                'data': stats
            })

        except Exception as e:
            return api_error_response(request, str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['delete'], url_path='members/(?P<user_id>[0-9]+)')
    def remove_member(self, request, pk=None, user_id=None):
        """팀 멤버 제거 (팀장의 추방 or 본인의 탈퇴)"""
        team = self.get_object()

        try:
            result = self.team_service.remove_member(
                team_id=team.id,
                target_user_id=user_id,
                requesting_user=request.user
            )

            if result['action_type'] == 'leave':
                message = f'"{team.title}" 팀에서 탈퇴했습니다.'
            else:
                message = f'{result["username"]}님을 팀에서 추방했습니다.'

            return api_success_response(
                request,
                message,
                data={'remaining_members': result['remaining_members']}
            )

        except ValueError as e:
            return api_error_response(request, str(e), status_code=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return api_error_response(request, str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        """마일스톤 목록 조회 (정렬: 시작일 → 종료일 → 우선순위)"""
        team = self.get_team()

        # 서비스 레이어를 통한 조회 (정렬 포함)
        # 같은 시작일/종료일이면 우선순위 높은 순
        milestones = self.milestone_service.get_team_milestones(
            team, order_by=['startdate', 'enddate', 'priority']
        )

        serializer = self.get_serializer(milestones, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """마일스톤 생성"""
        team = self.get_team()
        serializer = MilestoneCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # progress_mode 파라미터 추출 (기본값: 'auto')
            progress_mode = serializer.validated_data.get('progress_mode', 'auto')

            milestone = self.milestone_service.create_milestone(
                team=team,
                title=serializer.validated_data['title'],
                description=serializer.validated_data.get('description', ''),
                startdate=serializer.validated_data['startdate'],
                enddate=serializer.validated_data['enddate'],
                priority=serializer.validated_data['priority'],
                progress_mode=progress_mode
            )

            # 생성된 마일스톤을 MilestoneSerializer로 직렬화하여 반환
            response_serializer = MilestoneSerializer(milestone)
            return api_success_response(
                request,
                f'"{milestone.title}" 마일스톤이 생성되었습니다.',
                data={'milestone': response_serializer.data},
                status_code=status.HTTP_201_CREATED
            )

        except ValueError as e:
            return api_error_response(request, str(e))

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

            return api_success_response(
                request,
                f"마일스톤 {', '.join(updated_fields)}이(가) 업데이트되었습니다.",
                data={'milestone': response_serializer.data}
            )

        except ValueError as e:
            return api_error_response(request, str(e))

    def destroy(self, request, *args, **kwargs):
        """마일스톤 삭제"""
        milestone = self.get_object()
        team = self.get_team()

        try:
            milestone_title = self.milestone_service.delete_milestone(
                milestone_id=milestone.id,
                team=team
            )

            return api_success_response(
                request,
                f'"{milestone_title}" 마일스톤이 삭제되었습니다.'
            )

        except Exception as e:
            return api_error_response(request, str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'], url_path='progress-mode')
    def toggle_progress_mode(self, request, pk=None, team_pk=None):
        """
        진행률 모드 전환 (수동 ↔ AUTO)

        요청 본문:
        {
            "mode": "auto"  # 또는 "manual"
        }

        응답:
        {
            "milestone": {...},
            "metadata": {
                "old_mode": "manual",
                "new_mode": "auto",
                "progress_recalculated": true,
                "new_progress": 33
            }
        }
        """
        milestone = self.get_object()
        team = self.get_team()
        serializer = MilestoneProgressModeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            new_mode = serializer.validated_data['mode']

            # 서비스 레이어 호출
            updated_milestone, metadata = self.milestone_service.toggle_progress_mode(
                milestone_id=milestone.id,
                team=team,
                new_mode=new_mode
            )

            # metadata에 display 값 추가
            mode_display = {
                'manual': '수동 입력',
                'auto': 'TODO 기반 자동 계산'
            }
            metadata['new_mode_display'] = mode_display.get(metadata['new_mode'], metadata['new_mode'])

            return api_success_response(
                request,
                f'진행률 모드가 {metadata["new_mode_display"]}로 변경되었습니다.',
                data={
                    'milestone': MilestoneSerializer(updated_milestone).data,
                    'metadata': metadata
                }
            )

        except ValueError as e:
            return api_error_response(request, str(e))

    @action(detail=True, methods=['get'], url_path='with-stats')
    def milestone_with_stats(self, request, pk=None, team_pk=None):
        """
        마일스톤 + TODO 통계 조회

        응답:
        {
            "milestone": {...},
            "todo_stats": {
                "total": 10,
                "completed": 3,
                "in_progress": 7,
                "completion_rate": 30
            }
        }
        """
        milestone = self.get_object()
        team = self.get_team()

        try:
            # 서비스 레이어 호출
            result = self.milestone_service.get_milestone_with_todo_stats(
                milestone_id=milestone.id,
                team=team
            )

            return api_success_response(
                request,
                '',
                data={
                    'milestone': MilestoneSerializer(result['milestone']).data,
                    'todo_stats': result['todo_stats']
                }
            )

        except ValueError as e:
            return api_error_response(request, str(e))