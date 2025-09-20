// 회원가입 성공 페이지 전용 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 재전송 링크 이벤트 리스너
    const resendLink = document.querySelector('.resend-link');
    if (resendLink) {
        resendLink.addEventListener('click', function(e) {
            e.preventDefault();
            showResendForm();
        });
    }

    // 취소 버튼 이벤트 리스너
    const cancelButton = document.querySelector('.btn-cancel');
    if (cancelButton) {
        cancelButton.addEventListener('click', function(e) {
            e.preventDefault();
            hideResendForm();
        });
    }

    // 재전송 폼 이벤트 리스너
    const resendForm = document.getElementById('resend-form');
    if (resendForm) {
        resendForm.addEventListener('submit', handleResendSubmit);
    }
});

function showResendForm() {
    const form = document.getElementById('resend-form');
    const result = document.getElementById('resend-result');

    form.style.display = 'block';
    result.style.display = 'none';

    // 폼이 나타날 때 입력 필드에 포커스
    setTimeout(() => {
        document.getElementById('email_or_username').focus();
    }, 300);
}

function hideResendForm() {
    const form = document.getElementById('resend-form');
    form.style.display = 'none';
}

async function handleResendSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const resultDiv = document.getElementById('resend-result');

    // 버튼 비활성화 및 로딩 상태
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="ri-loader-4-line"></i> 전송 중...';

    try {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await response.json();

        // 결과 표시
        resultDiv.style.display = 'block';
        resultDiv.className = `resend-result ${data.status}`;
        resultDiv.textContent = data.message;

        if (data.status === 'success') {
            // 성공 시 폼 숨기기
            setTimeout(() => {
                hideResendForm();
            }, 3000);
        }

    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'resend-result error';
        resultDiv.textContent = '네트워크 오류가 발생했습니다. 다시 시도해주세요.';
    } finally {
        // 버튼 복원
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="ri-mail-send-line"></i> 인증 메일 재전송';
    }
}