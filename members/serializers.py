from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Todo
from teams.models import Team, TeamUser

User = get_user_model()


class TodoSerializer(serializers.ModelSerializer):
    """기본 TODO 직렬화"""
    assignee_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Todo
        fields = ['id', 'content', 'status', 'status_display', 'assignee',
                 'assignee_name', 'order', 'created_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'completed_at', 'assignee_name', 'status_display']

    def get_assignee_name(self, obj):
        """할당자 이름 반환"""
        if obj.assignee:
            return obj.assignee.user.nickname or obj.assignee.user.username
        return None

    def get_status_display(self, obj):
        """상태 표시명 반환"""
        status_map = {
            'todo': 'To Do',
            'in_progress': 'In Progress',
            'done': 'Done'
        }
        return status_map.get(obj.status, obj.status)


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


class TodoMoveSerializer(serializers.Serializer):
    """TODO 이동 액션용 직렬화"""
    new_status = serializers.ChoiceField(choices=Todo.STATUS_CHOICES)
    new_order = serializers.IntegerField(min_value=0, default=0)

    def validate_new_status(self, value):
        """유효한 상태인지 검증"""
        valid_statuses = [choice[0] for choice in Todo.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError('유효하지 않은 상태입니다.')
        return value


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