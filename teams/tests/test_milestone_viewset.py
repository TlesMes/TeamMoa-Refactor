"""
MilestoneViewSet API 엔드포인트 테스트

✅ 실제 사용 중 - 전체 테스트 유지
JavaScript: static/js/pages/milestone_timeline.js

사용 현황:
- list: ❌ 미사용 (서버 렌더링) - 테스트는 유지 (API 정합성 확인)
- create: ✅ 사용 (teamApi.createMilestone)
- partial_update: ✅ 사용 (teamApi.updateMilestone - 드래그 앤 드롭)
- destroy: ✅ 사용 (teamApi.deleteMilestone)
"""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from teams.models import Milestone


@pytest.mark.api
class TestMilestoneViewSetList:
    """마일스톤 목록 조회 API 테스트"""

    def test_list_milestones(self, authenticated_client, team, milestone, completed_milestone):
        """마일스톤 목록 조회 (정렬 확인)"""
        url = reverse('api:team-milestones-list', kwargs={'team_pk': team.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        # 우선순위 순으로 정렬 확인 (high → medium)
        priorities = [m['priority'] for m in response.data]
        assert priorities == ['high', 'medium']

    def test_list_milestones_empty(self, authenticated_client, team):
        """마일스톤이 없는 팀"""
        url = reverse('api:team-milestones-list', kwargs={'team_pk': team.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


@pytest.mark.api
class TestMilestoneViewSetCreate:
    """마일스톤 생성 API 테스트"""

    def test_create_milestone_success(self, authenticated_client, team):
        """정상적으로 마일스톤 생성"""
        url = reverse('api:team-milestones-list', kwargs={'team_pk': team.id})
        today = date.today()
        data = {
            'title': 'API 마일스톤',
            'description': 'API로 생성한 마일스톤',
            'startdate': str(today),
            'enddate': str(today + timedelta(days=7)),
            'priority': 'critical'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['milestone']['title'] == 'API 마일스톤'
        assert '"API 마일스톤" 마일스톤이 생성되었습니다' in response.data['messages'][0]['message']

        # DB에 실제로 생성되었는지 확인
        assert Milestone.objects.filter(title='API 마일스톤').exists()

    def test_create_milestone_with_invalid_dates(self, authenticated_client, team):
        """시작일이 종료일보다 늦을 때 실패"""
        url = reverse('api:team-milestones-list', kwargs={'team_pk': team.id})
        today = date.today()
        data = {
            'title': '잘못된 마일스톤',
            'description': '설명',
            'startdate': str(today + timedelta(days=10)),
            'enddate': str(today),
            'priority': 'medium'
        }
        response = authenticated_client.post(url, data, format='json')

        details = response.data.get('details', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert details['enddate'][0] == '종료일은 시작일보다 이후여야 합니다.'

    def test_create_milestone_missing_required_fields(self, authenticated_client, team):
        """필수 필드 누락 시 실패"""
        url = reverse('api:team-milestones-list', kwargs={'team_pk': team.id})
        data = {
            'title': '제목만 있는 마일스톤'
            # startdate, enddate, priority 누락
        }
        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.api
class TestMilestoneViewSetUpdate:
    """마일스톤 수정 API 테스트"""

    def test_partial_update_milestone_progress(self, authenticated_client, team, milestone):
        """진행률 업데이트"""
        url = reverse('api:team-milestones-detail', kwargs={
            'team_pk': team.id,
            'pk': milestone.id
        })
        data = {'progress_percentage': 75}
        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['milestone']['progress_percentage'] == 75
        assert len(response.data['messages']) > 0
        assert '진행률' in response.data['messages'][0]['message']

    def test_partial_update_milestone_dates(self, authenticated_client, team, milestone):
        """날짜 수정"""
        url = reverse('api:team-milestones-detail', kwargs={
            'team_pk': team.id,
            'pk': milestone.id
        })
        new_enddate = date.today() + timedelta(days=20)
        data = {'enddate': str(new_enddate)}
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['messages']) > 0
        assert '종료일' in response.data['messages'][0]['message']

    def test_partial_update_milestone_to_100_percent(self, authenticated_client, team, milestone):
        """진행률 100%로 업데이트 시 완료 처리"""
        url = reverse('api:team-milestones-detail', kwargs={
            'team_pk': team.id,
            'pk': milestone.id
        })
        data = {'progress_percentage': 100}
        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['milestone']['is_completed'] is True
        assert len(response.data['messages']) > 0
        assert '완료 상태' in response.data['messages'][0]['message']


@pytest.mark.api
class TestMilestoneViewSetDestroy:
    """마일스톤 삭제 API 테스트"""

    def test_destroy_milestone(self, authenticated_client, team, milestone):
        """마일스톤 삭제"""
        milestone_id = milestone.id
        url = reverse('api:team-milestones-detail', kwargs={
            'team_pk': team.id,
            'pk': milestone_id
        })
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['messages']) > 0
        assert '테스트 마일스톤' in response.data['messages'][0]['message']
        assert not Milestone.objects.filter(id=milestone_id).exists()
