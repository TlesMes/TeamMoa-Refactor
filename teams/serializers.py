from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Team, TeamUser, Milestone
from datetime import date

User = get_user_model()


class TeamListSerializer(serializers.ModelSerializer):
    """팀 목록 조회용 직렬화"""
    host_username = serializers.CharField(source='host.username', read_only=True)
    host_nickname = serializers.CharField(source='host.nickname', read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'title', 'introduction', 'maxuser', 'currentuser',
                 'host_username', 'host_nickname']
        read_only_fields = ['id', 'currentuser', 'host_username', 'host_nickname']


class TeamDetailSerializer(serializers.ModelSerializer):
    """팀 상세 조회용 직렬화 (초대코드 포함)"""
    host_username = serializers.CharField(source='host.username', read_only=True)
    host_nickname = serializers.CharField(source='host.nickname', read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'title', 'introduction', 'maxuser', 'currentuser',
                 'invitecode', 'host', 'host_username', 'host_nickname']
        read_only_fields = ['id', 'invitecode', 'currentuser', 'host', 'host_username', 'host_nickname']


class TeamCreateSerializer(serializers.Serializer):
    """팀 생성용 직렬화"""
    title = serializers.CharField(max_length=200)
    maxuser = serializers.IntegerField(min_value=1, max_value=100)
    teampasswd = serializers.CharField(max_length=100)
    introduction = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate_title(self, value):
        """제목 검증"""
        if not value or not value.strip():
            raise serializers.ValidationError('팀명을 입력해주세요.')
        return value.strip()

    def validate_teampasswd(self, value):
        """비밀번호 검증"""
        if not value or not value.strip():
            raise serializers.ValidationError('팀 비밀번호를 입력해주세요.')
        return value.strip()


class TeamUpdateSerializer(serializers.Serializer):
    """팀 정보 수정용 직렬화"""
    title = serializers.CharField(max_length=200, required=False)
    introduction = serializers.CharField(max_length=500, required=False, allow_blank=True)
    maxuser = serializers.IntegerField(min_value=1, max_value=100, required=False)

    def validate_title(self, value):
        """제목 검증"""
        if value is not None and (not value or not value.strip()):
            raise serializers.ValidationError('팀명을 입력해주세요.')
        return value.strip() if value else value

    def validate_maxuser(self, value):
        """최대 인원 검증"""
        if value and self.instance:
            current_members = self.instance.get_current_member_count()
            if value < current_members:
                raise serializers.ValidationError(
                    f'최대 인원은 현재 인원({current_members}명)보다 작을 수 없습니다.'
                )
        return value


class TeamJoinVerifySerializer(serializers.Serializer):
    """팀 코드 검증용 직렬화"""
    invitecode = serializers.CharField(max_length=50)

    def validate_invitecode(self, value):
        """초대코드 검증"""
        if not value or not value.strip():
            raise serializers.ValidationError('팀 코드를 입력해주세요.')
        return value.strip()


class TeamJoinSerializer(serializers.Serializer):
    """팀 가입용 직렬화"""
    teampasswd = serializers.CharField(max_length=100)

    def validate_teampasswd(self, value):
        """비밀번호 검증"""
        if not value or not value.strip():
            raise serializers.ValidationError('팀 비밀번호를 입력해주세요.')
        return value.strip()


class TeamSerializer(serializers.ModelSerializer):
    """팀 기본 정보 직렬화 (하위 호환성 유지)"""
    host_username = serializers.CharField(source='host.username', read_only=True)
    host_nickname = serializers.CharField(source='host.nickname', read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'title', 'introduction', 'maxuser', 'currentuser',
                 'invitecode', 'host', 'host_username', 'host_nickname']
        read_only_fields = ['id', 'invitecode', 'currentuser', 'host_username', 'host_nickname']


class MilestoneSerializer(serializers.ModelSerializer):
    """마일스톤 기본 직렬화"""
    status = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Milestone
        fields = ['id', 'team', 'title', 'description', 'startdate', 'enddate',
                 'is_completed', 'completed_date', 'progress_percentage', 'priority',
                 'priority_display', 'status', 'status_display']
        read_only_fields = ['id', 'team', 'is_completed', 'completed_date',
                           'status', 'status_display', 'priority_display']

    def get_status(self, obj):
        """현재 상태 반환"""
        return obj.get_status(date.today())

    def get_status_display(self, obj):
        """상태 표시명 반환"""
        return obj.status_display


class MilestoneCreateSerializer(serializers.ModelSerializer):
    """마일스톤 생성용 직렬화"""

    class Meta:
        model = Milestone
        fields = ['title', 'description', 'startdate', 'enddate', 'priority']

    def validate_title(self, value):
        """제목 검증"""
        if not value or not value.strip():
            raise serializers.ValidationError('마일스톤 제목을 입력해주세요.')

        if len(value.strip()) > 100:
            raise serializers.ValidationError('마일스톤 제목은 100자를 초과할 수 없습니다.')

        return value.strip()

    def validate(self, data):
        """날짜 교차 검증"""
        startdate = data.get('startdate')
        enddate = data.get('enddate')

        if startdate and enddate:
            if startdate > enddate:
                raise serializers.ValidationError({
                    'enddate': '종료일은 시작일보다 이후여야 합니다.'
                })

        return data


class MilestoneUpdateSerializer(serializers.Serializer):
    """마일스톤 업데이트용 직렬화 (드래그앤드롭, 진행률 변경)"""
    startdate = serializers.DateField(required=False)
    enddate = serializers.DateField(required=False)
    progress_percentage = serializers.IntegerField(required=False, min_value=0, max_value=100)

    def validate(self, data):
        """날짜 교차 검증"""
        startdate = data.get('startdate')
        enddate = data.get('enddate')

        # 둘 다 제공된 경우에만 검증
        if startdate and enddate:
            if startdate > enddate:
                raise serializers.ValidationError({
                    'enddate': '종료일은 시작일보다 이후여야 합니다.'
                })

        # 하나만 제공된 경우, 인스턴스의 다른 날짜와 비교
        if self.instance:
            if startdate and not enddate:
                if startdate > self.instance.enddate:
                    raise serializers.ValidationError({
                        'startdate': f'시작일은 종료일({self.instance.enddate})보다 이전이어야 합니다.'
                    })

            if enddate and not startdate:
                if enddate < self.instance.startdate:
                    raise serializers.ValidationError({
                        'enddate': f'종료일은 시작일({self.instance.startdate})보다 이후여야 합니다.'
                    })

        return data


class TeamMemberSerializer(serializers.ModelSerializer):
    """팀 멤버 정보 직렬화"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    nickname = serializers.CharField(source='user.nickname', read_only=True)
    is_host = serializers.SerializerMethodField()

    class Meta:
        model = TeamUser
        fields = ['id', 'user_id', 'username', 'nickname', 'is_host']
        read_only_fields = ['id', 'user_id', 'username', 'nickname', 'is_host']

    def get_is_host(self, obj):
        """팀장 여부 반환"""
        return obj.team.host == obj.user