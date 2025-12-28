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

        result, metadata = todo_service.complete_todo(
            todo_id=todo.id,
            team=team,
            requester=another_user
        )

        assert metadata['is_completed'] is True
        assert metadata['was_completed'] is False
        assert result.completed_at is not None

    def test_complete_todo_by_host(self, todo_service, team, user, member_teamuser):
        """팀장이 완료 토글"""
        todo = Todo.objects.create(
            team=team,
            content='Test',
            assignee=member_teamuser
        )

        result, metadata = todo_service.complete_todo(
            todo_id=todo.id,
            team=team,
            requester=user
        )

        assert metadata['is_completed'] is True
        assert metadata['was_completed'] is False

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


class TestTodoServiceMilestoneIntegration:
    """TODO-마일스톤 연동 테스트 (12개)"""

    def test_assign_todo_to_milestone(self, todo_service, team):
        """TODO 할당"""
        from datetime import date, timedelta
        from teams.models import Milestone

        milestone = Milestone.objects.create(
            team=team,
            title='마일스톤 1',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        todo = Todo.objects.create(team=team, content='TODO 1')

        updated_todo, result = todo_service.assign_to_milestone(todo.id, milestone.id, team)

        assert updated_todo.milestone == milestone
        assert result['milestone_changed'] is True
        assert result['new_milestone_id'] == milestone.id
        assert result['old_milestone_id'] is None

    def test_assign_todo_updates_milestone_progress(self, todo_service, team):
        """할당 시 진행률 갱신 (AUTO)"""
        from datetime import date, timedelta
        from teams.models import Milestone

        milestone = Milestone.objects.create(
            team=team,
            title='마일스톤 1',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        todo1 = Todo.objects.create(team=team, content='TODO 1', is_completed=True)
        todo2 = Todo.objects.create(team=team, content='TODO 2', is_completed=False)

        # TODO 1 할당 (완료됨)
        todo_service.assign_to_milestone(todo1.id, milestone.id, team)

        # TODO 2 할당 (미완료)
        updated_todo, result = todo_service.assign_to_milestone(todo2.id, milestone.id, team)

        # 진행률 확인 (1/2 = 50%)
        milestone.refresh_from_db()
        assert milestone.progress_percentage == 50

    def test_assign_todo_to_milestone_already_assigned_raises(self, todo_service, team):
        """중복 할당 에러"""
        from datetime import date, timedelta
        from teams.models import Milestone

        milestone = Milestone.objects.create(
            team=team,
            title='마일스톤 1',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        todo = Todo.objects.create(team=team, content='TODO 1', milestone=milestone)

        with pytest.raises(ValueError, match='이미 해당 마일스톤에 할당된 TODO'):
            todo_service.assign_to_milestone(todo.id, milestone.id, team)

    def test_assign_todo_from_one_milestone_to_another(self, todo_service, team):
        """마일스톤 변경"""
        from datetime import date, timedelta
        from teams.models import Milestone

        milestone1 = Milestone.objects.create(
            team=team,
            title='마일스톤 1',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        milestone2 = Milestone.objects.create(
            team=team,
            title='마일스톤 2',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=14),
            priority='medium',
            progress_mode='auto'
        )

        todo = Todo.objects.create(team=team, content='TODO 1', milestone=milestone1)

        updated_todo, result = todo_service.assign_to_milestone(todo.id, milestone2.id, team)

        assert updated_todo.milestone == milestone2
        assert result['old_milestone_id'] == milestone1.id
        assert result['new_milestone_id'] == milestone2.id

    def test_assign_todo_updates_old_and_new_milestone(self, todo_service, team):
        """변경 시 양쪽 진행률 갱신"""
        from datetime import date, timedelta
        from teams.models import Milestone

        milestone1 = Milestone.objects.create(
            team=team,
            title='마일스톤 1',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        milestone2 = Milestone.objects.create(
            team=team,
            title='마일스톤 2',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=14),
            priority='medium',
            progress_mode='auto'
        )

        # 마일스톤1에 TODO 2개 (1개 완료)
        todo1 = Todo.objects.create(team=team, content='TODO 1', milestone=milestone1, is_completed=True)
        todo2 = Todo.objects.create(team=team, content='TODO 2', milestone=milestone1, is_completed=False)

        # todo1을 마일스톤2로 이동
        updated_todo, result = todo_service.assign_to_milestone(todo1.id, milestone2.id, team)

        # 양쪽 마일스톤 진행률 확인
        milestone1.refresh_from_db()
        milestone2.refresh_from_db()

        assert milestone1.progress_percentage == 0  # 0/1 = 0%
        assert milestone2.progress_percentage == 100  # 1/1 = 100%
        assert result['old_milestone_updated'] is True
        assert result['new_milestone_updated'] is True

    def test_detach_todo_from_milestone(self, todo_service, team):
        """연결 해제"""
        from datetime import date, timedelta
        from teams.models import Milestone

        milestone = Milestone.objects.create(
            team=team,
            title='마일스톤 1',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        todo = Todo.objects.create(team=team, content='TODO 1', milestone=milestone)

        updated_todo, result = todo_service.detach_from_milestone(todo.id, team)

        assert updated_todo.milestone is None
        assert result['detached'] is True
        assert result['old_milestone_id'] == milestone.id

    def test_detach_todo_not_in_milestone_raises(self, todo_service, team):
        """연결 안 된 TODO 해제 시도"""
        todo = Todo.objects.create(team=team, content='TODO 1')

        with pytest.raises(ValueError, match='TODO가 마일스톤에 할당되어 있지 않습니다'):
            todo_service.detach_from_milestone(todo.id, team)

    def test_complete_todo_updates_milestone_progress(self, todo_service, team, user):
        """완료 시 진행률 갱신"""
        from datetime import date, timedelta
        from teams.models import Milestone

        milestone = Milestone.objects.create(
            team=team,
            title='마일스톤 1',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        # TODO 3개 생성 (모두 미완료)
        todo1 = Todo.objects.create(team=team, content='TODO 1', milestone=milestone)
        todo2 = Todo.objects.create(team=team, content='TODO 2', milestone=milestone)
        todo3 = Todo.objects.create(team=team, content='TODO 3', milestone=milestone)

        # todo1 완료
        updated_todo, result = todo_service.complete_todo(todo1.id, team, user)

        # 검증
        milestone.refresh_from_db()
        assert result['milestone_updated'] is True
        assert result['milestone_id'] == milestone.id
        assert result['milestone_progress'] == 33  # 1/3 = 33%
        assert milestone.progress_percentage == 33

    def test_complete_todo_in_manual_mode_no_update(self, todo_service, team, user):
        """수동 모드는 영향 없음"""
        from datetime import date, timedelta
        from teams.models import Milestone

        milestone = Milestone.objects.create(
            team=team,
            title='마일스톤 1',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='manual',
            progress_percentage=50
        )

        todo = Todo.objects.create(team=team, content='TODO 1', milestone=milestone)

        # TODO 완료
        updated_todo, result = todo_service.complete_todo(todo.id, team, user)

        # 검증: 수동 모드는 진행률이 변경되지 않음
        milestone.refresh_from_db()
        assert result['milestone_updated'] is False
        assert milestone.progress_percentage == 50  # 변경 없음

    def test_complete_all_todos_completes_milestone(self, todo_service, team, user):
        """모든 TODO 완료 시 마일스톤 완료"""
        from datetime import date, timedelta
        from teams.models import Milestone

        milestone = Milestone.objects.create(
            team=team,
            title='마일스톤 1',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        # TODO 2개 생성
        todo1 = Todo.objects.create(team=team, content='TODO 1', milestone=milestone)
        todo2 = Todo.objects.create(team=team, content='TODO 2', milestone=milestone)

        # 모두 완료
        todo_service.complete_todo(todo1.id, team, user)
        todo_service.complete_todo(todo2.id, team, user)

        # 검증: 마일스톤 자동 완료
        milestone.refresh_from_db()
        assert milestone.progress_percentage == 100
        assert milestone.is_completed is True
        assert milestone.completed_date is not None

    def test_uncomplete_todo_decreases_progress(self, todo_service, team, user):
        """완료 취소 시 진행률 감소"""
        from datetime import date, timedelta
        from teams.models import Milestone

        milestone = Milestone.objects.create(
            team=team,
            title='마일스톤 1',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        # TODO 2개 생성 (모두 완료)
        todo1 = Todo.objects.create(team=team, content='TODO 1', milestone=milestone, is_completed=True)
        todo2 = Todo.objects.create(team=team, content='TODO 2', milestone=milestone, is_completed=True)

        milestone.update_progress_from_todos()
        milestone.refresh_from_db()
        assert milestone.progress_percentage == 100

        # todo1 완료 취소 (토글)
        updated_todo, result = todo_service.complete_todo(todo1.id, team, user)

        # 검증
        milestone.refresh_from_db()
        assert result['was_completed'] is True
        assert result['is_completed'] is False
        assert result['milestone_progress'] == 50  # 1/2 = 50%
        assert milestone.progress_percentage == 50

    def test_assign_none_detaches_milestone(self, todo_service, team):
        """milestone_id=None 전달 시 해제"""
        from datetime import date, timedelta
        from teams.models import Milestone

        milestone = Milestone.objects.create(
            team=team,
            title='마일스톤 1',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        todo = Todo.objects.create(team=team, content='TODO 1', milestone=milestone)

        # milestone_id=None으로 assign 호출
        updated_todo, result = todo_service.assign_to_milestone(todo.id, None, team)

        # detach_from_milestone()이 호출되어야 함
        assert updated_todo.milestone is None
        assert result['detached'] is True
