"""
Teams 마일스톤 서비스 레이어 테스트 (14개)

테스트 구성:
- TestMilestoneServiceCreateMilestone: 3개 - 마일스톤 생성, 날짜 유효성 검증
- TestMilestoneServiceUpdateMilestone: 7개 - 날짜/진행률 수정, 완료 처리
- TestMilestoneServiceDeleteMilestone: 1개 - 마일스톤 삭제
- TestMilestoneServiceGetTeamMilestones: 3개 - 목록 조회, 정렬

사용 위치:
- API: MilestoneViewSet (create, partial_update, destroy, list)
- SSR: team_milestone_timeline 뷰
"""
import pytest
from datetime import date, timedelta
from teams.services import MilestoneService
from teams.models import Milestone


@pytest.mark.unit
class TestMilestoneServiceCreateMilestone:
    """마일스톤 생성 메서드 테스트"""

    def setup_method(self):
        self.service = MilestoneService()

    def test_create_milestone_success(self, team):
        """정상적으로 마일스톤 생성"""
        today = date.today()
        milestone = self.service.create_milestone(
            team=team,
            title='새 마일스톤',
            description='새 마일스톤 설명',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='high'
        )

        assert milestone.team == team
        assert milestone.title == '새 마일스톤'
        assert milestone.description == '새 마일스톤 설명'
        assert milestone.priority == 'high'
        assert milestone.startdate == today
        assert milestone.enddate == today + timedelta(days=7)

    def test_create_milestone_with_invalid_dates(self, team):
        """시작일이 종료일보다 늦을 때 실패"""
        today = date.today()
        with pytest.raises(ValueError, match='시작일은 종료일보다 이전이어야 합니다'):
            self.service.create_milestone(
                team=team,
                title='잘못된 마일스톤',
                description='설명',
                startdate=today + timedelta(days=10),
                enddate=today,
                priority='medium'
            )

    def test_create_milestone_with_same_dates(self, team):
        """시작일과 종료일이 같은 경우 허용"""
        today = date.today()
        milestone = self.service.create_milestone(
            team=team,
            title='당일 마일스톤',
            description='당일 완료',
            startdate=today,
            enddate=today,
            priority='critical'
        )

        assert milestone.startdate == milestone.enddate


@pytest.mark.unit
class TestMilestoneServiceUpdateMilestone:
    """마일스톤 업데이트 메서드 테스트"""

    def setup_method(self):
        self.service = MilestoneService()

    def test_update_milestone_startdate(self, team, milestone):
        """시작일 업데이트"""
        new_startdate = date.today() - timedelta(days=10)
        updated_milestone, updated_fields = self.service.update_milestone(
            milestone_id=milestone.id,
            team=team,
            startdate=new_startdate
        )

        assert updated_milestone.startdate == new_startdate
        assert '시작일' in updated_fields

    def test_update_milestone_enddate(self, team, milestone):
        """종료일 업데이트"""
        new_enddate = date.today() + timedelta(days=20)
        updated_milestone, updated_fields = self.service.update_milestone(
            milestone_id=milestone.id,
            team=team,
            enddate=new_enddate
        )

        assert updated_milestone.enddate == new_enddate
        assert '종료일' in updated_fields

    def test_update_milestone_progress(self, team, milestone):
        """진행률 업데이트"""
        updated_milestone, updated_fields = self.service.update_milestone(
            milestone_id=milestone.id,
            team=team,
            progress_percentage=75
        )

        assert updated_milestone.progress_percentage == 75
        assert '진행률' in updated_fields
        assert not updated_milestone.is_completed

    def test_update_milestone_progress_to_100_marks_completed(self, team, milestone):
        """진행률 100%로 업데이트 시 완료 상태로 변경"""
        updated_milestone, updated_fields = self.service.update_milestone(
            milestone_id=milestone.id,
            team=team,
            progress_percentage=100
        )

        assert updated_milestone.progress_percentage == 100
        assert updated_milestone.is_completed is True
        assert updated_milestone.completed_date is not None
        assert '진행률' in updated_fields
        assert '완료 상태' in updated_fields

    def test_update_milestone_progress_below_100_marks_incomplete(self, team, completed_milestone):
        """완료된 마일스톤의 진행률을 100% 미만으로 변경 시 미완료 상태로 변경"""
        updated_milestone, updated_fields = self.service.update_milestone(
            milestone_id=completed_milestone.id,
            team=team,
            progress_percentage=90
        )

        assert updated_milestone.progress_percentage == 90
        assert updated_milestone.is_completed is False
        assert updated_milestone.completed_date is None
        assert '완료 상태' in updated_fields

    def test_update_milestone_invalid_progress(self, team, milestone):
        """진행률이 0~100 범위 밖일 때 실패"""
        with pytest.raises(ValueError, match='진행률은 0-100 사이 값이어야 합니다'):
            self.service.update_milestone(
                milestone_id=milestone.id,
                team=team,
                progress_percentage=150
            )

    def test_update_milestone_invalid_date_range(self, team, milestone):
        """업데이트된 시작일이 종료일보다 늦을 때 실패"""
        with pytest.raises(ValueError, match='시작일은 종료일보다 이전이어야 합니다'):
            self.service.update_milestone(
                milestone_id=milestone.id,
                team=team,
                startdate=date.today() + timedelta(days=30)
            )


@pytest.mark.unit
class TestMilestoneServiceDeleteMilestone:
    """마일스톤 삭제 메서드 테스트"""

    def setup_method(self):
        self.service = MilestoneService()

    def test_delete_milestone(self, team, milestone):
        """마일스톤 삭제"""
        milestone_id = milestone.id
        milestone_title = self.service.delete_milestone(milestone_id, team)

        assert milestone_title == '테스트 마일스톤'
        assert not Milestone.objects.filter(id=milestone_id).exists()


@pytest.mark.unit
class TestMilestoneServiceGetTeamMilestones:
    """팀 마일스톤 목록 조회 메서드 테스트"""

    def setup_method(self):
        self.service = MilestoneService()

    def test_get_team_milestones_ordered_by_priority(self, team):
        """우선순위 순으로 정렬된 마일스톤 목록 반환"""
        today = date.today()

        # 다양한 우선순위의 마일스톤 생성
        m1 = Milestone.objects.create(
            team=team, title='M1', startdate=today, enddate=today + timedelta(days=1),
            priority='minimal'
        )
        m2 = Milestone.objects.create(
            team=team, title='M2', startdate=today, enddate=today + timedelta(days=1),
            priority='critical'
        )
        m3 = Milestone.objects.create(
            team=team, title='M3', startdate=today, enddate=today + timedelta(days=1),
            priority='medium'
        )

        # Act
        milestones = self.service.get_team_milestones(team)

        # Assert - critical(1) → medium(3) → minimal(5) 순
        assert list(milestones) == [m2, m3, m1]

    def test_get_team_milestones_ordered_by_enddate(self, team):
        """같은 우선순위일 때 종료일 순으로 정렬"""
        today = date.today()

        m1 = Milestone.objects.create(
            team=team, title='M1', startdate=today, enddate=today + timedelta(days=10),
            priority='high'
        )
        m2 = Milestone.objects.create(
            team=team, title='M2', startdate=today, enddate=today + timedelta(days=5),
            priority='high'
        )

        milestones = self.service.get_team_milestones(team)

        # 종료일 빠른 순
        assert list(milestones) == [m2, m1]

    def test_get_team_milestones_with_custom_order(self, team):
        """커스텀 정렬 옵션 적용"""
        today = date.today()

        m1 = Milestone.objects.create(
            team=team, title='M1', startdate=today, enddate=today + timedelta(days=1),
            priority='high'
        )
        m2 = Milestone.objects.create(
            team=team, title='M2', startdate=today + timedelta(days=5), enddate=today + timedelta(days=6),
            priority='low'
        )

        # startdate 순으로 정렬
        milestones = self.service.get_team_milestones(team, order_by=['startdate'])

        assert list(milestones) == [m1, m2]
