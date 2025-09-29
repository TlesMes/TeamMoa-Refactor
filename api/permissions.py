from rest_framework import permissions
from teams.models import TeamUser


class IsTeamMember(permissions.BasePermission):
    """
    팀 멤버만 접근 가능한 권한 클래스
    URL에서 team_id를 추출하여 사용자가 해당 팀의 멤버인지 확인
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # URL에서 team_id 추출 (여러 패턴 지원)
        team_id = None
        if 'team_id' in view.kwargs:
            team_id = view.kwargs['team_id']
        elif 'team_pk' in view.kwargs:
            team_id = view.kwargs['team_pk']
        elif hasattr(view, 'get_team_id'):
            team_id = view.get_team_id()

        if not team_id:
            return False

        # 팀 멤버십 확인
        is_member = TeamUser.objects.filter(
            team_id=team_id,
            user=request.user
        ).exists()

        return is_member


class IsTeamLeader(permissions.BasePermission):
    """
    팀 리더(호스트)만 접근 가능한 권한 클래스
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # URL에서 team_id 추출
        team_id = None
        if 'team_id' in view.kwargs:
            team_id = view.kwargs['team_id']
        elif 'team_pk' in view.kwargs:
            team_id = view.kwargs['team_pk']

        if not team_id:
            return False

        # 팀 리더(호스트) 확인
        from teams.models import Team
        try:
            team = Team.objects.get(id=team_id)
            return team.host == request.user
        except Team.DoesNotExist:
            return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    객체의 소유자는 수정/삭제 가능, 나머지는 읽기만 가능
    """

    def has_object_permission(self, request, view, obj):
        # 읽기 권한은 모든 인증된 사용자에게 허용
        if request.method in permissions.SAFE_METHODS:
            return True

        # 쓰기 권한은 객체의 소유자에게만 허용
        return obj.user == request.user