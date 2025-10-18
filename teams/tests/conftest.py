"""
Teams 앱 전용 pytest fixtures
"""
import pytest
from datetime import date, timedelta
from teams.models import Milestone, TeamUser


@pytest.fixture
def milestone(db, team):
    """기본 마일스톤 (진행 중)"""
    today = date.today()
    return Milestone.objects.create(
        team=team,
        title='테스트 마일스톤',
        description='테스트용 마일스톤입니다',
        startdate=today - timedelta(days=5),
        enddate=today + timedelta(days=10),
        priority='medium',
        progress_percentage=50,
        is_completed=False
    )


@pytest.fixture
def completed_milestone(db, team):
    """완료된 마일스톤"""
    today = date.today()
    return Milestone.objects.create(
        team=team,
        title='완료된 마일스톤',
        description='완료된 마일스톤입니다',
        startdate=today - timedelta(days=20),
        enddate=today - timedelta(days=5),
        priority='high',
        progress_percentage=100,
        is_completed=True
    )


@pytest.fixture
def team_with_members(db, team, another_user):
    """멤버가 있는 팀 (호스트 + 일반 멤버 1명)"""
    TeamUser.objects.create(team=team, user=another_user)
    team.currentuser = 2
    team.save()
    return team


@pytest.fixture
def full_team(db, user):
    """최대 인원에 도달한 팀"""
    from teams.models import Team
    team = Team.objects.create(
        title='가득찬팀',
        maxuser=1,
        teampasswd='fullteam123',
        introduction='가득 찬 팀입니다',
        host=user,
        currentuser=1,
        invitecode='FULL1234'
    )
    TeamUser.objects.create(team=team, user=user)
    return team
