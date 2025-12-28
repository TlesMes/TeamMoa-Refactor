"""
TeamMoa 프로젝트 공통 pytest fixtures

모든 앱에서 공통으로 사용하는 기본 fixture들을 정의합니다.
"""
import json
from collections import defaultdict
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from teams.models import Team, TeamUser

User = get_user_model()


@pytest.fixture
def user(db):
    """기본 테스트 사용자"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123!',
        nickname='테스터',
        is_active=True
    )


@pytest.fixture
def another_user(db):
    """추가 테스트 사용자 (권한 테스트용)"""
    return User.objects.create_user(
        username='anotheruser',
        email='another@example.com',
        password='testpass123!',
        nickname='다른유저',
        is_active=True
    )


@pytest.fixture
def third_user(db):
    """세 번째 테스트 사용자 (다중 멤버 테스트용)"""
    return User.objects.create_user(
        username='thirduser',
        email='third@example.com',
        password='testpass123!',
        nickname='세번째유저',
        is_active=True
    )


@pytest.fixture
def team(db, user):
    """기본 팀 (user가 호스트)"""
    team = Team.objects.create(
        title='테스트팀',
        maxuser=10,
        teampasswd='teampass123',
        introduction='테스트용 팀입니다',
        host=user,
        currentuser=1,
        invitecode='TEST1234'
    )
    TeamUser.objects.create(team=team, user=user)
    return team


# ================================
# API 테스트용 Clients (DRF)
# ================================

@pytest.fixture
def api_client():
    """DRF API 테스트 클라이언트"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, user):
    """인증된 API 클라이언트 (DRF)"""
    api_client.force_authenticate(user=user)
    return api_client


# 하위 호환성을 위한 별칭 (deprecated)
@pytest.fixture
def authenticated_client(api_client, user):
    """[DEPRECATED] authenticated_api_client 사용 권장"""
    api_client.force_authenticate(user=user)
    return api_client


# ================================
# SSR 테스트용 Clients (Django)
# ================================

@pytest.fixture
def web_client():
    """Django 웹 클라이언트 (SSR 테스트용)"""
    from django.test import Client
    return Client()


@pytest.fixture
def authenticated_web_client(web_client, user):
    """인증된 웹 클라이언트 (user로 로그인)"""
    web_client.force_login(user)
    return web_client


# ================================
# 테스트 통계 자동 생성
# ================================

def pytest_configure(config):
    """pytest 마커 등록"""
    config.addinivalue_line("markers", "service: 서비스 레이어 테스트")
    config.addinivalue_line("markers", "api: API 레이어 테스트")
    config.addinivalue_line("markers", "ssr: SSR 뷰 테스트")

    # --generate-stats 옵션 추가
    config.addinivalue_line(
        "markers",
        "generate-stats: 테스트 통계 JSON 생성 (CI/CD 전용)"
    )


def pytest_addoption(parser):
    """커맨드라인 옵션 추가"""
    parser.addoption(
        "--generate-stats",
        action="store_true",
        default=False,
        help="테스트 통계 JSON 생성 (CI/CD 전용)"
    )


def pytest_sessionfinish(session, exitstatus):
    """테스트 종료 시 통계 JSON 생성 (--generate-stats 옵션 필요)"""
    # --generate-stats 옵션이 없으면 통계 생성 건너뛰기
    if not session.config.getoption("--generate-stats"):
        return

    stats = defaultdict(lambda: {'service': 0, 'api': 0, 'ssr': 0, 'total': 0})

    for item in session.items:
        # pathlib로 OS 독립적인 경로 처리
        test_path = Path(item.fspath)

        # 프로젝트 루트 기준 상대 경로로 변환 (OS 독립적)
        try:
            relative_path = test_path.relative_to(Path.cwd())
            parts = relative_path.parts
        except ValueError:
            # 상대 경로 변환 실패 시 절대 경로 사용
            parts = test_path.parts

        # 앱 이름 추출 (예: teams/tests/test_service.py → teams)
        # parts[0]이 앱 이름, parts[1]이 'tests'인 경우
        if len(parts) >= 3 and parts[1] == 'tests':
            app_name = parts[0]

            # pytest marker 기반 카테고리 분류 (우선순위)
            if 'service' in item.keywords:
                category = 'service'
            elif 'api' in item.keywords:
                category = 'api'
            elif 'ssr' in item.keywords:
                category = 'ssr'
            else:
                # fallback: 파일명 기반 추론
                test_file = test_path.name.lower()
                if 'service' in test_file:
                    category = 'service'
                elif 'api' in test_file or 'viewset' in test_file:
                    category = 'api'
                elif 'view' in test_file or 'ssr' in test_file:
                    category = 'ssr'
                else:
                    category = 'service'  # 기본값

            stats[app_name][category] += 1
            stats[app_name]['total'] += 1

    # JSON 저장 (루트 디렉토리)
    output_file = Path('test_stats.json')
    with output_file.open('w', encoding='utf-8') as f:
        json.dump(dict(stats), f, ensure_ascii=False, indent=2)

    print(f"\n✅ 테스트 통계가 {output_file}에 저장되었습니다.")
