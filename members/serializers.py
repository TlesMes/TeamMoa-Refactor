from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Todo
from teams.models import Team, TeamUser

User = get_user_model()


class TodoSerializer(serializers.ModelSerializer):
    """기본 TODO 직렬화"""
    assignee_name = serializers.SerializerMethodField()
    assignee_id = serializers.SerializerMethodField()

    class Meta:
        model = Todo
        fields = ['id', 'content', 'is_completed', 'assignee_id',
                 'assignee_name', 'order', 'created_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'completed_at', 'assignee_name', 'assignee_id']

    def get_assignee_name(self, obj):
        """할당자 이름 반환"""
        if obj.assignee:
            return obj.assignee.user.nickname or obj.assignee.user.username
        return None

    def get_assignee_id(self, obj):
        """할당자 ID 반환 (TeamUser.id)"""
        return obj.assignee.id if obj.assignee else None


class TodoCreateSerializer(serializers.ModelSerializer):
    """TODO 생성용 직렬화"""

    class Meta:
        model = Todo
        fields = ['content']

    def validate_content(self, value):
        """내용 검증"""
        if not value or not value.strip():
            raise serializers.ValidationError('할 일 내용을 입력해주세요.')

        if len(value.strip()) > 200:
            raise serializers.ValidationError('할 일 내용은 200자를 초과할 수 없습니다.')

        return value.strip()


class TodoDragMoveSerializer(serializers.Serializer):
    """TODO 드래그 이동용 직렬화"""
    target_board = serializers.ChoiceField(choices=['todo', 'done', 'member'])
    target_member_id = serializers.IntegerField(required=False, allow_null=True)
    new_order = serializers.IntegerField(min_value=0, default=0)

    def validate(self, data):
        """멤버 보드로 이동 시 target_member_id 필수"""
        if data['target_board'] == 'member' and not data.get('target_member_id'):
            raise serializers.ValidationError('멤버 보드로 이동 시 멤버 ID가 필요합니다.')

        # 멤버 유효성 검증
        if data.get('target_member_id'):
            team = self.context.get('team')
            try:
                TeamUser.objects.get(id=data['target_member_id'], team=team)
            except TeamUser.DoesNotExist:
                raise serializers.ValidationError('유효하지 않은 팀 멤버입니다.')

        return data


class TodoAssignSerializer(serializers.Serializer):
    """TODO 할당 액션용 직렬화"""
    member_id = serializers.IntegerField()

    def validate_member_id(self, value):
        """유효한 팀 멤버인지 검증"""
        # 팀 정보는 context에서 받아옴
        team = self.context.get('team')
        if not team:
            raise serializers.ValidationError('팀 정보가 필요합니다.')

        try:
            member = TeamUser.objects.get(id=value, team=team)
            self.context['validated_member'] = member
            return value
        except TeamUser.DoesNotExist:
            raise serializers.ValidationError('유효하지 않은 팀 멤버입니다.')


class TodoCompleteSerializer(serializers.Serializer):
    """TODO 완료 토글용 직렬화"""
    # 완료 토글은 추가 데이터가 필요 없음
    pass


class TodoReturnSerializer(serializers.Serializer):
    """TODO 보드 복귀용 직렬화"""
    # 보드 복귀는 추가 데이터가 필요 없음
    pass


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