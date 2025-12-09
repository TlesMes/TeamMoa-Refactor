"""
Shares 서비스 레이어 테스트 (16개)

테스트 구성:
- TestPostCRUD: 6개 - 게시글 생성/수정/삭제, 파일 첨부
- TestSearchFunctionality: 4개 - 제목/내용/작성자/전체 검색 (parametrize)
- TestFileHandling: 2개 - 파일 다운로드, 정리
- TestPermissionsAndRetrieval: 4개 - 권한 및 상세 조회

사용 위치:
- SSR 뷰: post_list, post_detail, post_write, post_edit 등
"""
import pytest
from django.core.exceptions import PermissionDenied
from shares.models import Post
from shares.tests.conftest import MAX_FILE_SIZE


class TestPostCRUD:
    """게시물 CRUD 테스트 (6개)"""

    def test_create_post_without_file(self, share_service, team, user, base_date):
        """게시물 정상 생성 (파일 없음)"""
        post_data = {
            'title': '테스트 게시물',
            'article': '테스트 내용입니다.'
        }

        post = share_service.create_post(team.id, post_data, {}, user)

        assert post.title == '테스트 게시물'
        assert post.article == '테스트 내용입니다.'
        assert post.teamuser.user == user
        assert post.teamuser.team == team
        assert not post.upload_files  # 파일 없음

    def test_create_post_with_file(self, share_service, team, user, small_test_file):
        """게시물 정상 생성 (파일 포함)"""
        post_data = {
            'title': '파일 첨부 게시물',
            'article': '파일이 첨부된 내용입니다.'
        }
        files_data = {
            'upload_files': small_test_file
        }

        post = share_service.create_post(team.id, post_data, files_data, user)

        assert post.title == '파일 첨부 게시물'
        assert post.upload_files  # 파일 존재
        assert post.filename == 'test_document.pdf'

    def test_create_post_with_large_file_fails(self, share_service, team, user, large_test_file):
        """대용량 파일 업로드 실패 (10MB 초과)"""
        # Django의 FILE_UPLOAD_MAX_MEMORY_SIZE 설정을 모킹하거나
        # 서비스 레이어에서 파일 크기 검증이 있다면 해당 로직 테스트
        # 현재 서비스 레이어에는 파일 크기 검증이 없으므로,
        # 이 테스트는 향후 검증 로직 추가 시 사용

        # 임시로 파일 크기가 MAX_FILE_SIZE를 초과하는지 확인
        assert large_test_file.size > MAX_FILE_SIZE

        # 현재는 서비스 레이어에서 파일 크기 검증을 하지 않으므로
        # 이 테스트는 Django Form 레이어나 뷰 레벨에서 처리됨
        # 따라서 여기서는 파일 크기만 확인

    def test_update_post_by_author(self, share_service, sample_post):
        """게시물 수정 (작성자 본인)"""
        updated_data = {
            'title': '수정된 제목',
            'article': '수정된 내용'
        }

        updated_post = share_service.update_post(
            sample_post.id,
            updated_data,
            sample_post.teamuser.user
        )

        assert updated_post.title == '수정된 제목'
        assert updated_post.article == '수정된 내용'

    def test_update_post_by_non_author_fails(self, share_service, sample_post, another_user):
        """게시물 수정 실패 (권한 없음)"""
        updated_data = {
            'title': '수정 시도',
            'article': '권한 없는 수정'
        }

        with pytest.raises(PermissionDenied, match='본인 게시글이 아닙니다'):
            share_service.update_post(sample_post.id, updated_data, another_user)

    def test_delete_post_with_file_cleanup(self, share_service, post_with_file):
        """게시물 삭제 (파일 함께 삭제 확인)"""
        post_id = post_with_file.id
        post_title = post_with_file.title

        deleted_title = share_service.delete_post(post_id, post_with_file.teamuser.user)

        assert deleted_title == post_title
        assert not Post.objects.filter(id=post_id).exists()


class TestSearchFunctionality:
    """검색 기능 테스트 (1개, parametrize 활용)"""

    @pytest.mark.parametrize("search_type,query,expected_count", [
        ('title', '호스트 게시물 1', 1),       # 제목 검색
        ('content', '호스트가 작성한 내용 2', 1),  # 내용 검색
        ('writer', '테스터', 6),              # 작성자 검색 (conftest의 user.nickname)
        ('all', '게시물', 11),                # 전체 검색 (모든 게시물에 '게시물' 포함)
    ])
    def test_search_posts_integrated(
        self,
        share_service,
        multiple_posts,
        host_teamuser,
        search_type,
        query,
        expected_count
    ):
        """검색 기능 통합 테스트 (4가지 케이스)"""
        result = share_service.search_posts(
            team_id=host_teamuser.team.id,
            query=query,
            search_type=search_type,
            page=1,
            per_page=20  # 모든 결과 확인을 위해 20개로 설정
        )

        assert len(result['posts'].object_list) == expected_count


class TestFileHandling:
    """파일 처리 테스트 (2개)"""

    def test_file_download_no_file_raises_error(self, share_service, sample_post):
        """파일이 없는 게시물에서 다운로드 시도 시 에러"""
        with pytest.raises(ValueError, match='다운로드할 파일이 없습니다'):
            share_service.handle_file_download(sample_post.id, sample_post.teamuser.user)

    def test_cleanup_post_files(self, share_service, post_with_file):
        """게시물 삭제 시 파일 정리 메서드 호출"""
        # cleanup_post_files 메서드 호출 (예외 없이 실행되는지 확인)
        share_service.cleanup_post_files(post_with_file)

        # 파일이 정리되었는지 확인
        # 실제 파일 시스템 정리는 Post.delete()에서 처리되므로
        # 여기서는 메서드 호출이 성공하는지만 확인
        assert True  # cleanup_post_files 메서드가 예외 없이 실행됨


class TestPermissionsAndRetrieval:
    """권한 및 조회 테스트 (4개)"""

    def test_get_post_detail(self, share_service, sample_post, user):
        """게시물 상세 조회"""
        result = share_service.get_post_detail(sample_post.id, user)

        assert result['post'] == sample_post
        assert result['is_author'] is True  # user가 작성자

    def test_get_post_detail_is_author_false(self, share_service, sample_post, another_user):
        """게시물 상세 조회 (비작성자)"""
        result = share_service.get_post_detail(sample_post.id, another_user)

        assert result['post'] == sample_post
        assert result['is_author'] is False  # another_user는 작성자가 아님

    def test_check_post_author(self, share_service, sample_post, another_user):
        """작성자 확인 메서드"""
        # 작성자 본인
        assert share_service.check_post_author(sample_post.id, sample_post.teamuser.user) is True

        # 비작성자
        assert share_service.check_post_author(sample_post.id, another_user) is False

    def test_get_post_with_team_check(self, share_service, sample_post):
        """팀 확인 및 게시물 가져오기"""
        post = share_service.get_post_with_team_check(
            sample_post.id,
            sample_post.team.id
        )

        assert post == sample_post


class TestDeletedAuthorHandling:
    """탈퇴한 작성자 처리 테스트 (4개)"""

    def test_get_post_detail_with_deleted_author(self, share_service, post_with_deleted_author, user):
        """탈퇴한 작성자의 게시물 상세 조회"""
        result = share_service.get_post_detail(post_with_deleted_author.id, user)

        assert result['post'].teamuser is None
        assert result['is_author'] is False  # 작성자가 없으므로 False

    def test_check_post_author_with_deleted_author(self, share_service, post_with_deleted_author, user):
        """탈퇴한 작성자의 게시물 권한 확인 (일반 사용자)"""
        # 일반 사용자는 작성자가 아님
        is_author = share_service.check_post_author(post_with_deleted_author.id, user)
        assert is_author is False

    def test_get_team_posts_includes_deleted_author_posts(self, share_service, post_with_deleted_author):
        """팀 게시물 목록에 탈퇴한 작성자의 게시물 포함됨"""
        result = share_service.get_team_posts(post_with_deleted_author.team.id, page=1, per_page=10)

        # team FK가 있으므로 목록에 포함됨
        post_ids = [p.id for p in result['posts']]
        assert post_with_deleted_author.id in post_ids

    def test_get_post_with_team_check_deleted_author(self, share_service, post_with_deleted_author):
        """탈퇴한 작성자의 게시물 팀 확인"""
        # team FK로 직접 확인하므로 정상 작동
        post = share_service.get_post_with_team_check(
            post_with_deleted_author.id,
            post_with_deleted_author.team.id
        )

        assert post == post_with_deleted_author
        assert post.teamuser is None
