"""
로컬 한계점 탐색 부하 테스트용 시드 데이터 생성 (2026-09-10)

기존 create_test_account.py는 계정 1개만 만들지만, locustfile은
loaduser1~300 과 팀 3개를 전제한다. 이 스크립트가 그 전제를 만든다.

또한 N+1 최적화 전/후 비교가 목적이므로, 목록 페이지에 **항목이 충분히 많아야**
차이가 드러난다. 그래서 팀당 게시물/TODO/스케줄을 넉넉히 만든다.

실행:
    docker compose -f docker-compose.loadtest.yml exec -T web \
        python manage.py shell < docs/guides/load-testing/local-knee/seed_load_data.py

멱등하다. 두 번 돌려도 중복 생성하지 않는다.
"""
import datetime
import random

from django.db import transaction

from accounts.models import User
from teams.models import Team, TeamUser, Milestone
from members.models import Todo
from shares.models import Post
from schedules.models import PersonalDaySchedule

random.seed(42)  # 재현 가능하게 고정

# 2차 측정에서 VU를 1200까지 올리므로 계정을 늘릴 수 있게 파라미터화했다.
#
# ⚠️ USERS_PER_TEAM 은 **절대 바꾸지 말 것.**
# 기존 팀에 멤버를 더 넣으면 팀 상세/스케줄 집계 쿼리가 무거워져 요청당 비용이
# 달라지고, 1차 측정(팀당 100명)과 수치를 나란히 놓을 수 없게 된다.
# 계정을 늘릴 때는 **같은 모양의 팀을 새로 만든다** — TEAMS_TOTAL 만 올린다.
#   예) 1200 계정 = TEAMS_TOTAL 12 × 팀당 100명
#
#   LOADTEST_TEAMS=12 python manage.py shell < seed_load_data.py
import os

USERS_PER_TEAM = 100                                   # 고정 (1차와 동일)
TEAMS_TOTAL = int(os.environ.get("LOADTEST_TEAMS", "3"))
USERS_TOTAL = USERS_PER_TEAM * TEAMS_TOTAL
POSTS_PER_TEAM = 60      # 공유게시판 목록 N+1 노출용
TODOS_PER_TEAM = 120     # TODO 목록 N+1 노출용
SCHEDULE_DAYS = 7        # 팀 가용시간 계산 대상 기간
PASSWORD = "LoadTest2024!"

print("=" * 60)
print("부하 테스트 시드 데이터 생성")
print("=" * 60)

# ── 1. 사용자 300명 ──────────────────────────────────────────
existing = {u.username: u for u in User.objects.filter(username__startswith="loaduser")}
print(f"기존 loaduser: {len(existing)}명")

to_create = []
for i in range(1, USERS_TOTAL + 1):
    name = f"loaduser{i}"
    if name in existing:
        continue
    u = User(
        username=name,
        email=f"{name}@loadtest.local",
        nickname=f"부하{i}",
        is_active=True,
    )
    u.set_password(PASSWORD)  # PBKDF2 실제 해시 (prod와 동일한 검증 비용)
    to_create.append(u)

if to_create:
    print(f"사용자 {len(to_create)}명 생성 중... (PBKDF2 해싱으로 1~2분 소요)")
    User.objects.bulk_create(to_create, batch_size=50)

users = list(User.objects.filter(username__startswith="loaduser").order_by("id"))
# locustfile의 loaduser{n} → 팀 매핑과 맞추기 위해 번호순으로 정렬
users.sort(key=lambda u: int(u.username.replace("loaduser", "")))
print(f"✅ 사용자 총 {len(users)}명")

# ── 2. 팀 3개 + 팀당 100명 ──────────────────────────────────
team_ids = []
for t in range(TEAMS_TOTAL):
    title = f"LoadTest Team {t + 1}"
    team = Team.objects.filter(title=title).first()
    members = users[t * USERS_PER_TEAM:(t + 1) * USERS_PER_TEAM]
    if team is None:
        team = Team(
            title=title,
            maxuser=USERS_PER_TEAM + 10,
            currentuser=0,
            host=members[0],
            invitecode=f"LOADTEST{t + 1}",
            teampasswd="1234",
            introduction="한계점 탐색 부하 테스트용 팀",
        )
        team.save()
    team_ids.append(team.id)

    have = set(TeamUser.objects.filter(team=team).values_list("user_id", flat=True))
    new_tu = [TeamUser(team=team, user=u) for u in members if u.id not in have]
    if new_tu:
        TeamUser.objects.bulk_create(new_tu, batch_size=100)

    team.currentuser = TeamUser.objects.filter(team=team).count()
    Team.objects.filter(pk=team.pk).update(currentuser=team.currentuser)  # full_clean 우회
    print(f"✅ {title} (id={team.id}) 멤버 {team.currentuser}명")

# ── 3. 팀별 마일스톤 / 게시물 / TODO / 스케줄 ────────────────
today = datetime.date.today()

for team_id in team_ids:
    team = Team.objects.get(pk=team_id)
    tus = list(TeamUser.objects.filter(team=team))

    # 마일스톤 3개
    if not Milestone.objects.filter(team=team).exists():
        for m in range(3):
            Milestone.objects.create(
                team=team,
                title=f"마일스톤 {m + 1}",
                description="부하 테스트용",
                startdate=today,
                enddate=today + datetime.timedelta(days=14),
                priority="medium",
            )
    milestones = list(Milestone.objects.filter(team=team))

    # 게시물
    have = Post.objects.filter(team=team).count()
    if have < POSTS_PER_TEAM:
        Post.objects.bulk_create([
            Post(
                team=team,
                teamuser=random.choice(tus),
                title=f"부하 테스트 게시물 {i}",
                article="본문 " * 50,
            )
            for i in range(have, POSTS_PER_TEAM)
        ], batch_size=100)

    # TODO (Todo.save()가 마일스톤 진행률을 갱신하므로 bulk_create로 우회)
    have = Todo.objects.filter(team=team).count()
    if have < TODOS_PER_TEAM:
        Todo.objects.bulk_create([
            Todo(
                team=team,
                assignee=random.choice(tus),
                milestone=random.choice(milestones),
                content=f"부하 테스트 TODO {i}",
                is_completed=(i % 3 == 0),
                order=i,
            )
            for i in range(have, TODOS_PER_TEAM)
        ], batch_size=100)

    # 개인 스케줄 (팀 가용시간 집계 쿼리를 무겁게 만든다)
    have = PersonalDaySchedule.objects.filter(owner__team=team).count()
    want = len(tus) * SCHEDULE_DAYS
    if have < want:
        rows = []
        for tu in tus:
            for d in range(SCHEDULE_DAYS):
                rows.append(PersonalDaySchedule(
                    owner=tu,
                    date=today + datetime.timedelta(days=d),
                    available_hours=sorted(random.sample(range(24), 8)),
                ))
        PersonalDaySchedule.objects.bulk_create(
            rows, batch_size=500, ignore_conflicts=True
        )

    print(f"✅ team {team_id}: 게시물 {Post.objects.filter(team=team).count()}, "
          f"TODO {Todo.objects.filter(team=team).count()}, "
          f"스케줄 {PersonalDaySchedule.objects.filter(owner__team=team).count()}")

print("=" * 60)
print(f"locustfile config: TEAM_IDS = {team_ids}")
print("=" * 60)
