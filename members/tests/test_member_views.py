"""
Members SSR 뷰 테스트
총 3개 테스트:
- TeamMembersPageView GET: 1개
- TeamMembersPageView POST: 2개
"""
import pytest
from django.urls import reverse
from django.contrib.messages import get_messages
from members.models import Todo


pytestmark = pytest.mark.django_db


class TestTeamMembersPageView:
    """team_members_page SSR 뷰 테스트"""

    def test_get_team_members_page(self, client, user, team, member_teamuser):
        """팀 멤버 페이지 GET 요청 - 초기 로드"""
        client.force_login(user)
        url = reverse('members:team_members_page', kwargs={'pk': team.id})

        response = client.get(url)

        assert response.status_code == 200
        assert 'members' in response.context
        assert 'todos_unassigned' in response.context
        assert 'todos_done' in response.context
        assert 'form' in response.context
        assert 'is_host' in response.context
        assert response.context['is_host'] is True  # user는 팀장

    def test_post_create_todo_success(self, client, user, team):
        """POST 요청으로 Todo 생성 성공"""
        client.force_login(user)
        url = reverse('members:team_members_page', kwargs={'pk': team.id})
        data = {'content': 'New Todo from Form'}

        response = client.post(url, data)

        assert response.status_code == 302  # 리다이렉트
        assert Todo.objects.filter(team=team, content='New Todo from Form').exists()

        # 성공 메시지 확인
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert '성공적으로 추가되었습니다' in str(messages[0])

    def test_post_create_todo_empty_content(self, client, user, team):
        """POST 요청으로 빈 Todo 생성 시도 (실패)"""
        client.force_login(user)
        url = reverse('members:team_members_page', kwargs={'pk': team.id})
        data = {'content': '   '}  # 공백만

        response = client.post(url, data)

        assert response.status_code == 302
        assert not Todo.objects.filter(team=team).exists()

        # 에러 메시지 확인
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert '할 일 내용을 입력해주세요' in str(messages[0])
