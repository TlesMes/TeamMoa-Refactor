"""
부하 테스트용 계정 및 팀 생성 스크립트

사용법:
    python manage.py shell < temp/load_test/create_test_account.py
"""

from accounts.models import User
from teams.models import Team
from teams.services import TeamService

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트 계정 정보
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST_EMAIL = "loadtest@teammoa.com"
TEST_PASSWORD = "LoadTest2024!"
TEST_USERNAME = "loadtest"
TEST_TEAM_NAME = "LoadTest Team"

print("=" * 60)
print("부하 테스트용 계정 및 팀 생성")
print("=" * 60)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 테스트 계정 생성 또는 확인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if User.objects.filter(email=TEST_EMAIL).exists():
    user = User.objects.get(email=TEST_EMAIL)
    print(f"✅ 기존 테스트 계정 확인: {TEST_EMAIL}")

    # 비밀번호 재설정 (필요 시)
    user.set_password(TEST_PASSWORD)
    user.is_active = True
    user.save()
    print(f"   → 비밀번호 재설정 완료")
else:
    user = User.objects.create_user(
        username=TEST_USERNAME,
        email=TEST_EMAIL,
        password=TEST_PASSWORD,
        is_active=True
    )
    print(f"✅ 테스트 계정 생성 완료: {TEST_EMAIL}")

print(f"   ID: {user.id}")
print(f"   Username: {user.username}")
print(f"   Email: {user.email}")
print(f"   Active: {user.is_active}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 테스트 팀 생성 또는 확인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if Team.objects.filter(name=TEST_TEAM_NAME).exists():
    team = Team.objects.filter(name=TEST_TEAM_NAME).first()
    print(f"\n✅ 기존 테스트 팀 확인: {TEST_TEAM_NAME}")
else:
    team = TeamService.create_team(
        name=TEST_TEAM_NAME,
        description="부하 테스트용 팀 (자동 생성)",
        creator=user
    )
    print(f"\n✅ 테스트 팀 생성 완료: {TEST_TEAM_NAME}")

print(f"   ID: {team.id}")
print(f"   Name: {team.name}")
print(f"   Description: {team.description}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. config.py 설정값 출력
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "=" * 60)
print("📋 temp/load_test/config.py에 설정할 값:")
print("=" * 60)
print(f'TEST_USER_EMAIL = "{TEST_EMAIL}"')
print(f'TEST_USER_PASSWORD = "{TEST_PASSWORD}"')
print(f'TEST_TEAM_ID = {team.id}')
print("=" * 60)

print("\n✅ 설정 완료! 이제 부하 테스트를 실행할 수 있습니다.")
print("\n실행 방법:")
print("  1. temp/load_test/config.py 파일에 위 값 입력")
print("  2. cd temp/load_test")
print("  3. locust -f locustfile.py --host https://teammoa.duckdns.org")
print("  4. http://localhost:8089 접속")
print("=" * 60)
