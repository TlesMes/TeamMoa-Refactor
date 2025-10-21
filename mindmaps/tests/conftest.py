"""
Mindmaps 앱 테스트를 위한 Fixture 정의
독립적인 factory 함수 기반 설계
"""
import pytest
from django.contrib.auth import get_user_model
from mindmaps.models import Mindmap, Node, NodeConnection, Comment
from mindmaps.services import MindmapService
from teams.models import Team, TeamUser

User = get_user_model()

# ================================
# 테스트 상수
# ================================

TEST_PASSWORD = 'test1234!'
TEST_NODE_X = 100
TEST_NODE_Y = 200
TEST_CANVAS_WIDTH = 1920
TEST_CANVAS_HEIGHT = 1080


# ================================
# Factory Functions (독립 함수)
# ================================

def create_mindmap(team, title='테스트 마인드맵'):
    """마인드맵 생성 헬퍼"""
    return Mindmap.objects.create(team=team, title=title)


def create_node(mindmap, title='노드', content='노드 내용', x=TEST_NODE_X, y=TEST_NODE_Y, **kwargs):
    """노드 생성 헬퍼 (좌표 포함)"""
    defaults = {
        'mindmap': mindmap,
        'title': title,
        'content': content,
        'posX': x,
        'posY': y
    }
    defaults.update(kwargs)
    return Node.objects.create(**defaults)


def create_connection(from_node, to_node):
    """연결선 생성 헬퍼"""
    return NodeConnection.objects.create(
        from_node=from_node,
        to_node=to_node,
        mindmap=from_node.mindmap
    )


def create_comment(node, user, text='테스트 댓글'):
    """댓글 생성 헬퍼"""
    return Comment.objects.create(
        comment=text,
        node=node,
        user=user
    )


# ================================
# 기본 Fixtures
# ================================

@pytest.fixture
def mindmap_service():
    """MindmapService 인스턴스"""
    return MindmapService()


@pytest.fixture
def host_teamuser(db):
    """호스트 사용자 + 팀"""
    user = User.objects.create_user(
        username='host',
        password=TEST_PASSWORD,
        nickname='호스트',
        email='host@test.com'
    )
    team = Team.objects.create(
        title='테스트팀',
        maxuser=10,
        currentuser=1,
        teampasswd='teampass123',
        invitecode='TESTCODE',
        introduction='테스트 팀입니다',
        host=user
    )
    return TeamUser.objects.create(user=user, team=team)


@pytest.fixture
def member_teamuser(host_teamuser):
    """일반 멤버"""
    user = User.objects.create_user(
        username='member',
        password=TEST_PASSWORD,
        nickname='멤버',
        email='member@test.com'
    )
    return TeamUser.objects.create(user=user, team=host_teamuser.team)


@pytest.fixture
def sample_mindmap(host_teamuser):
    """샘플 마인드맵"""
    return create_mindmap(host_teamuser.team, title='샘플 마인드맵')


@pytest.fixture
def sample_node(sample_mindmap):
    """샘플 노드 (좌표 포함)"""
    return create_node(sample_mindmap, title='샘플 노드', content='샘플 내용', x=100, y=200)


# ================================
# SSR View 테스트용 Client Fixtures
# (루트 conftest.py의 web_client를 확장)
# ================================

@pytest.fixture
def authenticated_host_client(host_teamuser):
    """호스트로 로그인된 웹 클라이언트"""
    from django.test import Client
    client = Client()
    client.force_login(host_teamuser.user)
    return client


@pytest.fixture
def authenticated_member_client(member_teamuser):
    """멤버로 로그인된 웹 클라이언트"""
    from django.test import Client
    client = Client()
    client.force_login(member_teamuser.user)
    return client
