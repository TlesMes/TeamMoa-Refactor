// 회원가입 성공 페이지 전용 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('[Signup Success] Page loaded');

    // 재전송 링크 이벤트 리스너
    const resendLink = document.querySelector('.resend-link');
    if (resendLink) {
        console.log('[Signup Success] Resend link found');
        resendLink.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('[Signup Success] Resend link clicked');
            showResendForm();
        });
    }

    // 재전송 폼 이벤트 리스너
    const resendForm = document.getElementById('resend-form');
    if (resendForm) {
        console.log('[Signup Success] Resend form found');

        // 취소 버튼 클릭 이벤트 (이벤트 위임)
        resendForm.addEventListener('click', function(e) {
            if (e.target.closest('.btn-cancel')) {
                e.preventDefault();
                e.stopPropagation();
                console.log('[Signup Success] Cancel button clicked');
                hideResendForm();
            }
        });

        // 폼 제출 이벤트
        resendForm.addEventListener('submit', handleResendSubmit);
    }

    // 피드백 메시지가 있으면 자동으로 재전송 폼 열기
    const hasFeedback = resendForm && resendForm.querySelector('.email-sent-notice');
    console.log('[Signup Success] Has feedback:', !!hasFeedback);
    if (hasFeedback) {
        showResendForm();
    }
});

function showResendForm() {
    console.log('[Signup Success] showResendForm() called');
    const form = document.getElementById('resend-form');
    const result = document.getElementById('resend-result');

    if (form) {
        form.classList.remove('tm-hidden');
        console.log('[Signup Success] Form shown');
    }
    if (result) {
        result.classList.add('tm-hidden');
    }

    // 폼이 나타날 때 입력 필드에 포커스
    setTimeout(() => {
        const emailInput = document.getElementById('email_or_username');
        if (emailInput) {
            emailInput.focus();
        }
    }, 300);
}

function hideResendForm() {
    console.log('[Signup Success] hideResendForm() called');
    const form = document.getElementById('resend-form');
    if (form) {
        form.classList.add('tm-hidden');
        console.log('[Signup Success] Form hidden');
    }
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
        resultDiv.classList.remove('tm-hidden');
        resultDiv.className = `resend-result ${data.status}`;
        resultDiv.textContent = data.message;

        if (data.status === 'success') {
            // 성공 시 폼 숨기기
            setTimeout(() => {
                hideResendForm();
            }, 3000);
        }

    } catch (error) {
        resultDiv.classList.remove('tm-hidden');
        resultDiv.className = 'resend-result error';
        resultDiv.textContent = '네트워크 오류가 발생했습니다. 다시 시도해주세요.';
    } finally {
        // 버튼 복원
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="ri-mail-send-line"></i> 인증 메일 재전송';
    }
}