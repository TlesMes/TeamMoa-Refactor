"""
Teams 마일스톤 API 테스트 (16개)

테스트 구성:
- TestMilestoneViewSet: 9개 - 목록, 생성, 수정, 삭제 API
- TestMilestoneAPIProgressMode: 7개 - 진행률 모드 관련 API (Phase 3)

사용 위치:
- JavaScript: static/js/pages/milestone_timeline.js
- API 엔드포인트: /api/v1/teams/{pk}/milestones/

사용 현황:
- list: ❌ 미사용 (서버 렌더링) - 테스트는 유지 (API 정합성 확인)
- create: ✅ 사용 (teamApi.createMilestone)
- partial_update: ✅ 사용 (teamApi.updateMilestone - 드래그 앤 드롭)
- destroy: ✅ 사용 (teamApi.deleteMilestone)
- toggle_progress_mode: ✅ 사용 (Phase 3 - 진행률 모드 전환)
- milestone_with_stats: ✅ 사용 (Phase 3 - TODO 통계 조회)
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


@pytest.mark.api
class TestMilestoneAPIProgressMode:
    """MilestoneViewSet 진행률 모드 API 테스트 (Phase 3)"""

    def test_create_milestone_with_auto_mode(self, authenticated_client, team):
        """AUTO 모드로 마일스톤 생성"""
        url = reverse('api:team-milestones-list', kwargs={'team_pk': team.id})
        data = {
            'title': 'Sprint 1',
            'description': 'First sprint',
            'startdate': str(date.today()),
            'enddate': str(date.today() + timedelta(days=14)),
            'priority': 'high',
            'progress_mode': 'auto'
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['milestone']['progress_mode'] == 'auto'
        assert response.data['milestone']['progress_mode_display'] == 'TODO 기반 자동 계산'
        assert response.data['milestone']['progress_percentage'] == 0

    def test_create_milestone_default_mode_is_auto(self, authenticated_client, team):
        """progress_mode 미지정 시 기본값 'auto'"""
        url = reverse('api:team-milestones-list', kwargs={'team_pk': team.id})
        data = {
            'title': 'Sprint 2',
            'description': 'Second sprint',
            'startdate': str(date.today()),
            'enddate': str(date.today() + timedelta(days=14)),
            'priority': 'medium'
            # progress_mode 생략
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['milestone']['progress_mode'] == 'auto'

    def test_create_milestone_with_manual_mode(self, authenticated_client, team):
        """수동 모드로 마일스톤 생성"""
        url = reverse('api:team-milestones-list', kwargs={'team_pk': team.id})
        data = {
            'title': 'Sprint 3',
            'description': 'Third sprint',
            'startdate': str(date.today()),
            'enddate': str(date.today() + timedelta(days=14)),
            'priority': 'low',
            'progress_mode': 'manual'
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['milestone']['progress_mode'] == 'manual'
        assert response.data['milestone']['progress_mode_display'] == '수동 입력'

    def test_toggle_progress_mode_manual_to_auto(self, authenticated_client, team, user):
        """수동 → AUTO 모드 전환 (TODO 기반 재계산)"""
        from members.models import Todo

        # 수동 모드 마일스톤 생성
        milestone = Milestone.objects.create(
            team=team,
            title='Manual Milestone',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='manual',
            progress_percentage=50  # 수동 설정
        )

        # TODO 3개 생성 (1개 완료)
        Todo.objects.create(team=team, content='TODO 1', milestone=milestone, is_completed=True)
        Todo.objects.create(team=team, content='TODO 2', milestone=milestone, is_completed=False)
        Todo.objects.create(team=team, content='TODO 3', milestone=milestone, is_completed=False)

        url = reverse('api:team-milestones-progress-mode', kwargs={'team_pk': team.id, 'pk': milestone.id})
        data = {'mode': 'auto'}

        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['milestone']['progress_mode'] == 'auto'
        assert response.data['metadata']['old_mode'] == 'manual'
        assert response.data['metadata']['new_mode'] == 'auto'
        assert response.data['metadata']['progress_recalculated'] is True
        assert response.data['metadata']['new_progress'] == 33  # 1/3 = 33%

    def test_toggle_progress_mode_auto_to_manual(self, authenticated_client, team):
        """AUTO → 수동 모드 전환 (진행률 유지)"""
        # AUTO 모드 마일스톤 생성
        milestone = Milestone.objects.create(
            team=team,
            title='Auto Milestone',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto',
            progress_percentage=40
        )

        url = reverse('api:team-milestones-progress-mode', kwargs={'team_pk': team.id, 'pk': milestone.id})
        data = {'mode': 'manual'}

        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['milestone']['progress_mode'] == 'manual'
        assert response.data['metadata']['old_mode'] == 'auto'
        assert response.data['metadata']['new_mode'] == 'manual'
        assert response.data['metadata']['progress_recalculated'] is False
        assert response.data['metadata']['new_progress'] == 40  # 기존 진행률 유지

    def test_get_milestone_with_stats(self, authenticated_client, team, user):
        """마일스톤 + TODO 통계 조회"""
        from members.models import Todo

        milestone = Milestone.objects.create(
            team=team,
            title='Milestone with TODOs',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        # TODO 5개 생성 (2개 완료)
        Todo.objects.create(team=team, content='TODO 1', milestone=milestone, is_completed=True)
        Todo.objects.create(team=team, content='TODO 2', milestone=milestone, is_completed=True)
        Todo.objects.create(team=team, content='TODO 3', milestone=milestone, is_completed=False)
        Todo.objects.create(team=team, content='TODO 4', milestone=milestone, is_completed=False)
        Todo.objects.create(team=team, content='TODO 5', milestone=milestone, is_completed=False)

        url = reverse('api:team-milestones-with-stats', kwargs={'team_pk': team.id, 'pk': milestone.id})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['milestone']['id'] == milestone.id
        assert response.data['todo_stats']['total'] == 5
        assert response.data['todo_stats']['completed'] == 2
        assert response.data['todo_stats']['in_progress'] == 3
        assert response.data['todo_stats']['completion_rate'] == 40

    def test_update_progress_in_auto_mode_raises_error(self, authenticated_client, team):
        """AUTO 모드에서 진행률 수동 설정 시도 → 에러"""
        milestone = Milestone.objects.create(
            team=team,
            title='Auto Milestone',
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        url = reverse('api:team-milestones-detail', kwargs={'team_pk': team.id, 'pk': milestone.id})
        data = {'progress_percentage': 70}

        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'AUTO 모드에서는 진행률을 수동으로 설정할 수 없습니다' in str(response.data)
