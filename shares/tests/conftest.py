"""
Shares 앱 전용 pytest fixtures
"""
import pytest
from datetime import date
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

from shares.models import Post
from shares.services import ShareService
from teams.models import TeamUser


# ================================
# 상수 정의
# ================================

# 테스트 기준 날짜 (2025-10-20 월요일)
TEST_BASE_DATE = date(2025, 10, 20)

# 파일 크기 상수 (가독성 및 유지보수성 향상)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
SMALL_FILE_SIZE = 1 * 1024 * 1024  # 1MB
LARGE_FILE_SIZE = 11 * 1024 * 1024  # 11MB (실패 케이스용)

# 허용 파일 확장자
ALLOWED_FILE_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.jpg', '.png', '.txt']


# ================================
# 서비스 및 도메인 객체 Fixtures
# ================================

@pytest.fixture
def share_service():
    """ShareService 인스턴스"""
    return ShareService()


@pytest.fixture(scope="session")
def base_date():
    """
    테스트 기준 날짜 (고정)

    Returns:
        date: 2025-10-20 (월요일)

    Note:
        테스트 재현성을 위해 고정된 날짜 사용
        scope="session"으로 전체 테스트 세션에서 한 번만 생성
    """
    return TEST_BASE_DATE


@pytest.fixture
def host_teamuser(db, team, user):
    """
    팀장 TeamUser (Members, Schedules 앱과 네이밍 일관성 유지)

    Note:
        db fixture는 Django DB 접근을 위해 필요 (암묵적 사용)
    """
    return TeamUser.objects.get(team=team, user=user)


@pytest.fixture
def member_teamuser(db, team, another_user):
    """
    일반 멤버 TeamUser (Members, Schedules 앱과 네이밍 일관성 유지)

    Note:
        db fixture는 Django DB 접근을 위해 필요 (암묵적 사용)
    """
    teamuser = TeamUser.objects.create(team=team, user=another_user)
    team.currentuser += 1
    team.save()
    return teamuser


# ================================
# 파일 Fixtures
# ================================

@pytest.fixture
def small_test_file():
    """
    작은 테스트 파일 (1MB, 정상 케이스용)

    Returns:
        InMemoryUploadedFile: 메모리 내 업로드 파일 객체

    사용 시나리오:
    - 파일 업로드 성공 테스트
    - 파일 다운로드 테스트
    """
    file_content = b'x' * SMALL_FILE_SIZE
    file_io = BytesIO(file_content)

    return InMemoryUploadedFile(
        file=file_io,
        field_name='file',
        name='test_document.pdf',
        content_type='application/pdf',
        size=SMALL_FILE_SIZE,
        charset=None
    )


@pytest.fixture
def large_test_file():
    """
    대용량 테스트 파일 (11MB, 실패 케이스용)

    Returns:
        InMemoryUploadedFile: 10MB 초과 파일

    사용 시나리오:
    - 파일 크기 제한 테스트
    - ValidationError 발생 확인
    """
    file_content = b'x' * LARGE_FILE_SIZE
    file_io = BytesIO(file_content)

    return InMemoryUploadedFile(
        file=file_io,
        field_name='file',
        name='large_document.pdf',
        content_type='application/pdf',
        size=LARGE_FILE_SIZE,
        charset=None
    )


# ================================
# 게시물 데이터 Fixtures
# ================================

@pytest.fixture
def sample_post(db, host_teamuser):
    """
    기본 게시물 (파일 없음)

    사용 시나리오:
    - 단일 게시물 조회 테스트
    - 기본 CRUD 테스트

    Note:
        registered_date는 auto_now_add=True로 자동 생성
    """
    return Post.objects.create(
        team=host_teamuser.team,
        writer=host_teamuser.user,
        title='테스트 게시물',
        article='테스트 내용입니다.'
    )


@pytest.fixture
def post_with_file(db, host_teamuser, small_test_file):
    """
    파일 첨부 게시물

    사용 시나리오:
    - 파일 다운로드 테스트
    - 파일 포함 게시물 삭제 테스트

    Note:
        registered_date는 auto_now_add=True로 자동 생성
    """
    return Post.objects.create(
        team=host_teamuser.team,
        writer=host_teamuser.user,
        title='파일 첨부 게시물',
        article='파일이 첨부된 게시물입니다.',
        upload_files=small_test_file,
        filename='test_document.pdf'
    )


@pytest.fixture
def multiple_posts(db, host_teamuser, member_teamuser):
    """
    검색 및 페이지네이션용 다수 게시물

    구조:
    - 11개 게시물 (페이지네이션 테스트용, 페이지당 10개)
    - 다양한 제목/내용 (검색 테스트용)
    - 2명의 작성자 (작성자 검색 테스트용)

    사용 시나리오:
    - 검색 기능 테스트 (제목, 내용, 작성자)
    - 페이지네이션 테스트 (2페이지 확인)

    Note:
        registered_date는 auto_now_add=True로 자동 생성
    """
    posts = []

    # host_teamuser 작성 게시물 6개
    for i in range(6):
        post = Post.objects.create(
            team=host_teamuser.team,
            writer=host_teamuser.user,
            title=f'호스트 게시물 {i+1}',
            article=f'호스트가 작성한 내용 {i+1}'
        )
        posts.append(post)

    # member_teamuser 작성 게시물 5개
    for i in range(5):
        post = Post.objects.create(
            team=member_teamuser.team,
            writer=member_teamuser.user,
            title=f'멤버 게시물 {i+1}',
            article=f'멤버가 작성한 내용 {i+1}'
        )
        posts.append(post)

    return posts
