from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from datetime import timedelta

from .models import PersonalDaySchedule
from .serializers import (
    PersonalDayScheduleSerializer,
    ScheduleCreateSerializer,
    TeamAvailabilitySerializer,
    TeamScheduleQuerySerializer
)
from .services import ScheduleService
from teams.models import Team, TeamUser
from api.permissions import IsTeamMember


class ScheduleViewSet(viewsets.ModelViewSet):
    """팀 스케줄 관리 ViewSet"""
    serializer_class = PersonalDayScheduleSerializer
    permission_classes = [IsAuthenticated, IsTeamMember]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schedule_service = ScheduleService()

    def get_queryset(self):
        """팀별 스케줄 목록 반환"""
        team_id = self.kwargs.get('team_pk')
        if team_id:
            return PersonalDaySchedule.objects.filter(
                owner__team_id=team_id
            ).select_related('owner__user', 'owner__team')
        return PersonalDaySchedule.objects.none()

    def get_team(self):
        """현재 팀 객체 반환"""
        team_id = self.kwargs.get('team_pk')
        return get_object_or_404(Team, pk=team_id)

    @action(detail=False, methods=['post'], url_path='save-personal')
    def save_personal_schedule(self, request, team_pk=None):
        """
        개인 주간 스케줄 저장

        POST /api/v1/teams/{team_pk}/schedules/save-personal/
        {
            "week_start": "2025-10-06",
            "schedule_data": {"time_0-1": true, "time_9-2": true, ...}
        }
        """
        team = self.get_team()
        serializer = ScheduleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # 팀 멤버 확인
            team_user = get_object_or_404(TeamUser, team=team, user=request.user)

            # 서비스 레이어를 통한 스케줄 저장
            updated_days = self.schedule_service.save_personal_schedule(
                team_user=team_user,
                week_start=serializer.validated_data['week_start'],
                schedule_data=serializer.validated_data['schedule_data']
            )

            if updated_days > 0:
                message = f'주간 스케줄이 성공적으로 저장되었습니다. ({updated_days}일)'
            else:
                message = '등록된 가능 시간이 없습니다.'

            return Response({
                'success': True,
                'message': message,
                'updated_days': updated_days
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='team-availability')
    def get_team_availability(self, request, team_pk=None):
        """
        팀 가용성 조회

        GET /api/v1/teams/{team_pk}/schedules/team-availability/?start_date=2025-10-06&end_date=2025-10-12
        """
        team = self.get_team()

        # 쿼리 파라미터 검증
        query_serializer = TeamScheduleQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        start_date = query_serializer.validated_data['start_date']
        end_date = query_serializer.validated_data['end_date']

        # 서비스 레이어를 통한 가용성 계산
        availability_data = self.schedule_service.get_team_availability(
            team=team,
            start_date=start_date,
            end_date=end_date
        )

        # 응답 직렬화
        response_serializer = TeamAvailabilitySerializer(availability_data, many=True)

        return Response({
            'success': True,
            'data': response_serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='my-schedule')
    def get_my_schedule(self, request, team_pk=None):
        """
        내 개인 스케줄 조회

        GET /api/v1/teams/{team_pk}/schedules/my-schedule/?start_date=2025-10-06&end_date=2025-10-12
        """
        team = self.get_team()

        # 쿼리 파라미터 검증
        query_serializer = TeamScheduleQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        start_date = query_serializer.validated_data['start_date']
        end_date = query_serializer.validated_data['end_date']

        try:
            team_user = get_object_or_404(TeamUser, team=team, user=request.user)

            # 해당 기간의 내 스케줄 조회
            my_schedules = PersonalDaySchedule.objects.filter(
                owner=team_user,
                date__range=[start_date, end_date]
            ).order_by('date')

            serializer = PersonalDayScheduleSerializer(my_schedules, many=True)

            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
