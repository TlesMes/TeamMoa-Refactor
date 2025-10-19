"""
Members 앱 전용 pytest fixtures
"""
import pytest
from members.models import Todo
from members.services import TodoService
from teams.models import TeamUser


@pytest.fixture
def todo_service():
    """TodoService 인스턴스"""
    return TodoService()


@pytest.fixture
def host_teamuser(db, team, user):
    """팀장 TeamUser (이미 team fixture에서 생성되지만 명시적으로 반환)"""
    return TeamUser.objects.get(team=team, user=user)


@pytest.fixture
def member_teamuser(db, team, another_user):
    """일반 멤버 TeamUser"""
    teamuser = TeamUser.objects.create(
        team=team,
        user=another_user
    )
    team.currentuser += 1
    team.save()
    return teamuser


@pytest.fixture
def third_member_teamuser(db, team, third_user):
    """세 번째 멤버 TeamUser (다중 멤버 테스트용)"""
    teamuser = TeamUser.objects.create(
        team=team,
        user=third_user
    )
    team.currentuser += 1
    team.save()
    return teamuser


@pytest.fixture
def unassigned_todo(db, team):
    """미할당 Todo (TODO 보드)"""
    return Todo.objects.create(
        team=team,
        content='미할당 할 일',
        is_completed=False,
        order=1
    )


@pytest.fixture
def assigned_todo(db, team, member_teamuser):
    """할당된 Todo (멤버 보드)"""
    return Todo.objects.create(
        team=team,
        content='할당된 할 일',
        assignee=member_teamuser,
        is_completed=False,
        order=1
    )


@pytest.fixture
def completed_todo(db, team):
    """완료된 Todo (DONE 보드)"""
    return Todo.objects.create(
        team=team,
        content='완료된 할 일',
        is_completed=True,
        order=1
    )


@pytest.fixture
def member_completed_todo(db, team, member_teamuser):
    """멤버에게 할당되고 완료된 Todo"""
    return Todo.objects.create(
        team=team,
        content='멤버 완료 할 일',
        assignee=member_teamuser,
        is_completed=True,
        order=1
    )


@pytest.fixture
def multiple_todos(db, team, member_teamuser):
    """다양한 상태의 여러 Todo (보드 테스트용)"""
    todos = {
        'unassigned_1': Todo.objects.create(team=team, content='TODO 1', order=1),
        'unassigned_2': Todo.objects.create(team=team, content='TODO 2', order=2),
        'member_1': Todo.objects.create(team=team, content='멤버 Todo 1', assignee=member_teamuser, order=1),
        'member_2': Todo.objects.create(team=team, content='멤버 Todo 2', assignee=member_teamuser, order=2),
        'completed_1': Todo.objects.create(team=team, content='DONE 1', is_completed=True, order=1),
        'completed_2': Todo.objects.create(team=team, content='DONE 2', is_completed=True, order=2),
    }
    return todos
