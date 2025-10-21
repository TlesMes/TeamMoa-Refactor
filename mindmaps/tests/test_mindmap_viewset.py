"""
Mindmap ViewSet 테스트 (DRF API)
총 8개 테스트: Node ViewSet, Connection ViewSet

개선 사항:
- HTTP 상태 코드 구체적 검증
- JSON 응답 구조 검증
- 권한 검증 (다른 팀 사용자 차단)
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from mindmaps.models import Node, NodeConnection
from .conftest import create_node, create_connection, create_mindmap


@pytest.fixture
def api_client():
    """DRF API Client"""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, host_teamuser):
    """인증된 API Client (호스트)"""
    api_client.force_authenticate(user=host_teamuser.user)
    return api_client


@pytest.fixture
def member_client(api_client, member_teamuser):
    """인증된 API Client (멤버)"""
    api_client.force_authenticate(user=member_teamuser.user)
    return api_client


class TestNodeViewSet:
    """Node ViewSet 테스트 (5개)"""

    def test_node_create_via_api(self, authenticated_client, sample_mindmap, host_teamuser):
        """POST /api/v1/teams/{team_id}/mindmaps/{mindmap_id}/nodes/ - 노드 생성"""
        url = f'/api/v1/teams/{host_teamuser.team.id}/mindmaps/{sample_mindmap.id}/nodes/'
        data = {
            'posX': 150,
            'posY': 250,
            'title': 'API 노드',
            'content': 'API로 생성된 노드'
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert 'node' in response.data
        assert response.data['node']['title'] == 'API 노드'
        assert response.data['node']['posX'] == 150
        assert response.data['node']['posY'] == 250

        # DB 검증
        assert Node.objects.filter(title='API 노드', mindmap=sample_mindmap).exists()

    def test_node_update_position_via_api(self, authenticated_client, sample_node, host_teamuser):
        """PATCH /api/teams/{team_id}/mindmaps/{mindmap_id}/nodes/{node_id}/ - 노드 좌표 업데이트"""
        url = f'/api/v1/teams/{host_teamuser.team.id}/mindmaps/{sample_node.mindmap.id}/nodes/{sample_node.id}/'
        data = {
            'posX': 300,
            'posY': 400
        }

        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['node']['posX'] == 300
        assert response.data['node']['posY'] == 400

        # DB 검증
        sample_node.refresh_from_db()
        assert sample_node.posX == 300
        assert sample_node.posY == 400

    def test_node_delete_via_api(self, authenticated_client, sample_node, host_teamuser):
        """DELETE /api/teams/{team_id}/mindmaps/{mindmap_id}/nodes/{node_id}/ - 노드 삭제"""
        node_id = sample_node.id
        url = f'/api/v1/teams/{host_teamuser.team.id}/mindmaps/{sample_node.mindmap.id}/nodes/{node_id}/'

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert '삭제' in response.data['message']

        # DB 검증
        assert not Node.objects.filter(id=node_id).exists()

    def test_node_recommend_toggle_via_api(self, authenticated_client, sample_node, host_teamuser):
        """POST /api/teams/{team_id}/mindmaps/{mindmap_id}/nodes/{node_id}/recommend/ - 추천 토글"""
        url = f'/api/v1/teams/{host_teamuser.team.id}/mindmaps/{sample_node.mindmap.id}/nodes/{sample_node.id}/recommend/'

        # 추천 추가
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['action'] == 'added'
        assert response.data['recommendation_count'] == 1

        # 추천 취소
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['action'] == 'removed'
        assert response.data['recommendation_count'] == 0

    def test_node_create_unauthorized_team_returns_403(self, api_client, sample_mindmap, host_teamuser):
        """다른 팀 사용자가 노드 생성 시도 시 403"""
        from django.contrib.auth import get_user_model
        from teams.models import Team, TeamUser

        User = get_user_model()

        # 다른 팀의 사용자 생성
        other_user = User.objects.create_user(username='other', password='test1234!', email='other@test.com')
        other_team = Team.objects.create(
            title='다른팀',
            maxuser=5,
            currentuser=1,
            teampasswd='pass123',
            invitecode='OTHER',
            introduction='다른 팀',
            host=other_user
        )
        TeamUser.objects.create(user=other_user, team=other_team)

        # 다른 팀 사용자로 인증
        api_client.force_authenticate(user=other_user)

        # 현재 팀의 마인드맵에 노드 생성 시도
        url = f'/api/v1/teams/{host_teamuser.team.id}/mindmaps/{sample_mindmap.id}/nodes/'
        data = {
            'posX': 100,
            'posY': 100,
            'title': '불법 노드',
            'content': '권한 없음'
        }

        response = api_client.post(url, data, format='json')

        # 권한 없음 (IsTeamMember 권한 체크)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestConnectionViewSet:
    """Connection ViewSet 테스트 (3개)"""

    def test_connection_create_via_api(self, authenticated_client, sample_mindmap, host_teamuser):
        """POST /api/teams/{team_id}/mindmaps/{mindmap_id}/connections/ - 연결선 생성"""
        node1 = create_node(sample_mindmap, title='노드1')
        node2 = create_node(sample_mindmap, title='노드2')

        url = f'/api/v1/teams/{host_teamuser.team.id}/mindmaps/{sample_mindmap.id}/connections/'
        data = {
            'from_node_id': node1.id,
            'to_node_id': node2.id
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert 'connection' in response.data
        assert response.data['connection']['from_node_id'] == node1.id
        assert response.data['connection']['to_node_id'] == node2.id

        # DB 검증
        assert NodeConnection.objects.filter(
            from_node=node1,
            to_node=node2,
            mindmap=sample_mindmap
        ).exists()

    def test_connection_delete_via_api(self, authenticated_client, sample_mindmap, host_teamuser):
        """DELETE /api/teams/{team_id}/mindmaps/{mindmap_id}/connections/{connection_id}/ - 연결선 삭제"""
        node1 = create_node(sample_mindmap, title='노드1')
        node2 = create_node(sample_mindmap, title='노드2')
        connection = create_connection(node1, node2)

        connection_id = connection.id
        url = f'/api/v1/teams/{host_teamuser.team.id}/mindmaps/{sample_mindmap.id}/connections/{connection_id}/'

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert '삭제' in response.data['message']

        # DB 검증
        assert not NodeConnection.objects.filter(id=connection_id).exists()

    def test_connection_create_circular_returns_400(self, authenticated_client, sample_mindmap, host_teamuser):
        """순환 연결 생성 시도 시 400 (serializer validation)"""
        node = create_node(sample_mindmap, title='노드')

        url = f'/api/v1/teams/{host_teamuser.team.id}/mindmaps/{sample_mindmap.id}/connections/'
        data = {
            'from_node_id': node.id,
            'to_node_id': node.id  # 자기 자신과 연결
        }

        response = authenticated_client.post(url, data, format='json')

        # Serializer validation error
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # DRF는 serializer error를 다르게 포맷팅함
        assert 'non_field_errors' in response.data or '자기 자신' in str(response.data)

        # DB 검증 (연결선 생성되지 않음)
        assert not NodeConnection.objects.filter(from_node=node, to_node=node).exists()
