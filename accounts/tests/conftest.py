"""
Accounts 앱 전용 pytest fixtures

독립성 원칙:
- fixture 간 의존도 최소화
- factory 함수 활용 (재사용성)
- 테스트 격리성 확보
"""
import pytest
from datetime import date
from django.contrib.sites.models import Site
from accounts.models import User
from accounts.services import AuthService


# ================================
# 상수 정의
# ================================

# 테스트 기준 날짜 (2025-10-20 월요일)
TEST_BASE_DATE = date(2025, 10, 20)

# Rate limiting 상수
RATE_LIMIT_MINUTES = 5  # 인증 이메일 재발송 제한 시간

# 테스트용 비밀번호
TEST_PASSWORD = 'TestPass123!'


# ================================
# 독립적 Fixtures (최소 의존도)
# ================================

@pytest.fixture
def auth_service():
    """
    AuthService 인스턴스 (의존성 없음)

    사용 시나리오:
    - 순수 비즈니스 로직 테스트
    - HTTP와 무관한 서비스 메서드 검증
    """
    return AuthService()


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
def test_site(db):
    """
    Django Site 객체 (이메일 발송용)

    Returns:
        Site: 현재 사이트 (기본 example.com)

    사용 시나리오:
    - 이메일 템플릿에 도메인 정보 제공
    - 활성화 링크 생성

    Note:
        Django의 Site framework 사용
        테스트 DB에 자동 생성되는 기본 Site 반환
    """
    return Site.objects.get_current()


# ================================
# Factory 함수 (독립적 사용자 생성)
# ================================

def create_inactive_user(**kwargs):
    """
    비활성 사용자 생성 헬퍼 (독립 함수)

    Args:
        **kwargs: User 모델 필드 (기본값 덮어쓰기)

    Returns:
        User: 비활성 상태 사용자 (is_active=False)

    사용 예시:
        user = create_inactive_user(username='testuser1', email='test1@example.com')

    Note:
        - fixture가 아닌 일반 함수 (독립 실행 가능)
        - 테스트마다 고유한 사용자 생성 가능
        - 의존성 없음
    """
    defaults = {
        'username': 'testuser',
        'email': 'test@example.com',
        'nickname': '테스트유저',
        'is_active': False
    }
    defaults.update(kwargs)

    password = TEST_PASSWORD
    if 'password' in kwargs:
        password = kwargs.pop('password')

    user = User.objects.create_user(**defaults)
    user.set_password(password)
    user.save()
    return user


def create_active_user(**kwargs):
    """
    활성 사용자 생성 헬퍼 (독립 함수)

    Args:
        **kwargs: User 모델 필드 (기본값 덮어쓰기)

    Returns:
        User: 활성 상태 사용자 (is_active=True)

    사용 예시:
        user = create_active_user(username='activeuser', email='active@example.com')

    Note:
        내부적으로 create_inactive_user 호출 후 is_active=True 설정
    """
    defaults = {'is_active': True}
    defaults.update(kwargs)
    return create_inactive_user(**defaults)
