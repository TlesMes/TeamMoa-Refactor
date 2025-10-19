"""
TodoViewSet API 테스트
총 10개 테스트:
- assign: 3개
- complete: 3개
- move_to_todo: 2개
- move_to_done: 2개

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
