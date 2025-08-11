
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
            if (confirm('정말 로그아웃하시겠습니까?')) {
                // 실제 로그아웃 로직을 여기에 구현
                alert('로그아웃되었습니다.');
                window.location.href = logoutUrl;
            }
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
    
    // 버튼 클릭 이벤트들
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const buttonText = this.textContent.trim();
            showToast(`"${buttonText}" 버튼이 클릭되었습니다.`);
        });
    });
    
    // 네비게이션 링크 클릭 이벤트 (SPA처럼 동작하도록)
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            const text = this.textContent.trim();
            showToast(`"${text}" 페이지로 이동합니다.`);
            
            // 실제 페이지 이동은 여기서 구현
            window.location.href = href;
        });
    });
});