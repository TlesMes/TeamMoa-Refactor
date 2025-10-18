"""
TeamViewSet API 엔드포인트 테스트

✅ 테스트 대상:
- TeamViewSet.remove_member: 팀 메인 페이지에서 사용 (team_main.js)
  엔드포인트: DELETE /api/v1/teams/<pk>/members/<user_id>/

❌ 테스트 제외 (SSR로 처리):
- list/create/retrieve/update/destroy → Form 기반 SSR 뷰
- statistics → 템플릿에서 직접 계산

참고: MilestoneViewSet 테스트는 test_milestone_viewset.py 참고
"""
import pytest
from rest_framework import status
from teams.models import TeamUser


@pytest.mark.api
class TestTeamViewSetRemoveMember:
    """
    팀 멤버 제거 API 테스트 (추방/탈퇴)

    JavaScript: static/js/pages/team_main.js - removeMember()
    엔드포인트: DELETE /api/v1/teams/<pk>/members/<user_id>/
    """

    def test_host_remove_member_success(self, api_client, team, another_user, user):
        """팀장이 멤버를 추방할 수 있다"""
        # another_user를 팀에 추가
        TeamUser.objects.create(team=team, user=another_user)
        team.currentuser += 1
        team.save()

        # user는 팀장(host)
        api_client.force_authenticate(user=user)
        url = f'/api/v1/teams/{team.id}/members/{another_user.id}/'
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['messages']) > 0
        assert '추방' in response.data['messages'][0]['message']

        # DB에서 실제로 제거되었는지 확인
        assert not TeamUser.objects.filter(team=team, user=another_user).exists()

        # currentuser 감소 확인
        team.refresh_from_db()
        assert team.currentuser == 1

    def test_member_leave_team_success(self, api_client, team, another_user):
        """일반 멤버가 본인 탈퇴를 할 수 있다"""
        # another_user를 팀에 추가
        TeamUser.objects.create(team=team, user=another_user)
        team.currentuser += 1
        team.save()

        # another_user가 본인 탈퇴
        api_client.force_authenticate(user=another_user)
        url = f'/api/v1/teams/{team.id}/members/{another_user.id}/'
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert '탈퇴' in response.data['messages'][0]['message']

        # DB에서 실제로 제거되었는지 확인
        assert not TeamUser.objects.filter(team=team, user=another_user).exists()

    def test_non_host_cannot_remove_others(self, api_client, team, another_user, third_user):
        """일반 멤버는 다른 사람을 추방할 수 없다"""
        # 두 멤버를 팀에 추가
        TeamUser.objects.create(team=team, user=another_user)
        TeamUser.objects.create(team=team, user=third_user)
        team.currentuser += 2
        team.save()

        # another_user가 third_user를 추방 시도
        api_client.force_authenticate(user=another_user)
        url = f'/api/v1/teams/{team.id}/members/{third_user.id}/'
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert len(response.data['messages']) > 0
        assert '권한' in response.data['messages'][0]['message'] or '팀장' in response.data['messages'][0]['message']

        # third_user는 여전히 팀에 속해있어야 함
        assert TeamUser.objects.filter(team=team, user=third_user).exists()
