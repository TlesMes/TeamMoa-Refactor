
// DOM이 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    // 드롭다운 기능
    const dropdownToggle = document.getElementById('userDropdown');
    const dropdownMenu = document.getElementById('dropdownMenu');
    const dropdownArrow = dropdownToggle.querySelector('.dropdown-arrow');
    
    // 드롭다운 토글 함수
    function toggleDropdown() {
        const isOpen = dropdownMenu.classList.contains('show');
        
        if (isOpen) {
            closeDropdown();
        } else {
            openDropdown();
        }
    }
    
    // 드롭다운 열기
    function openDropdown() {
        dropdownMenu.classList.add('show');
        dropdownToggle.classList.add('active');
        dropdownToggle.setAttribute('aria-expanded', 'true');
    }
    
    // 드롭다운 닫기
    function closeDropdown() {
        dropdownMenu.classList.remove('show');
        dropdownToggle.classList.remove('active');
        dropdownToggle.setAttribute('aria-expanded', 'false');
    }
    
    // 드롭다운 버튼 클릭 이벤트
    dropdownToggle.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        toggleDropdown();
    });
    
    // 문서 클릭 시 드롭다운 닫기
    document.addEventListener('click', function(e) {
        if (!dropdownToggle.contains(e.target) && !dropdownMenu.contains(e.target)) {
            closeDropdown();
        }
    });
    
    // ESC 키로 드롭다운 닫기
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeDropdown();
        }
    });
    
    // 로그아웃 버튼 클릭 이벤트
    const logoutBtn = document.querySelector('.logout-btn');
    const logoutUrl = document.getElementById('logout-url').dataset.logoutUrl;
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showConfirmModal('정말 로그아웃하시겠습니까?', () => {
                showToast('로그아웃되었습니다.');
                setTimeout(() => {
                    window.location.href = logoutUrl;
                }, 1000);
            });
        });
    }
    
    // 복사 아이콘 클릭 이벤트
    const copyIcon = document.querySelector('.copy-icon');
    if (copyIcon) {
        copyIcon.addEventListener('click', function() {
            const cardTitle = document.querySelector('.card-title').textContent;
            
            // 클립보드에 복사
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(cardTitle).then(function() {
                    showToast('클립보드에 복사되었습니다.');
                }).catch(function(err) {
                    console.error('복사 실패:', err);
                    fallbackCopyTextToClipboard(cardTitle);
                });
            } else {
                fallbackCopyTextToClipboard(cardTitle);
            }
        });
    }
    
    // 폴백 복사 함수 (구형 브라우저 지원)
    function fallbackCopyTextToClipboard(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        
        // 화면 밖에 위치시키기
        textArea.style.top = "0";
        textArea.style.left = "0";
        textArea.style.position = "fixed";
        
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                showToast('클립보드에 복사되었습니다.');
            } else {
                showToast('복사에 실패했습니다.');
            }
        } catch (err) {
            console.error('복사 실패:', err);
            showToast('복사에 실패했습니다.');
        }
        
        document.body.removeChild(textArea);
    }
    
    // 토스트 메시지 표시 함수
    function showToast(message) {
        // 기존 토스트가 있다면 제거
        const existingToast = document.querySelector('.toast');
        if (existingToast) {
            existingToast.remove();
        }
        
        // 토스트 엘리먼트 생성
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        
        // 토스트 스타일
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #374151;
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 14px;
            z-index: 1000;
            opacity: 0;
            transform: translateY(-10px);
            transition: all 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        // 애니메이션으로 표시
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        }, 10);
        
        // 3초 후 제거
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }
    
    // Django Messages를 토스트로 표시
    function showDjangoMessages() {
        const messagesContainer = document.getElementById('django-messages');
        if (messagesContainer) {
            const messages = messagesContainer.querySelectorAll('.django-message');
            messages.forEach((messageElement, index) => {
                const message = messageElement.textContent;
                const level = messageElement.getAttribute('data-level');
                
                // 각 메시지를 순차적으로 표시 (0.5초 간격)
                setTimeout(() => {
                    showDjangoToast(message, level);
                }, index * 500);
            });
        }
    }
    
    // Django Messages 전용 토스트 함수
    function showDjangoToast(message, level = 'info') {
        // 기존 토스트 제거
        const existingToast = document.querySelector('.django-toast');
        if (existingToast) {
            existingToast.remove();
        }
        
        // 레벨별 색상 및 아이콘 설정
        const levelConfig = {
            'success': { bg: '#10b981', icon: 'ri-check-line' },
            'error': { bg: '#ef4444', icon: 'ri-error-warning-line' },
            'warning': { bg: '#f59e0b', icon: 'ri-alert-line' },
            'info': { bg: '#3b82f6', icon: 'ri-information-line' }
        };
        
        const config = levelConfig[level] || levelConfig['info'];
        
        // 토스트 엘리먼트 생성
        const toast = document.createElement('div');
        toast.className = 'django-toast';
        toast.innerHTML = `
            <i class="${config.icon}"></i>
            <span>${message}</span>
        `;
        
        // 토스트 스타일
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: ${config.bg};
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 10000;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
            max-width: 400px;
            opacity: 0;
            transform: translateY(-10px);
            transition: all 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        // 애니메이션으로 표시
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        }, 10);
        
        // 4초 후 제거
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 4000);
    }
    
    // 페이지 로드 시 Django Messages 표시
    showDjangoMessages();
    
    // 공통 확인 모달 함수
    function showConfirmModal(message, onConfirm) {
        // 기존 모달이 있다면 제거
        const existingModal = document.querySelector('.confirm-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // 모달 배경 생성
        const modalBackdrop = document.createElement('div');
        modalBackdrop.className = 'confirm-modal-backdrop';
        modalBackdrop.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 10001;
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        // 모달 컨테이너 생성
        const modal = document.createElement('div');
        modal.className = 'confirm-modal';
        modal.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 24px;
            max-width: 400px;
            width: 90%;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            transform: scale(0.9);
            transition: transform 0.3s ease;
        `;
        
        // 모달 내용 생성
        modal.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <div style="
                    width: 48px; 
                    height: 48px; 
                    background: #fef3c7; 
                    border-radius: 50%; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center;
                    margin-right: 16px;
                ">
                    <i class="ri-question-line" style="font-size: 24px; color: #d97706;"></i>
                </div>
                <div>
                    <h3 style="margin: 0 0 4px 0; font-size: 18px; font-weight: 600; color: #111827;">확인</h3>
                </div>
            </div>
            <p style="margin: 0 0 24px 0; color: #6b7280; font-size: 14px; line-height: 1.5;">${message}</p>
            <div style="display: flex; gap: 12px; justify-content: flex-end;">
                <button class="modal-cancel-btn" style="
                    padding: 8px 16px;
                    border: 1px solid #d1d5db;
                    background: white;
                    color: #374151;
                    border-radius: 6px;
                    font-size: 14px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                ">취소</button>
                <button class="modal-confirm-btn" style="
                    padding: 8px 16px;
                    border: none;
                    background: #dc2626;
                    color: white;
                    border-radius: 6px;
                    font-size: 14px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                ">확인</button>
            </div>
        `;
        
        modalBackdrop.appendChild(modal);
        document.body.appendChild(modalBackdrop);
        
        // 애니메이션으로 표시
        setTimeout(() => {
            modalBackdrop.style.opacity = '1';
            modal.style.transform = 'scale(1)';
        }, 10);
        
        // 모달 닫기 함수
        function closeModal() {
            modalBackdrop.style.opacity = '0';
            modal.style.transform = 'scale(0.9)';
            setTimeout(() => {
                if (modalBackdrop.parentNode) {
                    modalBackdrop.parentNode.removeChild(modalBackdrop);
                }
            }, 300);
        }
        
        // 이벤트 리스너들
        const cancelBtn = modal.querySelector('.modal-cancel-btn');
        const confirmBtn = modal.querySelector('.modal-confirm-btn');
        
        cancelBtn.addEventListener('click', closeModal);
        confirmBtn.addEventListener('click', () => {
            closeModal();
            if (onConfirm) onConfirm();
        });
        
        // 배경 클릭 시 닫기
        modalBackdrop.addEventListener('click', (e) => {
            if (e.target === modalBackdrop) {
                closeModal();
            }
        });
        
        // ESC 키로 닫기
        const handleEscKey = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', handleEscKey);
            }
        };
        document.addEventListener('keydown', handleEscKey);
        
        // 버튼 호버 효과
        cancelBtn.addEventListener('mouseenter', () => {
            cancelBtn.style.backgroundColor = '#f3f4f6';
        });
        cancelBtn.addEventListener('mouseleave', () => {
            cancelBtn.style.backgroundColor = 'white';
        });
        
        confirmBtn.addEventListener('mouseenter', () => {
            confirmBtn.style.backgroundColor = '#b91c1c';
        });
        confirmBtn.addEventListener('mouseleave', () => {
            confirmBtn.style.backgroundColor = '#dc2626';
        });
    }
    
    // 전역으로 접근 가능하도록 설정
    window.showConfirmModal = showConfirmModal;
    window.showToast = showToast;
    
});