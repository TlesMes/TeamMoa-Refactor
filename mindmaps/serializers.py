from rest_framework import serializers
from .models import Mindmap, Node, NodeConnection, Comment
from teams.models import Team


class MindmapSerializer(serializers.ModelSerializer):
    """마인드맵 직렬화"""
    team_id = serializers.IntegerField(source='team.id', read_only=True)
    team_name = serializers.CharField(source='team.title', read_only=True)

    class Meta:
        model = Mindmap
        fields = ['id', 'title', 'team_id', 'team_name']
        read_only_fields = ['id', 'team_id', 'team_name']


class MindmapCreateSerializer(serializers.Serializer):
    """마인드맵 생성용 직렬화"""
    title = serializers.CharField(max_length=64, help_text="마인드맵 제목")

    def validate_title(self, value):
        """제목 검증"""
        if not value or not value.strip():
            raise serializers.ValidationError('마인드맵 제목을 입력해주세요.')

        if len(value.strip()) > 64:
            raise serializers.ValidationError('제목은 64자를 초과할 수 없습니다.')

        return value.strip()


class NodeSerializer(serializers.ModelSerializer):
    """노드 직렬화"""
    mindmap_id = serializers.IntegerField(source='mindmap.id', read_only=True)

    class Meta:
        model = Node
        fields = ['id', 'posX', 'posY', 'title', 'content', 'mindmap_id',
                  'recommended_users', 'recommendation_count']
        read_only_fields = ['id', 'mindmap_id', 'recommended_users', 'recommendation_count']


class NodeCreateSerializer(serializers.Serializer):
    """노드 생성용 직렬화"""
    posX = serializers.IntegerField(min_value=0, help_text="X 좌표")
    posY = serializers.IntegerField(min_value=0, help_text="Y 좌표")
    title = serializers.CharField(max_length=64, help_text="노드 제목")
    content = serializers.CharField(help_text="노드 내용")
    parent = serializers.CharField(max_length=64, required=False, allow_blank=True,
                                   help_text="부모 노드 제목 (선택)")

    def validate_title(self, value):
        """제목 검증"""
        if not value or not value.strip():
            raise serializers.ValidationError('노드 제목을 입력해주세요.')
        return value.strip()

    def validate_content(self, value):
        """내용 검증"""
        if not value or not value.strip():
            raise serializers.ValidationError('노드 내용을 입력해주세요.')
        return value.strip()


class NodeUpdateSerializer(serializers.Serializer):
    """노드 업데이트용 직렬화 (위치 이동)"""
    posX = serializers.IntegerField(min_value=0, required=False)
    posY = serializers.IntegerField(min_value=0, required=False)
    title = serializers.CharField(max_length=64, required=False)
    content = serializers.CharField(required=False)


class NodeConnectionSerializer(serializers.ModelSerializer):
    """노드 연결선 직렬화"""
    from_node_id = serializers.IntegerField(source='from_node.id', read_only=True)
    to_node_id = serializers.IntegerField(source='to_node.id', read_only=True)
    from_node_title = serializers.CharField(source='from_node.title', read_only=True)
    to_node_title = serializers.CharField(source='to_node.title', read_only=True)

    class Meta:
        model = NodeConnection
        fields = ['id', 'from_node_id', 'to_node_id', 'from_node_title', 'to_node_title']
        read_only_fields = ['id', 'from_node_id', 'to_node_id', 'from_node_title', 'to_node_title']


class NodeConnectionCreateSerializer(serializers.Serializer):
    """노드 연결 생성용 직렬화"""
    from_node_id = serializers.IntegerField(help_text="시작 노드 ID")
    to_node_id = serializers.IntegerField(help_text="끝 노드 ID")

    def validate(self, data):
        """자기 자신과 연결하는지 검증"""
        if data['from_node_id'] == data['to_node_id']:
            raise serializers.ValidationError('노드는 자기 자신과 연결할 수 없습니다.')
        return data


class CommentSerializer(serializers.ModelSerializer):
    """댓글 직렬화"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    nickname = serializers.CharField(source='user.nickname', read_only=True)
    node_id = serializers.IntegerField(source='node.id', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'comment', 'node_id', 'user_id', 'username', 'nickname', 'commented_at']
        read_only_fields = ['id', 'node_id', 'user_id', 'username', 'nickname', 'commented_at']


class CommentCreateSerializer(serializers.Serializer):
    """댓글 생성용 직렬화"""
    comment = serializers.CharField(help_text="댓글 내용")

    def validate_comment(self, value):
        """댓글 검증"""
        if not value or not value.strip():
            raise serializers.ValidationError('댓글 내용을 입력해주세요.')
        return value.strip()


class NodeRecommendSerializer(serializers.Serializer):
    """노드 추천 토글용 직렬화"""
    # 추천 토글은 추가 데이터가 필요 없음
    pass
