"""
MindmapService 비즈니스 로직 테스트
총 16개 테스트: Mindmap CRUD, Node CRUD, Connection CRUD, 댓글, 권한

개선 사항:
- DB 상태 기반 검증 (서비스 리턴값 의존도 감소)
- 구체적 예외 타입 검증 (Exception → ValueError/DuplicateTitleError)
- 부정 시나리오 추가 (다른 팀 사용자, 권한 없는 접근)
"""
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from mindmaps.models import Mindmap, Node, NodeConnection, Comment
from mindmaps.services import MindmapService, DuplicateTitleError
from .conftest import create_mindmap, create_node, create_connection, create_comment

User = get_user_model()


class TestMindmapCRUD:
    """마인드맵 CRUD 테스트 (4개)"""

    def test_create_mindmap_success(self, mindmap_service, host_teamuser, db):
        """마인드맵 생성 성공"""
        mindmap = mindmap_service.create_mindmap(
            team_id=host_teamuser.team.id,
            title='새 마인드맵',
            creator=host_teamuser.user
        )

        assert mindmap.title == '새 마인드맵'
        assert mindmap.team == host_teamuser.team
        assert Mindmap.objects.filter(id=mindmap.id).exists()

    def test_create_mindmap_duplicate_title_raises_error(self, mindmap_service, host_teamuser, db):
        """중복 제목으로 마인드맵 생성 시 에러"""
        # 첫 번째 생성
        mindmap_service.create_mindmap(
            team_id=host_teamuser.team.id,
            title='중복 제목',
            creator=host_teamuser.user
        )

        # 같은 제목으로 두 번째 생성 시도
        with pytest.raises(DuplicateTitleError, match='이미 사용중인 이름입니다'):
            mindmap_service.create_mindmap(
                team_id=host_teamuser.team.id,
                title='중복 제목',
                creator=host_teamuser.user
            )

    def test_get_mindmap_with_nodes_and_connections(self, mindmap_service, sample_mindmap, db):
        """노드/연결선 포함 마인드맵 조회"""
        # 노드 2개 생성
        node1 = create_node(sample_mindmap, title='노드1', x=100, y=100)
        node2 = create_node(sample_mindmap, title='노드2', x=200, y=200)

        # 연결선 생성
        connection = create_connection(node1, node2)

        # 조회
        result = mindmap_service.get_mindmap_with_nodes(sample_mindmap.id)

        assert result['mindmap'].id == sample_mindmap.id
        assert result['nodes'].count() == 2
        assert result['lines'].count() == 1
        assert list(result['nodes'].values_list('title', flat=True)) == ['노드1', '노드2']

    def test_delete_mindmap_cascade_deletes_nodes_and_connections(self, mindmap_service, sample_mindmap, host_teamuser, db):
        """마인드맵 삭제 시 노드/연결선 cascade 삭제 (DB 상태 검증)"""
        # 노드 2개 생성
        node1 = create_node(sample_mindmap, title='노드1')
        node2 = create_node(sample_mindmap, title='노드2')

        # 연결선 생성
        create_connection(node1, node2)

        mindmap_id = sample_mindmap.id
        node1_id = node1.id
        node2_id = node2.id

        # 마인드맵 삭제
        mindmap_service.delete_mindmap(mindmap_id, host_teamuser.user)

        # DB 상태 검증 (서비스 리턴값에 의존하지 않음)
        assert not Mindmap.objects.filter(id=mindmap_id).exists()
        assert not Node.objects.filter(id=node1_id).exists()
        assert not Node.objects.filter(id=node2_id).exists()
        assert not NodeConnection.objects.filter(mindmap_id=mindmap_id).exists()


class TestNodeCRUD:
    """노드 CRUD 테스트 (5개)"""

    def test_create_node_with_coordinates(self, mindmap_service, sample_mindmap, host_teamuser, db):
        """노드 생성 (좌표 저장 확인)"""
        node_data = {
            'posX': 150,
            'posY': 300,
            'title': '새 노드',
            'content': '노드 내용'
        }

        node = mindmap_service.create_node(
            mindmap_id=sample_mindmap.id,
            node_data=node_data,
            creator=host_teamuser.user
        )

        assert node.posX == 150
        assert node.posY == 300
        assert node.title == '새 노드'
        assert node.content == '노드 내용'
        assert node.mindmap == sample_mindmap

    def test_update_node_position(self, sample_node, db):
        """노드 좌표 업데이트"""
        # 초기 좌표 확인
        assert sample_node.posX == 100
        assert sample_node.posY == 200

        # 좌표 업데이트
        sample_node.posX = 250
        sample_node.posY = 350
        sample_node.save()

        # 새로고침 후 확인
        sample_node.refresh_from_db()
        assert sample_node.posX == 250
        assert sample_node.posY == 350

    def test_update_node_content(self, sample_node, db):
        """노드 내용 수정"""
        # 초기 내용 확인
        assert sample_node.title == '샘플 노드'
        assert sample_node.content == '샘플 내용'

        # 내용 수정
        sample_node.title = '수정된 제목'
        sample_node.content = '수정된 내용'
        sample_node.save()

        # 새로고침 후 확인
        sample_node.refresh_from_db()
        assert sample_node.title == '수정된 제목'
        assert sample_node.content == '수정된 내용'

    def test_delete_node_removes_connections(self, mindmap_service, sample_mindmap, host_teamuser, db):
        """노드 삭제 시 연결선 제거 (DB 상태 검증)"""
        # 노드 3개 생성
        node1 = create_node(sample_mindmap, title='노드1')
        node2 = create_node(sample_mindmap, title='노드2')
        node3 = create_node(sample_mindmap, title='노드3')

        # 연결선 생성 (node2를 중심으로)
        conn1 = create_connection(node1, node2)
        conn2 = create_connection(node2, node3)

        node2_id = node2.id
        conn1_id = conn1.id
        conn2_id = conn2.id

        # node2 삭제
        mindmap_service.delete_node(node2_id, host_teamuser.user)

        # DB 상태 검증
        assert not Node.objects.filter(id=node2_id).exists()
        # 연결선도 함께 삭제되었는지 확인
        assert not NodeConnection.objects.filter(id=conn1_id).exists()
        assert not NodeConnection.objects.filter(id=conn2_id).exists()
        # node1, node3는 유지
        assert Node.objects.filter(id=node1.id).exists()
        assert Node.objects.filter(id=node3.id).exists()

    def test_create_node_invalid_mindmap_raises_error(self, mindmap_service, host_teamuser, db):
        """잘못된 mindmap_id로 노드 생성 시 Http404"""
        from django.http import Http404

        node_data = {
            'posX': 100,
            'posY': 100,
            'title': '노드',
            'content': '내용'
        }

        with pytest.raises(Http404):
            mindmap_service.create_node(
                mindmap_id=99999,
                node_data=node_data,
                creator=host_teamuser.user
            )


class TestConnectionCRUD:
    """연결선 CRUD 테스트 (3개)"""

    def test_create_connection_between_nodes(self, mindmap_service, sample_mindmap, db):
        """연결선 생성"""
        node1 = create_node(sample_mindmap, title='노드1')
        node2 = create_node(sample_mindmap, title='노드2')

        connection = mindmap_service.create_node_connection(
            from_node_id=node1.id,
            to_node_id=node2.id,
            mindmap_id=sample_mindmap.id
        )

        assert connection.from_node == node1
        assert connection.to_node == node2
        assert connection.mindmap == sample_mindmap
        assert NodeConnection.objects.filter(id=connection.id).exists()

    def test_prevent_circular_connection(self, mindmap_service, sample_node, db):
        """순환 연결 방지 (from_node == to_node)"""
        with pytest.raises(ValueError, match='노드는 자기 자신과 연결할 수 없습니다'):
            mindmap_service.create_node_connection(
                from_node_id=sample_node.id,
                to_node_id=sample_node.id,
                mindmap_id=sample_node.mindmap.id
            )

    def test_delete_connection_success(self, mindmap_service, sample_mindmap, host_teamuser, db):
        """연결선 삭제 (DB 상태 검증)"""
        node1 = create_node(sample_mindmap, title='노드1')
        node2 = create_node(sample_mindmap, title='노드2')
        connection = create_connection(node1, node2)

        connection_id = connection.id

        mindmap_service.delete_node_connection(connection_id, host_teamuser.user)

        # DB 상태 검증
        assert not NodeConnection.objects.filter(id=connection_id).exists()
        # 노드는 유지
        assert Node.objects.filter(id=node1.id).exists()
        assert Node.objects.filter(id=node2.id).exists()


class TestCommentAndPermission:
    """댓글 및 권한 테스트 (4개)"""

    def test_add_comment_to_node(self, mindmap_service, sample_node, host_teamuser, db):
        """노드 댓글 작성 (DB 상태 검증)"""
        comment = mindmap_service.create_comment(
            node_id=sample_node.id,
            comment_text='테스트 댓글입니다',
            user=host_teamuser.user
        )

        # DB 상태 검증
        assert comment.comment == '테스트 댓글입니다'
        assert comment.node == sample_node
        assert comment.user == host_teamuser.user
        assert Comment.objects.filter(node=sample_node, user=host_teamuser.user).exists()

    def test_create_comment_empty_text_raises_error(self, mindmap_service, sample_node, host_teamuser):
        """빈 댓글 작성 시 ValueError"""
        with pytest.raises(ValueError, match='댓글 내용을 입력해주세요'):
            mindmap_service.create_comment(
                node_id=sample_node.id,
                comment_text='   ',
                user=host_teamuser.user
            )

    def test_get_node_with_comments(self, mindmap_service, sample_node, host_teamuser, member_teamuser):
        """노드 댓글 조회 (여러 사용자)"""
        # 호스트 댓글
        create_comment(sample_node, host_teamuser.user, '호스트 댓글')
        # 멤버 댓글
        create_comment(sample_node, member_teamuser.user, '멤버 댓글')

        result = mindmap_service.get_node_with_comments(sample_node.id)

        assert result['node'].id == sample_node.id
        assert result['comments'].count() == 2
        comments_text = list(result['comments'].values_list('comment', flat=True))
        assert '호스트 댓글' in comments_text
        assert '멤버 댓글' in comments_text

    def test_check_team_membership_permission(self, host_teamuser, member_teamuser):
        """팀 멤버십 권한 검증 (부정 시나리오 포함)"""
        # 호스트는 팀 멤버
        assert host_teamuser.team.teamuser_set.filter(user=host_teamuser.user).exists()

        # 일반 멤버도 팀 멤버
        assert member_teamuser.team.teamuser_set.filter(user=member_teamuser.user).exists()

        # 팀에 속하지 않은 외부 사용자
        outsider = User.objects.create_user(username='outsider', password='test1234!')
        assert not host_teamuser.team.teamuser_set.filter(user=outsider).exists()

        # 다른 팀의 사용자
        from teams.models import Team, TeamUser
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

        # 다른 팀의 사용자는 현재 팀의 멤버가 아님
        assert not host_teamuser.team.teamuser_set.filter(user=other_user).exists()
