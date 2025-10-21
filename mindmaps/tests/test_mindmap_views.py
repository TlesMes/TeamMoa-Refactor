"""
Mindmap SSR Views 테스트
총 6개 테스트: 목록, 생성, 삭제, 에디터, 노드 상세

개선 사항:
- 템플릿 렌더링 검증
- 리다이렉트 검증
- Django messages 검증
- 권한 검증 (호스트 전용 삭제)
"""
import pytest
from django.urls import reverse
from django.contrib.messages import get_messages
from mindmaps.models import Mindmap, Node, Comment
from .conftest import create_mindmap, create_node, create_comment


class TestMindmapListAndCreate:
    """마인드맵 목록 및 생성 테스트 (3개)"""

    def test_mindmap_list_view_shows_team_mindmaps(self, authenticated_host_client, host_teamuser):
        """GET /teams/{id}/mindmaps/ - 팀 마인드맵 목록 표시"""
        # 마인드맵 2개 생성
        create_mindmap(host_teamuser.team, title='마인드맵1')
        create_mindmap(host_teamuser.team, title='마인드맵2')

        url = reverse('mindmaps:mindmap_list_page', kwargs={'pk': host_teamuser.team.id})
        response = authenticated_host_client.get(url)

        assert response.status_code == 200
        assert 'mindmaps/mindmap_list_page.html' in [t.name for t in response.templates]
        assert '마인드맵1' in response.content.decode()
        assert '마인드맵2' in response.content.decode()

    def test_mindmap_create_view_redirects_on_success(self, authenticated_host_client, host_teamuser):
        """POST /teams/{id}/mindmaps/create/ - 마인드맵 생성 후 리다이렉트"""
        url = reverse('mindmaps:mindmap_create', kwargs={'pk': host_teamuser.team.id})
        data = {'title': '새 마인드맵'}

        response = authenticated_host_client.post(url, data)

        # 리다이렉트 검증
        assert response.status_code == 302
        assert response.url == reverse('mindmaps:mindmap_list_page', kwargs={'pk': host_teamuser.team.id})

        # DB 검증
        assert Mindmap.objects.filter(team=host_teamuser.team, title='새 마인드맵').exists()

        # Messages 검증
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert '성공적으로 생성' in str(messages[0])

    def test_mindmap_create_duplicate_title_shows_error(self, authenticated_host_client, host_teamuser):
        """POST /teams/{id}/mindmaps/create/ - 중복 제목 시 에러 메시지"""
        # 기존 마인드맵 생성
        create_mindmap(host_teamuser.team, title='중복 제목')

        url = reverse('mindmaps:mindmap_create', kwargs={'pk': host_teamuser.team.id})
        data = {'title': '중복 제목'}

        response = authenticated_host_client.post(url, data)

        # 리다이렉트
        assert response.status_code == 302

        # 에러 메시지 검증
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert '이미 사용중인 이름' in str(messages[0])


class TestMindmapDelete:
    """마인드맵 삭제 테스트 (1개)"""

    def test_mindmap_delete_view_host_only(self, authenticated_host_client, authenticated_member_client, host_teamuser):
        """POST /teams/{id}/mindmaps/{id}/delete/ - 호스트만 삭제 가능"""
        mindmap = create_mindmap(host_teamuser.team, title='삭제할 마인드맵')
        url = reverse('mindmaps:mindmap_delete', kwargs={'pk': host_teamuser.team.id, 'mindmap_id': mindmap.id})

        # 일반 멤버로 시도 (TeamHostRequiredMixin이 차단)
        response = authenticated_member_client.post(url)

        # 권한 없음 (mixin이 리다이렉트 또는 403)
        assert response.status_code in [302, 403]
        # DB 검증 (삭제 안 됨)
        assert Mindmap.objects.filter(id=mindmap.id).exists()
        
        # 호스트로 시도
        response = authenticated_host_client.post(url)

        # 성공 리다이렉트
        assert response.status_code == 302
        # DB 검증 (삭제됨)
        assert not Mindmap.objects.filter(id=mindmap.id).exists()


class TestMindmapEditor:
    """마인드맵 에디터 테스트 (1개)"""

    def test_mindmap_editor_view_renders_canvas(self, authenticated_host_client, host_teamuser):
        """GET /teams/{id}/mindmaps/{id}/ - 에디터 페이지 렌더링"""
        mindmap = create_mindmap(host_teamuser.team, title='편집할 마인드맵')
        # 노드 추가
        create_node(mindmap, title='테스트 노드', x=100, y=200)

        url = reverse('mindmaps:mindmap_detail_page', kwargs={'pk': host_teamuser.team.id, 'mindmap_id': mindmap.id})
        response = authenticated_host_client.get(url)

        assert response.status_code == 200
        assert 'mindmaps/mindmap_detail_page.html' in [t.name for t in response.templates]
        assert 'nodes' in response.context
        assert response.context['nodes'].count() == 1


class TestNodeDetail:
    """노드 상세 페이지 테스트 (2개)"""

    def test_node_detail_view_shows_comments(self, authenticated_host_client, host_teamuser, member_teamuser):
        """GET /teams/{id}/nodes/{id}/ - 노드 상세 및 댓글 표시"""
        mindmap = create_mindmap(host_teamuser.team, title='마인드맵')
        node = create_node(mindmap, title='노드', content='노드 내용')

        # 댓글 추가
        create_comment(node, host_teamuser.user, '호스트 댓글')
        create_comment(node, member_teamuser.user, '멤버 댓글')

        url = reverse('mindmaps:node_detail_page', kwargs={'pk': host_teamuser.team.id, 'node_id': node.id})
        response = authenticated_host_client.get(url)

        assert response.status_code == 200
        assert 'mindmaps/node_detail_page.html' in [t.name for t in response.templates]
        assert 'comments' in response.context
        assert response.context['comments'].count() == 2

        content = response.content.decode()
        assert '호스트 댓글' in content
        assert '멤버 댓글' in content

    def test_node_detail_add_comment_redirects(self, authenticated_host_client, host_teamuser):
        """POST /teams/{id}/nodes/{id}/ - 댓글 작성 후 리다이렉트"""
        mindmap = create_mindmap(host_teamuser.team, title='마인드맵')
        node = create_node(mindmap, title='노드')

        url = reverse('mindmaps:node_detail_page', kwargs={'pk': host_teamuser.team.id, 'node_id': node.id})
        data = {'comment': '새 댓글입니다'}

        response = authenticated_host_client.post(url, data)

        # 리다이렉트 검증
        assert response.status_code == 302
        assert response.url == url

        # DB 검증
        assert Comment.objects.filter(node=node, user=host_teamuser.user, comment='새 댓글입니다').exists()

        # Messages 검증
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert '성공적으로 등록' in str(messages[0])
