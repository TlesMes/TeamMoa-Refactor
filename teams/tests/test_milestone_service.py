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


@pytest.mark.unit
class TestMilestoneServiceProgressMode:
    """마일스톤 진행률 모드 관련 테스트 (12개)"""

    def setup_method(self):
        self.service = MilestoneService()

    def test_create_milestone_with_auto_mode(self, team):
        """AUTO 모드 마일스톤 생성"""
        today = date.today()
        milestone = self.service.create_milestone(
            team=team,
            title='AUTO 마일스톤',
            description='TODO 기반 자동 계산',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        assert milestone.progress_mode == 'auto'
        assert milestone.title == 'AUTO 마일스톤'

    def test_create_milestone_with_manual_mode(self, team):
        """수동 모드 마일스톤 생성"""
        today = date.today()
        milestone = self.service.create_milestone(
            team=team,
            title='수동 마일스톤',
            description='슬라이더로 조정',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='medium',
            progress_mode='manual'
        )

        assert milestone.progress_mode == 'manual'

    def test_create_milestone_default_mode_is_auto(self, team):
        """기본값은 AUTO 모드"""
        today = date.today()
        milestone = self.service.create_milestone(
            team=team,
            title='기본 모드 마일스톤',
            description='',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='low'
        )

        assert milestone.progress_mode == 'auto'

    def test_create_milestone_with_invalid_mode_raises(self, team):
        """잘못된 모드 입력 시 에러"""
        today = date.today()
        with pytest.raises(ValueError, match='유효하지 않은 진행률 모드'):
            self.service.create_milestone(
                team=team,
                title='잘못된 모드',
                description='',
                startdate=today,
                enddate=today + timedelta(days=7),
                priority='medium',
                progress_mode='invalid'
            )

    def test_toggle_mode_manual_to_auto_recalculates(self, team):
        """수동 → AUTO 전환 시 진행률 재계산"""
        from members.models import Todo

        # 수동 모드 마일스톤 생성
        today = date.today()
        milestone = Milestone.objects.create(
            team=team,
            title='수동→AUTO 테스트',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='high',
            progress_mode='manual',
            progress_percentage=50  # 수동으로 50% 설정
        )

        # TODO 3개 생성 (1개 완료)
        todo1 = Todo.objects.create(team=team, content='TODO 1', milestone=milestone, is_completed=True)
        todo2 = Todo.objects.create(team=team, content='TODO 2', milestone=milestone, is_completed=False)
        todo3 = Todo.objects.create(team=team, content='TODO 3', milestone=milestone, is_completed=False)

        # 모드 전환
        updated_milestone, result = self.service.toggle_progress_mode(milestone.id, team, 'auto')

        # 검증
        assert result['old_mode'] == 'manual'
        assert result['new_mode'] == 'auto'
        assert result['progress_recalculated'] is True
        assert result['new_progress'] == 33  # 1/3 = 33%
        assert updated_milestone.progress_percentage == 33

    def test_toggle_mode_auto_to_manual_keeps_progress(self, team):
        """AUTO → 수동 전환 시 기존 진행률 유지"""
        from members.models import Todo

        # AUTO 모드 마일스톤 생성
        today = date.today()
        milestone = Milestone.objects.create(
            team=team,
            title='AUTO→수동 테스트',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        # TODO 2개 생성 (1개 완료 = 50%)
        todo1 = Todo.objects.create(team=team, content='TODO 1', milestone=milestone, is_completed=True)
        todo2 = Todo.objects.create(team=team, content='TODO 2', milestone=milestone, is_completed=False)
        milestone.update_progress_from_todos()
        milestone.refresh_from_db()

        old_progress = milestone.progress_percentage

        # 모드 전환
        updated_milestone, result = self.service.toggle_progress_mode(milestone.id, team, 'manual')

        # 검증
        assert result['old_mode'] == 'auto'
        assert result['new_mode'] == 'manual'
        assert result['progress_recalculated'] is False
        assert result['new_progress'] == old_progress
        assert updated_milestone.progress_percentage == old_progress

    def test_toggle_mode_same_mode_no_change(self, team):
        """동일 모드 전환 시 변경 없음"""
        today = date.today()
        milestone = Milestone.objects.create(
            team=team,
            title='동일 모드 테스트',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='medium',
            progress_mode='auto',
            progress_percentage=25
        )

        # AUTO → AUTO 전환
        updated_milestone, result = self.service.toggle_progress_mode(milestone.id, team, 'auto')

        # 검증
        assert result['old_mode'] == 'auto'
        assert result['new_mode'] == 'auto'
        assert result['progress_recalculated'] is False
        assert updated_milestone.progress_percentage == 25

    def test_toggle_mode_invalid_mode_raises(self, team, milestone):
        """잘못된 모드로 전환 시도 시 에러"""
        with pytest.raises(ValueError, match='유효하지 않은 진행률 모드'):
            self.service.toggle_progress_mode(milestone.id, team, 'wrong_mode')

    def test_update_progress_in_auto_mode_raises(self, team):
        """AUTO 모드에서 수동 진행률 설정 방지"""
        today = date.today()
        milestone = Milestone.objects.create(
            team=team,
            title='AUTO 모드 마일스톤',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        with pytest.raises(ValueError, match='AUTO 모드에서는 진행률을 수동으로 설정할 수 없습니다'):
            self.service.update_milestone(
                milestone_id=milestone.id,
                team=team,
                progress_percentage=50
            )

    def test_update_progress_in_manual_mode_allowed(self, team):
        """수동 모드에서 진행률 설정 허용"""
        today = date.today()
        milestone = Milestone.objects.create(
            team=team,
            title='수동 모드 마일스톤',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='medium',
            progress_mode='manual'
        )

        updated_milestone, updated_fields = self.service.update_milestone(
            milestone_id=milestone.id,
            team=team,
            progress_percentage=75
        )

        assert updated_milestone.progress_percentage == 75
        assert '진행률' in updated_fields

    def test_get_milestone_with_todo_stats(self, team):
        """TODO 통계 조회"""
        from members.models import Todo

        today = date.today()
        milestone = Milestone.objects.create(
            team=team,
            title='통계 테스트',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='high',
            progress_mode='auto'
        )

        # TODO 4개 생성 (2개 완료)
        Todo.objects.create(team=team, content='TODO 1', milestone=milestone, is_completed=True)
        Todo.objects.create(team=team, content='TODO 2', milestone=milestone, is_completed=True)
        Todo.objects.create(team=team, content='TODO 3', milestone=milestone, is_completed=False)
        Todo.objects.create(team=team, content='TODO 4', milestone=milestone, is_completed=False)

        # 통계 조회
        result = self.service.get_milestone_with_todo_stats(milestone.id, team)

        # 검증
        assert result['milestone'] == milestone
        assert result['todo_stats']['total'] == 4
        assert result['todo_stats']['completed'] == 2
        assert result['todo_stats']['in_progress'] == 2
        assert result['todo_stats']['completion_rate'] == 50

    def test_get_milestone_with_todo_stats_no_todos(self, team):
        """TODO 0개일 때 통계"""
        today = date.today()
        milestone = Milestone.objects.create(
            team=team,
            title='TODO 없음',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='low',
            progress_mode='auto'
        )

        result = self.service.get_milestone_with_todo_stats(milestone.id, team)

        assert result['todo_stats']['total'] == 0
        assert result['todo_stats']['completed'] == 0
        assert result['todo_stats']['in_progress'] == 0
        assert result['todo_stats']['completion_rate'] == 0

    def test_update_milestone_mode_manual_to_auto_recalculates(self, team):
        """update_milestone로 수동 → AUTO 전환 시 진행률 재계산"""
        from members.models import Todo

        # 수동 모드 마일스톤 생성
        today = date.today()
        milestone = Milestone.objects.create(
            team=team,
            title='수동→AUTO 테스트',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='high',
            progress_mode='manual',
            progress_percentage=50  # 수동으로 50% 설정
        )

        # TODO 3개 생성 (2개 완료)
        Todo.objects.create(team=team, content='TODO 1', milestone=milestone, is_completed=True)
        Todo.objects.create(team=team, content='TODO 2', milestone=milestone, is_completed=True)
        Todo.objects.create(team=team, content='TODO 3', milestone=milestone, is_completed=False)

        # update_milestone로 모드 전환
        updated_milestone, updated_fields = self.service.update_milestone(
            milestone_id=milestone.id,
            team=team,
            progress_mode='auto'
        )

        # 검증
        assert updated_milestone.progress_mode == 'auto'
        assert updated_milestone.progress_percentage == 66  # 2/3 = 66%
        assert '진행률 모드' in updated_fields
        assert '진행률 (AUTO 재계산)' in updated_fields

    def test_update_milestone_mode_auto_to_manual_keeps_progress(self, team):
        """update_milestone로 AUTO → 수동 전환 시 기존 진행률 유지"""
        from members.models import Todo

        # AUTO 모드 마일스톤 생성
        today = date.today()
        milestone = Milestone.objects.create(
            team=team,
            title='AUTO→수동 테스트',
            startdate=today,
            enddate=today + timedelta(days=7),
            priority='medium',
            progress_mode='auto'
        )

        # TODO 4개 생성 (3개 완료)
        Todo.objects.create(team=team, content='TODO 1', milestone=milestone, is_completed=True)
        Todo.objects.create(team=team, content='TODO 2', milestone=milestone, is_completed=True)
        Todo.objects.create(team=team, content='TODO 3', milestone=milestone, is_completed=True)
        Todo.objects.create(team=team, content='TODO 4', milestone=milestone, is_completed=False)

        # AUTO 모드에서 진행률 자동 계산
        milestone.update_progress_from_todos()
        milestone.refresh_from_db()
        assert milestone.progress_percentage == 75  # 3/4 = 75%

        # update_milestone로 모드 전환
        updated_milestone, updated_fields = self.service.update_milestone(
            milestone_id=milestone.id,
            team=team,
            progress_mode='manual'
        )

        # 검증: 진행률 유지
        assert updated_milestone.progress_mode == 'manual'
        assert updated_milestone.progress_percentage == 75  # 기존 75% 유지
        assert '진행률 모드' in updated_fields
        assert '진행률 (AUTO 재계산)' not in updated_fields
