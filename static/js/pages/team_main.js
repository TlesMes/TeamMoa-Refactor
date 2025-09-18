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

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
  // 팀코드 복사 버튼 이벤트 연결
  const copyButton = document.getElementById("copybtn");
  if (copyButton) {
    copyButton.addEventListener("click", copyClipboard);
  }

  // 팀 해산 버튼 이벤트 연결
  initTeamDisbandConfirm();
});