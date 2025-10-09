// 팀 메인페이지 전용 JavaScript

// 클립보드 복사 기능
function copyClipboard() {
  const text = document.getElementById("copycode").textContent;
  const textarea = document.createElement("textarea");
  textarea.textContent = text;
  document.body.append(textarea);
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
  showToast("팀코드가 복사되었습니다");
}

// 팀 해산 확인 기능
function initTeamDisbandConfirm() {
  const disbandTeamBtn = document.getElementById('disband-team-btn');
  if (disbandTeamBtn) {
    disbandTeamBtn.addEventListener('click', function(e) {
      e.preventDefault();
      const teamTitle = this.dataset.teamTitle;
      showConfirmModal(`"${teamTitle}" 팀을 정말로 해산하시겠습니까?\n해산된 팀은 복구할 수 없습니다.`, () => {
        document.getElementById('disband-form').submit();
      });
    });
  }
}

// 멤버 제거 (추방/탈퇴) 기능
async function removeMember(userId, userName, isLeave = false) {
  const teamId = window.teamData.teamId;
  const action = isLeave ? '탈퇴' : '추방';
  const message = isLeave
    ? '정말로 팀에서 탈퇴하시겠습니까?'
    : `"${userName}"님을 정말로 추방하시겠습니까?`;

  showConfirmModal(message, async () => {
    try {
      const response = await window.teamApi.removeMember(teamId, userId);

      // 성공 메시지 표시
      if (window.handleApiResponse) {
        window.handleApiResponse(response);
      }

      // 멤버 카드 제거
      const memberItem = document.querySelector(`.member-item[data-user-id="${userId}"]`);
      if (memberItem && !memberItem.classList.contains('leader')) {
        memberItem.style.transition = 'opacity 0.3s ease';
        memberItem.style.opacity = '0';
        setTimeout(() => {
          memberItem.remove();
        }, 300);
      }

      // 탈퇴한 경우 팀 목록으로 리다이렉트
      if (isLeave) {
        setTimeout(() => {
          window.location.href = '/teams/';
        }, 1500);
      }

    } catch (error) {
      if (window.handleApiError) {
        window.handleApiError(error);
      }
    }
  });
}

// 멤버 제거/탈퇴 버튼 초기화
function initMemberRemoveButtons() {
  // 추방 버튼
  document.querySelectorAll('.remove-member-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const userId = this.dataset.userId;
      const userName = this.dataset.userName;
      removeMember(userId, userName, false);
    });
  });

  // 탈퇴 버튼
  document.querySelectorAll('.leave-team-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const userId = this.dataset.userId;
      removeMember(userId, null, true);
    });
  });
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
  // 팀코드 복사 버튼 이벤트 연결
  const copyButton = document.getElementById("copybtn");
  if (copyButton) {
    copyButton.addEventListener("click", copyClipboard);
  }

  // 팀 해산 버튼 이벤트 연결
  initTeamDisbandConfirm();

  // 멤버 제거/탈퇴 버튼 이벤트 연결
  initMemberRemoveButtons();
});