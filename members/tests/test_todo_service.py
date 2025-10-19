"""
TodoService 서비스 레이어 테스트
총 20개 테스트:
- create_todo: 2개
- assign_todo: 5개
- complete_todo: 3개
- move_to_todo: 3개
- move_to_done: 3개
- delete_todo: 2개
- get_team_todos_with_stats: 2개
"""
import pytest
from django.http import Http404
from members.models import Todo


pytestmark = pytest.mark.django_db


class TestTodoServiceCreateTodo:
    """create_todo 메서드 테스트"""

    def test_create_todo_success(self, todo_service, team, user):
        """Todo 생성 성공"""
        content = 'Test Todo'

        todo = todo_service.create_todo(
            team=team,
            content=content,
            creator=user
        )

        assert todo.content == content
        assert todo.team == team
        assert todo.is_completed is False
        assert todo.assignee is None

    def test_create_todo_empty_content(self, todo_service, team, user):
        """빈 내용으로 Todo 생성 시 실패"""
        with pytest.raises(ValueError, match='할 일 내용을 입력해주세요'):
            todo_service.create_todo(
                team=team,
                content='   ',  # 공백만
                creator=user
            )


class TestTodoServiceAssignTodo:
    """assign_todo 메서드 테스트"""

    def test_assign_todo_by_host(self, todo_service, team, user, member_teamuser):
        """팀장이 Todo 할당"""
        todo = Todo.objects.create(team=team, content='Test')

        result = todo_service.assign_todo(
            todo_id=todo.id,
            assignee_id=member_teamuser.id,
            team=team,
            requester=user
        )

        assert result.assignee == member_teamuser
        assert result.order == 1

    def test_assign_todo_self_assign(self, todo_service, team, another_user, member_teamuser):
        """일반 멤버가 본인에게 할당"""
        todo = Todo.objects.create(team=team, content='Test')

        result = todo_service.assign_todo(
            todo_id=todo.id,
            assignee_id=member_teamuser.id,
            team=team,
            requester=another_user
        )

        assert result.assignee == member_teamuser

    def test_assign_todo_no_permission(self, todo_service, team, another_user, host_teamuser, member_teamuser):
        """일반 멤버가 다른 사람에게 할당 시도 (실패)"""
        todo = Todo.objects.create(team=team, content='Test')

        with pytest.raises(ValueError, match='권한이 없습니다'):
            todo_service.assign_todo(
                todo_id=todo.id,
                assignee_id=host_teamuser.id,  # 다른 사람
                team=team,
                requester=another_user  # 일반 멤버
            )

    def test_assign_todo_order_calculation(self, todo_service, team, user, member_teamuser):
        """할당 시 order가 멤버별로 올바르게 계산되는지 확인"""
        # 멤버에게 이미 2개의 Todo 할당
        Todo.objects.create(team=team, content='Todo 1', assignee=member_teamuser, order=1)
        Todo.objects.create(team=team, content='Todo 2', assignee=member_teamuser, order=2)

        # 새 Todo 생성 후 할당
        new_todo = Todo.objects.create(team=team, content='New Todo')

        result = todo_service.assign_todo(
            todo_id=new_todo.id,
            assignee_id=member_teamuser.id,
            team=team,
            requester=user
        )

        assert result.order == 3  # 마지막 순서

    def test_assign_todo_nonexistent_member(self, todo_service, team, user):
        """존재하지 않는 멤버에게 할당 시도"""
        todo = Todo.objects.create(team=team, content='Test')

        with pytest.raises(Http404):
            todo_service.assign_todo(
                todo_id=todo.id,
                assignee_id=9999,  # 존재하지 않는 ID
                team=team,
                requester=user
            )


class TestTodoServiceCompleteTodo:
    """complete_todo 메서드 테스트"""

    def test_complete_todo_by_assignee(self, todo_service, team, another_user, member_teamuser):
        """할당받은 멤버가 완료 토글"""
        todo = Todo.objects.create(
            team=team,
            content='Test',
            assignee=member_teamuser
        )

        result, is_completed = todo_service.complete_todo(
            todo_id=todo.id,
            team=team,
            requester=another_user
        )

        assert is_completed is True
        assert result.completed_at is not None

    def test_complete_todo_by_host(self, todo_service, team, user, member_teamuser):
        """팀장이 완료 토글"""
        todo = Todo.objects.create(
            team=team,
            content='Test',
            assignee=member_teamuser
        )

        result, is_completed = todo_service.complete_todo(
            todo_id=todo.id,
            team=team,
            requester=user
        )

        assert is_completed is True

    def test_complete_todo_no_permission(self, todo_service, team, member_teamuser, third_user):
        """다른 멤버의 Todo 완료 시도 (실패)"""
        # third_user를 팀에 추가
        from teams.models import TeamUser
        TeamUser.objects.create(team=team, user=third_user)

        todo = Todo.objects.create(
            team=team,
            content='Test',
            assignee=member_teamuser
        )

        with pytest.raises(ValueError, match='권한이 없습니다'):
            todo_service.complete_todo(
                todo_id=todo.id,
                team=team,
                requester=third_user  # 다른 멤버
            )


class TestTodoServiceMoveToTodo:
    """move_to_todo 메서드 테스트"""

    def test_move_to_todo_by_host(self, todo_service, team, user, member_teamuser):
        """팀장이 TODO 보드로 이동"""
        todo = Todo.objects.create(
            team=team,
            content='Test',
            assignee=member_teamuser,
            is_completed=True
        )

        result = todo_service.move_to_todo(
            todo_id=todo.id,
            team=team,
            requester=user
        )

        assert result.assignee is None
        assert result.is_completed is False
        assert result.completed_at is None

    def test_move_to_todo_by_assignee(self, todo_service, team, another_user, member_teamuser):
        """할당받은 멤버가 TODO 보드로 이동"""
        todo = Todo.objects.create(
            team=team,
            content='Test',
            assignee=member_teamuser
        )

        result = todo_service.move_to_todo(
            todo_id=todo.id,
            team=team,
            requester=another_user
        )

        assert result.assignee is None

    def test_move_to_todo_order_calculation(self, todo_service, team, user, member_teamuser):
        """TODO 보드로 이동 시 order 계산"""
        # TODO 보드에 이미 2개 존재
        Todo.objects.create(team=team, content='Todo 1', order=1)
        Todo.objects.create(team=team, content='Todo 2', order=2)

        # 할당된 Todo를 TODO 보드로 이동
        todo = Todo.objects.create(
            team=team,
            content='Test',
            assignee=member_teamuser
        )

        result = todo_service.move_to_todo(
            todo_id=todo.id,
            team=team,
            requester=user
        )

        assert result.order == 3  # 마지막 순서


class TestTodoServiceMoveToDone:
    """move_to_done 메서드 테스트"""

    def test_move_to_done_by_host(self, todo_service, team, user, member_teamuser):
        """팀장이 DONE 보드로 이동"""
        todo = Todo.objects.create(
            team=team,
            content='Test',
            assignee=member_teamuser
        )

        result = todo_service.move_to_done(
            todo_id=todo.id,
            team=team,
            requester=user
        )

        assert result.assignee is None
        assert result.is_completed is True
        assert result.completed_at is not None

    def test_move_to_done_by_assignee(self, todo_service, team, another_user, member_teamuser):
        """할당받은 멤버가 DONE 보드로 이동"""
        todo = Todo.objects.create(
            team=team,
            content='Test',
            assignee=member_teamuser
        )

        result = todo_service.move_to_done(
            todo_id=todo.id,
            team=team,
            requester=another_user
        )

        assert result.is_completed is True

    def test_move_to_done_order_calculation(self, todo_service, team, user, member_teamuser):
        """DONE 보드로 이동 시 order 계산"""
        # DONE 보드에 이미 2개 존재
        Todo.objects.create(team=team, content='Done 1', is_completed=True, order=1)
        Todo.objects.create(team=team, content='Done 2', is_completed=True, order=2)

        # 할당된 Todo를 DONE 보드로 이동
        todo = Todo.objects.create(
            team=team,
            content='Test',
            assignee=member_teamuser
        )

        result = todo_service.move_to_done(
            todo_id=todo.id,
            team=team,
            requester=user
        )

        assert result.order == 3  # 마지막 순서


class TestTodoServiceDeleteTodo:
    """delete_todo 메서드 테스트"""

    def test_delete_todo_success(self, todo_service, team):
        """Todo 삭제 성공"""
        todo = Todo.objects.create(team=team, content='Test Todo')

        content = todo_service.delete_todo(
            todo_id=todo.id,
            team=team
        )

        assert content == 'Test Todo'
        assert not Todo.objects.filter(id=todo.id).exists()

    def test_delete_todo_nonexistent(self, todo_service, team):
        """존재하지 않는 Todo 삭제 시도"""
        with pytest.raises(Http404):
            todo_service.delete_todo(
                todo_id=9999,
                team=team
            )


class TestTodoServiceGetTeamTodosWithStats:
    """get_team_todos_with_stats 메서드 테스트"""

    def test_get_team_todos_with_stats_basic(self, todo_service, team, member_teamuser):
        """팀 Todo 및 통계 조회"""
        # 다양한 상태의 Todo 생성
        Todo.objects.create(team=team, content='Unassigned 1')
        Todo.objects.create(team=team, content='Done 1', is_completed=True)
        Todo.objects.create(team=team, content='Member Todo', assignee=member_teamuser)
        Todo.objects.create(team=team, content='Member Done', assignee=member_teamuser, is_completed=True)

        result = todo_service.get_team_todos_with_stats(team)

        assert result['todos_unassigned'].count() == 1  # Unassigned 1
        assert result['todos_done'].count() == 1  # Done 1
        assert result['members'].count() == 2  # host + member

        # 멤버 통계 확인
        member_data = next(m for m in result['members_data'] if m['member'] == member_teamuser)
        assert member_data['todo_count'] == 2  # 2개 할당
        assert member_data['completed_count'] == 1  # 1개 완료
        assert member_data['in_progress_count'] == 1  # 1개 진행 중

    def test_get_team_todos_with_stats_empty(self, todo_service, team):
        """빈 팀의 Todo 조회"""
        result = todo_service.get_team_todos_with_stats(team)

        assert result['todos_unassigned'].count() == 0
        assert result['todos_done'].count() == 0
        assert result['members'].count() == 1  # host만 존재
