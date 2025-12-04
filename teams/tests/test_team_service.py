"""
Teams 서비스 레이어 테스트 (25개)

테스트 구성:
- TestTeamServiceCreateTeam: 5개 - 팀 생성, 유효성 검증
- TestTeamServiceVerifyTeamCode: 5개 - 초대 코드 검증, 정원 초과
- TestTeamServiceJoinTeam: 5개 - 팀 가입, 비밀번호 체크
- TestTeamServiceGetUserTeams: 2개 - 사용자 팀 목록
- TestTeamServiceGetTeamStatistics: 2개 - 팀 통계 계산
- TestTeamServiceDisbandTeam: 2개 - 팀 해체, 권한 확인
- TestTeamServiceRemoveMember: 4개 - 멤버 제거/탈퇴

사용 위치:
- SSR 뷰: team_create, team_verify_code, team_join_process, main_page 등
- API: TeamViewSet.remove_member
"""
import pytest
from teams.services import TeamService
from teams.models import Team, TeamUser


@pytest.mark.unit
class TestTeamServiceCreateTeam:
    """팀 생성 메서드 테스트"""

    def setup_method(self):
        self.service = TeamService()

    def test_create_team_success(self, user):
        """정상적으로 팀이 생성되는지 확인"""
        # Act
        team = self.service.create_team(
            host_user=user,
            title='새로운팀',
            maxuser=5,
            teampasswd='newteam123',
            introduction='새 팀 소개'
        )

        # Assert
        assert team.title == '새로운팀'
        assert team.maxuser == 5
        assert team.teampasswd == 'newteam123'
        assert team.introduction == '새 팀 소개'
        assert team.host == user
        assert team.currentuser == 1
        assert team.invitecode is not None
        assert len(team.invitecode) == 16

        # 호스트가 TeamUser로 추가되었는지 확인
        assert TeamUser.objects.filter(team=team, user=user).exists()

    def test_create_team_with_empty_title(self, user):
        """빈 제목으로 팀 생성 시 실패"""
        with pytest.raises(ValueError, match='팀 이름을 입력해주세요'):
            self.service.create_team(
                host_user=user,
                title='',
                maxuser=5,
                teampasswd='password123',
                introduction='소개'
            )

    def test_create_team_with_invalid_maxuser(self, user):
        """최대 인원이 0 이하일 때 실패"""
        with pytest.raises(ValueError, match='최대 인원수는 1명 이상이어야 합니다'):
            self.service.create_team(
                host_user=user,
                title='팀이름',
                maxuser=0,
                teampasswd='password123',
                introduction='소개'
            )

    def test_create_team_with_empty_password(self, user):
        """빈 비밀번호로 팀 생성 시 실패"""
        with pytest.raises(ValueError, match='팀 비밀번호를 입력해주세요'):
            self.service.create_team(
                host_user=user,
                title='팀이름',
                maxuser=5,
                teampasswd='',
                introduction='소개'
            )

    def test_create_team_generates_unique_invite_code(self, user):
        """각 팀마다 고유한 초대 코드가 생성되는지 확인"""
        team1 = self.service.create_team(user, '팀1', 5, 'pass1', '소개1')
        team2 = self.service.create_team(user, '팀2', 5, 'pass2', '소개2')

        assert team1.invitecode != team2.invitecode


@pytest.mark.unit
class TestTeamServiceVerifyTeamCode:
    """팀 코드 검증 메서드 테스트"""

    def setup_method(self):
        self.service = TeamService()

    def test_verify_team_code_success(self, team, another_user):
        """유효한 팀 코드 검증 성공"""
        # Act
        result = self.service.verify_team_code(team.invitecode, another_user)

        # Assert
        assert result['id'] == team.id
        assert result['title'] == team.title
        assert result['current_members'] == 1
        assert result['maxuser'] == team.maxuser

    def test_verify_team_code_with_empty_code(self, user):
        """빈 코드로 검증 시 실패"""
        with pytest.raises(ValueError, match='팀 코드를 입력해주세요'):
            self.service.verify_team_code('', user)

    def test_verify_team_code_with_invalid_code(self, user):
        """존재하지 않는 코드로 검증 시 실패"""
        with pytest.raises(ValueError, match='유효하지 않은 팀 코드입니다'):
            self.service.verify_team_code('INVALID1234', user)

    def test_verify_team_code_already_member(self, team, user):
        """이미 가입한 팀 코드 검증 시 실패"""
        with pytest.raises(ValueError, match='이미 가입된 팀입니다'):
            self.service.verify_team_code(team.invitecode, user)

    def test_verify_team_code_team_full(self, full_team, another_user):
        """최대 인원에 도달한 팀 코드 검증 시 실패"""
        with pytest.raises(ValueError, match='팀 최대인원을 초과했습니다'):
            self.service.verify_team_code(full_team.invitecode, another_user)


@pytest.mark.unit
class TestTeamServiceJoinTeam:
    """팀 가입 메서드 테스트"""

    def setup_method(self):
        self.service = TeamService()

    def test_join_team_success(self, team, another_user):
        """정상적으로 팀 가입"""
        # Act
        joined_team = self.service.join_team(
            user=another_user,
            team_id=team.id,
            password='teampass123'
        )

        # Assert
        assert TeamUser.objects.filter(team=team, user=another_user).exists()
        assert joined_team.currentuser == 2

    def test_join_team_with_wrong_password(self, team, another_user):
        """잘못된 비밀번호로 가입 시 실패"""
        with pytest.raises(ValueError, match='팀 비밀번호가 올바르지 않습니다'):
            self.service.join_team(another_user, team.id, 'wrongpassword')

    def test_join_team_already_member(self, team, user):
        """이미 가입한 팀에 재가입 시도 시 실패"""
        with pytest.raises(ValueError, match='이미 가입된 팀입니다'):
            self.service.join_team(user, team.id, 'teampass123')

    def test_join_team_full(self, full_team, another_user):
        """최대 인원에 도달한 팀 가입 시 실패"""
        with pytest.raises(ValueError, match='팀 최대인원을 초과했습니다'):
            self.service.join_team(another_user, full_team.id, 'fullteam123')

    def test_join_team_with_nonexistent_team_id(self, another_user):
        """존재하지 않는 팀 ID로 가입 시 실패"""
        with pytest.raises(ValueError, match='존재하지 않는 팀입니다'):
            self.service.join_team(another_user, 99999, 'password')


@pytest.mark.unit
class TestTeamServiceGetUserTeams:
    """사용자 팀 목록 조회 메서드 테스트"""

    def setup_method(self):
        self.service = TeamService()

    def test_get_user_teams(self, user, team):
        """사용자가 가입한 팀 목록 반환"""
        # Arrange - 추가 팀 생성
        team2 = self.service.create_team(user, '팀2', 5, 'pass2', '소개2')

        # Act
        teams = self.service.get_user_teams(user)

        # Assert
        assert teams.count() == 2
        assert team in teams
        assert team2 in teams

    def test_get_user_teams_empty(self, another_user):
        """가입한 팀이 없는 사용자"""
        teams = self.service.get_user_teams(another_user)
        assert teams.count() == 0


@pytest.mark.unit
class TestTeamServiceGetTeamStatistics:
    """팀 통계 조회 메서드 테스트"""

    def setup_method(self):
        self.service = TeamService()

    def test_get_team_statistics(self, team, milestone, completed_milestone):
        """마일스톤 통계 계산"""
        # Act
        stats = self.service.get_team_statistics(team)

        # Assert
        assert stats['in_progress'] == 1
        assert stats['completed'] == 1
        assert stats['not_started'] == 0
        assert stats['completed_count'] == 1
        assert stats['in_progress_count'] == 1
        assert '테스트 마일스톤' in stats['today_milestone']

    def test_get_team_statistics_no_milestones(self, team):
        """마일스톤이 없는 팀 통계"""
        stats = self.service.get_team_statistics(team)

        assert stats['in_progress'] == 0
        assert stats['completed'] == 0
        assert stats['today_milestone'] == '진행 중인 마일스톤이 없습니다.'


@pytest.mark.unit
class TestTeamServiceDisbandTeam:
    """팀 해체 메서드 테스트"""

    def setup_method(self):
        self.service = TeamService()

    def test_disband_team_by_host(self, team, user):
        """호스트가 팀 해체"""
        team_id = team.id
        team_title = self.service.disband_team(team_id, user)

        assert team_title == '테스트팀'
        assert not Team.objects.filter(id=team_id).exists()

    def test_disband_team_by_non_host(self, team_with_members, another_user):
        """일반 멤버가 팀 해체 시도 시 실패"""
        with pytest.raises(ValueError, match='팀을 해체할 권한이 없습니다'):
            self.service.disband_team(team_with_members.id, another_user)


@pytest.mark.unit
class TestTeamServiceRemoveMember:
    """멤버 제거 메서드 테스트"""

    def setup_method(self):
        self.service = TeamService()

    def test_remove_member_by_host(self, team_with_members, user, another_user):
        """호스트가 일반 멤버 추방"""
        result = self.service.remove_member(
            team_id=team_with_members.id,
            target_user_id=another_user.id,
            requesting_user=user
        )

        assert result['action_type'] == 'remove'
        assert result['remaining_members'] == 1
        assert not TeamUser.objects.filter(
            team=team_with_members,
            user=another_user
        ).exists()

    def test_remove_member_self_leave(self, team_with_members, another_user):
        """일반 멤버가 본인 탈퇴"""
        result = self.service.remove_member(
            team_id=team_with_members.id,
            target_user_id=another_user.id,
            requesting_user=another_user
        )

        assert result['action_type'] == 'leave'
        assert result['remaining_members'] == 1

    def test_remove_member_host_cannot_leave(self, team, user):
        """호스트는 탈퇴 불가"""
        with pytest.raises(ValueError, match='팀장은 탈퇴할 수 없습니다'):
            self.service.remove_member(team.id, user.id, user)

    def test_remove_member_without_permission(self, team_with_members, another_user, user):
        """권한 없는 멤버가 다른 멤버 추방 시도"""
        with pytest.raises(ValueError, match='권한이 없습니다'):
            self.service.remove_member(
                team_id=team_with_members.id,
                target_user_id=user.id,
                requesting_user=another_user
            )
