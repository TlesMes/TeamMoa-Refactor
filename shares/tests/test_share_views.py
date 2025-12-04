"""
Shares SSR 뷰 테스트 (13개)

테스트 구성:
- TestPostListAndRetrieval: 3개 - 목록, 상세, 페이지네이션
- TestSearchUI: 3개 - 검색 필터링 (parametrize)
- TestPostWriteAndEdit: 3개 - 작성, 수정
- TestDeleteAndPermissions: 4개 - 삭제, 권한 체크

페이지:
- post_list: 게시판 목록
- post_detail: 게시글 상세
- post_write/edit: 작성/수정
"""
import pytest
from django.urls import reverse
from django.test import Client


@pytest.fixture
def client_with_login(client, user):
    """로그인된 클라이언트"""
    client.force_login(user)
    return client


class TestPostListAndRetrieval:
    """목록 및 조회 테스트 (3개)"""

    def test_post_list_page_renders(self, client_with_login, team, sample_post):
        """게시판 목록 페이지 렌더링"""
        url = reverse('shares:post_list', kwargs={'pk': team.id})
        response = client_with_login.get(url)

        assert response.status_code == 200
        assert 'post_list' in response.context
        assert sample_post in response.context['post_list']

    def test_post_detail_page_renders(self, client_with_login, team, sample_post):
        """게시물 상세 페이지 렌더링"""
        url = reverse('shares:post_detail', kwargs={'pk': team.id, 'post_id': sample_post.id})
        response = client_with_login.get(url)

        assert response.status_code == 200
        assert 'post' in response.context
        assert response.context['post'] == sample_post

    def test_pagination_works(self, client_with_login, team, multiple_posts):
        """페이지네이션 동작 확인 (11개 게시물 → 2페이지)"""
        # 1페이지 (10개)
        url = reverse('shares:post_list', kwargs={'pk': team.id})
        response = client_with_login.get(url, {'page': 1})

        assert response.status_code == 200
        assert len(response.context['post_list']) == 10
        assert response.context['is_paginated'] is True

        # 2페이지 (1개)
        response = client_with_login.get(url, {'page': 2})
        assert len(response.context['post_list']) == 1


class TestSearchUI:
    """검색 UI 테스트 (1개, parametrize 활용)"""

    @pytest.mark.parametrize("search_query,expected_count", [
        ('호스트 게시물 1', 1),  # 특정 제목 검색
        ('멤버', 5),            # 제목에 '멤버' 포함
        ('내용 2', 2),          # 내용에 '2' 포함 (호스트 2, 멤버 2)
    ])
    def test_post_list_search_filtering(
        self,
        client_with_login,
        team,
        multiple_posts,
        search_query,
        expected_count
    ):
        """검색 필터링 통합 테스트"""
        url = reverse('shares:post_list', kwargs={'pk': team.id})
        response = client_with_login.get(url, {'q': search_query, 'type': 'all'})

        assert response.status_code == 200
        assert len(response.context['post_list']) == expected_count
        assert response.context['q'] == search_query


class TestPostWriteAndEdit:
    """게시물 작성/수정 테스트 (4개)"""

    def test_post_write_page_renders(self, client_with_login, team):
        """작성 페이지 렌더링 (GET)"""
        url = reverse('shares:post_write', kwargs={'pk': team.id})
        response = client_with_login.get(url)

        assert response.status_code == 200
        assert 'form' in response.context

    def test_post_create_with_file(self, client_with_login, team, small_test_file):
        """게시물 생성 (POST, 파일 포함)"""
        url = reverse('shares:post_write', kwargs={'pk': team.id})
        data = {
            'title': '새 게시물',
            'article': '새 내용',
            'upload_files': small_test_file
        }

        response = client_with_login.post(url, data)

        # 성공 시 리다이렉트
        assert response.status_code in [200, 302]

        # 게시물이 생성되었는지 확인
        from shares.models import Post
        assert Post.objects.filter(title='새 게시물').exists()

    def test_post_edit_page_renders(self, client_with_login, team, sample_post):
        """수정 페이지 렌더링 (GET)"""
        url = reverse('shares:post_edit', kwargs={'pk': team.id, 'post_id': sample_post.id})
        response = client_with_login.get(url)

        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['post'] == sample_post

    def test_post_update(self, client_with_login, team, sample_post):
        """게시물 수정 (POST)"""
        url = reverse('shares:post_edit', kwargs={'pk': team.id, 'post_id': sample_post.id})
        data = {
            'title': '수정된 제목',
            'article': '수정된 내용'
        }

        response = client_with_login.post(url, data)

        # 성공 시 리다이렉트
        assert response.status_code in [200, 302]

        # 게시물이 수정되었는지 확인
        sample_post.refresh_from_db()
        assert sample_post.title == '수정된 제목'


class TestDeleteAndDownload:
    """삭제 테스트 (1개)"""

    def test_post_delete(self, client_with_login, team, sample_post):
        """게시물 삭제 (POST)"""
        url = reverse('shares:post_delete', kwargs={'pk': team.id, 'post_id': sample_post.id})
        response = client_with_login.post(url)

        # 성공 시 리다이렉트
        assert response.status_code == 302

        # 게시물이 삭제되었는지 확인
        from shares.models import Post
        assert not Post.objects.filter(id=sample_post.id).exists()


class TestPermissions:
    """권한 검증 테스트 (2개)"""

    def test_unauthenticated_user_redirected(self, client, team):
        """비로그인 사용자 리다이렉트"""
        url = reverse('shares:post_list', kwargs={'pk': team.id})
        response = client.get(url)

        # 로그인 페이지로 리다이렉트
        assert response.status_code == 302
        assert '/accounts/login' in response.url

    def test_non_member_access_denied(self, client, team, db):
        """비멤버 접근 차단"""
        from accounts.models import User

        # 팀에 속하지 않은 새 사용자 생성
        non_member = User.objects.create_user(
            username='nonmember',
            nickname='비멤버',
            password='testpass123'
        )

        client.force_login(non_member)
        url = reverse('shares:post_list', kwargs={'pk': team.id})
        response = client.get(url)

        # 403 또는 리다이렉트
        assert response.status_code in [403, 302]
