"""
TodoViewSet API 테스트
총 16개 테스트:
- assign: 3개
- complete: 3개
- move_to_todo: 2개
- move_to_done: 2개
- assign_milestone: 3개 (Phase 3)
- detach_milestone: 3개 (Phase 3)

참고: create, list, retrieve, update 액션은 프론트엔드에서 사용하지 않아 테스트 제외
"""
import pytest
from django.urls import reverse
from rest_framework import status


pytestmark = pytest.mark.django_db


class TestTodoViewSetAssign:
    """POST /api/teams/{team_pk}/todos/{pk}/assign/ - Todo 할당"""

    def test_assign_todo_by_host(self, authenticated_client, team, unassigned_todo, member_teamuser):
        """팀장이 멤버에게 할당"""
        url = reverse('api:team-todos-assign', kwargs={'team_pk': team.id, 'pk': unassigned_todo.id})
        data = {'member_id': member_teamuser.id}

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['todo']['assignee_id'] == member_teamuser.id

        unassigned_todo.refresh_from_db()
        assert unassigned_todo.assignee == member_teamuser

    def test_assign_todo_self_assign(self, api_client, team, another_user, unassigned_todo, member_teamuser):
        """일반 멤버가 본인에게 할당"""
        api_client.force_authenticate(user=another_user)
        url = reverse('api:team-todos-assign', kwargs={'team_pk': team.id, 'pk': unassigned_todo.id})
        data = {'member_id': member_teamuser.id}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['todo']['assignee_id'] == member_teamuser.id

    def test_assign_todo_invalid_member(self, authenticated_client, team, unassigned_todo):
        """존재하지 않는 멤버에게 할당 시도"""
        url = reverse('api:team-todos-assign', kwargs={'team_pk': team.id, 'pk': unassigned_todo.id})
        data = {'member_id': 9999}

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestTodoViewSetComplete:
    """POST /api/teams/{team_pk}/todos/{pk}/complete/ - Todo 완료 토글"""

    def test_complete_todo_by_assignee(self, api_client, team, another_user, assigned_todo):
        """할당받은 멤버가 완료"""
        api_client.force_authenticate(user=another_user)
        url = reverse('api:team-todos-complete', kwargs={'team_pk': team.id, 'pk': assigned_todo.id})

        response = api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['is_completed'] is True

        assigned_todo.refresh_from_db()
        assert assigned_todo.is_completed is True

    def test_complete_todo_by_host(self, authenticated_client, team, assigned_todo):
        """팀장이 완료"""
        url = reverse('api:team-todos-complete', kwargs={'team_pk': team.id, 'pk': assigned_todo.id})

        response = authenticated_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_completed'] is True

    def test_complete_todo_toggle(self, api_client, team, another_user, assigned_todo):
        """완료 토글 동작 확인"""
        api_client.force_authenticate(user=another_user)
        url = reverse('api:team-todos-complete', kwargs={'team_pk': team.id, 'pk': assigned_todo.id})

        # 첫 번째 호출: 미완료 → 완료
        response1 = api_client.post(url, {}, format='json')
        assert response1.data['is_completed'] is True

        # 두 번째 호출: 완료 → 미완료
        response2 = api_client.post(url, {}, format='json')
        assert response2.data['is_completed'] is False


class TestTodoViewSetMoveToTodo:
    """POST /api/teams/{team_pk}/todos/{pk}/move-to-todo/ - TODO 보드로 이동"""

    def test_move_to_todo_from_member_board(self, authenticated_client, team, assigned_todo):
        """멤버 보드에서 TODO 보드로 이동"""
        url = reverse('api:team-todos-move-to-todo', kwargs={'team_pk': team.id, 'pk': assigned_todo.id})

        response = authenticated_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

        assigned_todo.refresh_from_db()
        assert assigned_todo.assignee is None
        assert assigned_todo.is_completed is False

    def test_move_to_todo_from_done_board(self, authenticated_client, team, completed_todo):
        """DONE 보드에서 TODO 보드로 이동"""
        url = reverse('api:team-todos-move-to-todo', kwargs={'team_pk': team.id, 'pk': completed_todo.id})

        response = authenticated_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK

        completed_todo.refresh_from_db()
        assert completed_todo.is_completed is False


class TestTodoViewSetMoveToDone:
    """POST /api/teams/{team_pk}/todos/{pk}/move-to-done/ - DONE 보드로 이동"""

    def test_move_to_done_from_member_board(self, authenticated_client, team, assigned_todo):
        """멤버 보드에서 DONE 보드로 이동"""
        url = reverse('api:team-todos-move-to-done', kwargs={'team_pk': team.id, 'pk': assigned_todo.id})

        response = authenticated_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

        assigned_todo.refresh_from_db()
        assert assigned_todo.assignee is None
        assert assigned_todo.is_completed is True

    def test_move_to_done_from_todo_board(self, authenticated_client, team, unassigned_todo):
        """TODO 보드에서 DONE 보드로 이동"""
        url = reverse('api:team-todos-move-to-done', kwargs={'team_pk': team.id, 'pk': unassigned_todo.id})

        response = authenticated_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK

        unassigned_todo.refresh_from_db()
        assert unassigned_todo.is_completed is True


class TestTodoViewSetMilestoneIntegration:
    """TODO-마일스톤 연동 API 테스트 (Phase 3)"""

    def test_assign_todo_to_milestone(self, authenticated_client, team, user):
        """TODO를 마일스톤에 할당"""
        from teams.models import Milestone
        from members.models import Todo
        from datetime import date, timedelta

        milestone = Milestone.objects.create(
            team=team,
            title='Sprint 1',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )
        todo = Todo.objects.create(team=team, content='Feature A', is_completed=False)

        url = reverse('api:team-todos-assign-milestone', kwargs={'team_pk': team.id, 'pk': todo.id})
        data = {'milestone_id': milestone.id}

        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['todo']['milestone_id'] == milestone.id
        assert response.data['todo']['milestone_title'] == 'Sprint 1'
        assert response.data['metadata']['milestone_changed'] is True

        todo.refresh_from_db()
        assert todo.milestone_id == milestone.id

    def test_assign_todo_to_invalid_milestone(self, authenticated_client, team):
        """존재하지 않는 마일스톤에 할당 시도"""
        from members.models import Todo

        todo = Todo.objects.create(team=team, content='Feature B', is_completed=False)
        url = reverse('api:team-todos-assign-milestone', kwargs={'team_pk': team.id, 'pk': todo.id})
        data = {'milestone_id': 9999}

        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_assign_todo_updates_milestone_progress(self, authenticated_client, team, user):
        """TODO 할당 시 마일스톤 진행률 자동 갱신 (AUTO 모드)"""
        from teams.models import Milestone
        from members.models import Todo
        from datetime import date, timedelta

        milestone = Milestone.objects.create(
            team=team,
            title='Sprint 2',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto',
            progress_percentage=0
        )

        # 기존 TODO 1개 (완료)
        Todo.objects.create(team=team, content='TODO 1', milestone=milestone, is_completed=True)

        # 새 TODO 추가
        new_todo = Todo.objects.create(team=team, content='TODO 2', is_completed=False)

        url = reverse('api:team-todos-assign-milestone', kwargs={'team_pk': team.id, 'pk': new_todo.id})
        data = {'milestone_id': milestone.id}

        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        milestone.refresh_from_db()
        assert milestone.progress_percentage == 50  # 1/2 = 50%

    def test_detach_todo_from_milestone(self, authenticated_client, team):
        """TODO를 마일스톤에서 분리"""
        from teams.models import Milestone
        from members.models import Todo
        from datetime import date, timedelta

        milestone = Milestone.objects.create(
            team=team,
            title='Sprint 3',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )
        todo = Todo.objects.create(
            team=team,
            content='Feature C',
            milestone=milestone,
            is_completed=False
        )

        url = reverse('api:team-todos-detach-milestone', kwargs={'team_pk': team.id, 'pk': todo.id})

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['metadata']['detached'] is True
        assert response.data['todo']['milestone_id'] is None

        todo.refresh_from_db()
        assert todo.milestone is None

    def test_detach_todo_updates_milestone_progress(self, authenticated_client, team):
        """TODO 분리 시 마일스톤 진행률 자동 갱신 (AUTO 모드)"""
        from teams.models import Milestone
        from members.models import Todo
        from datetime import date, timedelta

        milestone = Milestone.objects.create(
            team=team,
            title='Sprint 4',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        # TODO 2개 생성 (1개 완료)
        todo1 = Todo.objects.create(team=team, content='TODO 1', milestone=milestone, is_completed=True)
        todo2 = Todo.objects.create(team=team, content='TODO 2', milestone=milestone, is_completed=False)

        # 진행률: 1/2 = 50%
        assert milestone.progress_percentage == 50

        # TODO 1개 분리
        url = reverse('api:team-todos-detach-milestone', kwargs={'team_pk': team.id, 'pk': todo2.id})
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        milestone.refresh_from_db()
        assert milestone.progress_percentage == 100  # 1/1 = 100%

    def test_detach_todo_with_no_milestone(self, authenticated_client, team):
        """마일스톤이 없는 TODO 분리 시도"""
        from members.models import Todo

        todo = Todo.objects.create(team=team, content='Feature D', is_completed=False)
        url = reverse('api:team-todos-detach-milestone', kwargs={'team_pk': team.id, 'pk': todo.id})

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
