// 마일스톤 타임라인 페이지 전용 JavaScript

// 월별 실제 일수 기반 타임라인 시스템
document.addEventListener('DOMContentLoaded', function() {
    const scrollContent = document.querySelector('.timeline-scroll-content');
    const monthHeaders = document.getElementById('monthHeaders');
    const currentYear = new Date().getFullYear();
    const dayWidth = 12; // 일당 픽셀 너비

    // 각 월의 일수 계산 (윤년 고려)
    function getDaysInMonth(year, month) {
        return new Date(year, month + 1, 0).getDate();
    }

    // 월별 일수 배열과 누적 위치 계산
    const monthDays = [];
    const monthOffsets = [];
    let totalOffset = 0;

    for (let month = 0; month < 12; month++) {
        monthOffsets[month] = totalOffset;
        const daysInMonth = getDaysInMonth(currentYear, month);
        monthDays[month] = daysInMonth;
        totalOffset += daysInMonth * dayWidth;
    }

    const totalWidth = totalOffset; // 전체 타임라인 너비

    // 툴팁 요소 생성
    const tooltip = document.createElement('div');
    tooltip.className = 'milestone-tooltip';
    tooltip.style.cssText = `
        position: absolute;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        white-space: nowrap;
        z-index: 1000;
        pointer-events: none;
        display: none;
    `;
    document.body.appendChild(tooltip);

    // 월 헤더 동적 생성
    const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
    for (let month = 0; month < 12; month++) {
        const monthHeader = document.createElement('div');
        monthHeader.className = 'month-header';
        monthHeader.textContent = monthNames[month];
        monthHeader.style.cssText = `
            position: absolute;
            left: ${monthOffsets[month]}px;
            width: ${monthDays[month] * dayWidth}px;
        `;
        monthHeaders.appendChild(monthHeader);
    }

    // 월별 구분선 동적 생성
    for (let month = 1; month < 12; month++) { // 1월부터 시작 (0월 제외)
        const monthMarker = document.createElement('div');
        monthMarker.className = 'month-marker';
        monthMarker.style.cssText = `
            position: absolute;
            left: ${monthOffsets[month]}px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #8c9399;
            pointer-events: none;
        `;
        scrollContent.appendChild(monthMarker);
    }

    // 일별 구분선 생성 (디버깅용)
    for (let month = 0; month < 12; month++) {
        for (let day = 1; day <= monthDays[month]; day++) {
            const dayPos = monthOffsets[month] + ((day - 1) * dayWidth);
            const dayMarker = document.createElement('div');
            dayMarker.className = 'day-marker';
            dayMarker.style.cssText = `
                position: absolute;
                left: ${dayPos}px;
                top: 0;
                bottom: 0;
                width: 1px;
                background: rgba(200, 200, 200, 0.3);
                pointer-events: none;
            `;
            scrollContent.appendChild(dayMarker);
        }
    }

    // 타임라인 컨테이너 너비 설정
    scrollContent.style.width = totalWidth + 'px';

    const milestoneItems = document.querySelectorAll('.milestone-timeline-item');

    // 날짜 <-> 픽셀 변환 함수들 (새로운 월별 오프셋 기반)
    function dateToPixel(date) {
        const month = date.getMonth();
        const day = date.getDate();
        return monthOffsets[month] + ((day - 1) * dayWidth);
    }

    function pixelToDate(pixel) {
        // 어느 월에 속하는지 찾기
        let month = 0;
        for (let m = 0; m < 12; m++) {
            if (pixel >= monthOffsets[m] && (m === 11 || pixel < monthOffsets[m + 1])) {
                month = m;
                break;
            }
        }

        // 해당 월 내에서의 일수 계산
        const dayInMonth = Math.floor((pixel - monthOffsets[month]) / dayWidth) + 1;
        const validDay = Math.min(Math.max(dayInMonth, 1), monthDays[month]);

        return new Date(currentYear, month, validDay);
    }

    function formatDate(date) {
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    }

    // 날짜를 디스플레이용으로 포맷팅
    function formatDateForDisplay(date) {
        return `${date.getMonth() + 1}월 ${date.getDate()}일`;
    }

    // 픽셀 위치를 가장 가까운 일(day) 단위로 스냅
    function snapToDay(pixel) {
        // 어느 월에 속하는지 찾기
        let month = 0;
        for (let m = 0; m < 12; m++) {
            if (pixel >= monthOffsets[m] && (m === 11 || pixel < monthOffsets[m + 1])) {
                month = m;
                break;
            }
        }

        // 해당 월 내에서의 일수 계산하고 반올림
        const pixelInMonth = pixel - monthOffsets[month];
        const dayInMonth = Math.round(pixelInMonth / dayWidth);
        const validDay = Math.min(Math.max(dayInMonth, 0), monthDays[month] - 1);

        return monthOffsets[month] + (validDay * dayWidth);
    }

    milestoneItems.forEach(item => {
        const startDate = new Date(item.dataset.start);
        const endDate = new Date(item.dataset.end);
        const milestoneId = item.dataset.milestoneId;

        const startPixel = dateToPixel(startDate);
        const endPixel = dateToPixel(endDate) + dayWidth; // 종료일은 해당 날까지 포함하므로 +1일
        const width = endPixel - startPixel;

        const milestoneBar = item.querySelector('.milestone-bar');
        milestoneBar.style.left = startPixel + 'px';
        milestoneBar.style.width = width + 'px';

        // 툴팁 이벤트
        milestoneBar.addEventListener('mouseenter', function(e) {
            const title = this.dataset.title;

            // ⭐ 최신 날짜를 data 속성에서 다시 읽기 (드래그 업데이트 반영)
            const parentItem = this.closest('.milestone-timeline-item');
            const currentStartDate = new Date(parentItem.dataset.start);
            const currentEndDate = new Date(parentItem.dataset.end);

            const startStr = formatDateForDisplay(currentStartDate);
            const endStr = formatDateForDisplay(currentEndDate);

            tooltip.textContent = `${title} (${startStr} ~ ${endStr})`;
            tooltip.style.display = 'block';
        });

        milestoneBar.addEventListener('mousemove', function(e) {
            if (tooltip.style.display === 'block') {
                tooltip.style.left = (e.pageX + 10) + 'px';
                tooltip.style.top = (e.pageY - 30) + 'px';
            }
        });

        milestoneBar.addEventListener('mouseleave', function() {
            tooltip.style.display = 'none';
        });

        // 드래그 앤 드롭 시스템
        milestoneBar.addEventListener('mousedown', function(e) {
            e.preventDefault();
            const startX = e.clientX;
            const startLeft = parseInt(this.style.left);
            const startWidth = parseInt(this.style.width);

            // 드래그 중 시각적 피드백
            this.style.cursor = 'grabbing';
            this.style.opacity = '0.8';

            // 툴팁 숨기기
            tooltip.style.display = 'none';

            const handleMouseMove = (e) => {
                const deltaX = e.clientX - startX;

                // 새로운 위치 계산 (일 단위로 스냅)
                const newLeft = snapToDay(startLeft + deltaX);
                const newRight = newLeft + startWidth;

                // 경계 체크 (0 이상, 총 너비 이하)
                if (newLeft >= 0 && newRight <= totalWidth) {
                    milestoneBar.style.left = newLeft + 'px';
                }
            };

            const handleMouseUp = () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);

                // 드래그 완료 후 스타일 복원
                milestoneBar.style.opacity = '1';
                milestoneBar.style.cursor = 'move';

                // 툴팁 숨기기
                tooltip.style.display = 'none';

                // 새로운 날짜 계산
                const newLeft = parseInt(milestoneBar.style.left);
                const newWidth = parseInt(milestoneBar.style.width);
                const newRight = newLeft + newWidth; // 전체 너비

                const newStartDate = pixelToDate(newLeft);
                // 종료일은 실제 마지막 날짜로 계산 (다음 날 시작점에서 -1일)
                const nextDayDate = pixelToDate(newRight);
                const newEndDate = new Date(nextDayDate);
                newEndDate.setDate(nextDayDate.getDate() - 1);

                // 서버에 업데이트 전송
                console.log('드래그 완료 - 새로운 날짜:', {
                    startdate: formatDate(newStartDate),
                    enddate: formatDate(newEndDate)
                });
                updateMilestone(milestoneId, {
                    startdate: formatDate(newStartDate),
                    enddate: formatDate(newEndDate)
                });
            };

            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        });

        // 드래그 시작시 커서 변경
        milestoneBar.addEventListener('mouseenter', function() {
            this.style.cursor = 'move';
        });

        milestoneBar.addEventListener('dragstart', function(e) {
            e.preventDefault();
        });

        // 리사이즈 핸들 추가 및 이벤트 (기간 조정)
        const leftHandle = document.createElement('div');
        leftHandle.className = 'resize-handle resize-handle-left';
        leftHandle.style.cssText = `
            position: absolute;
            left: -3px;
            top: 0;
            bottom: 0;
            width: 6px;
            cursor: ew-resize;
            background: transparent;
            z-index: 10;
        `;

        const rightHandle = document.createElement('div');
        rightHandle.className = 'resize-handle resize-handle-right';
        rightHandle.style.cssText = `
            position: absolute;
            right: -3px;
            top: 0;
            bottom: 0;
            width: 6px;
            cursor: ew-resize;
            background: transparent;
            z-index: 10;
        `;

        milestoneBar.appendChild(leftHandle);
        milestoneBar.appendChild(rightHandle);

        // 좌측 핸들 - 시작일 조정
        leftHandle.addEventListener('mousedown', function(e) {
            e.stopPropagation();
            e.preventDefault();

            const startX = e.clientX;
            const originalLeft = parseInt(milestoneBar.style.left);
            const originalWidth = parseInt(milestoneBar.style.width);
            const rightEdge = originalLeft + originalWidth;

            tooltip.style.display = 'none';

            const handleMouseMove = (e) => {
                const deltaX = e.clientX - startX;
                const newLeft = snapToDay(originalLeft + deltaX);
                const newWidth = rightEdge - newLeft;

                // 최소 너비 체크 (1일 이상)
                if (newWidth >= dayWidth && newLeft >= 0) {
                    milestoneBar.style.left = newLeft + 'px';
                    milestoneBar.style.width = newWidth + 'px';
                }
            };

            const handleMouseUp = () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);

                // 새로운 시작일 계산
                const newLeft = parseInt(milestoneBar.style.left);
                const newWidth = parseInt(milestoneBar.style.width);
                const newRight = newLeft + newWidth;

                const newStartDate = pixelToDate(newLeft);
                const nextDayDate = pixelToDate(newRight);
                const newEndDate = new Date(nextDayDate);
                newEndDate.setDate(nextDayDate.getDate() - 1);

                updateMilestone(milestoneId, {
                    startdate: formatDate(newStartDate),
                    enddate: formatDate(newEndDate)
                });
            };

            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        });

        // 우측 핸들 - 종료일 조정
        rightHandle.addEventListener('mousedown', function(e) {
            e.stopPropagation();
            e.preventDefault();

            const startX = e.clientX;
            const originalLeft = parseInt(milestoneBar.style.left);
            const originalWidth = parseInt(milestoneBar.style.width);

            tooltip.style.display = 'none';

            const handleMouseMove = (e) => {
                const deltaX = e.clientX - startX;
                const newWidth = snapToDay(originalWidth + deltaX) - originalLeft + originalLeft;

                // 최소 너비 체크 및 경계 체크
                if (newWidth >= dayWidth && originalLeft + newWidth <= totalWidth) {
                    milestoneBar.style.width = newWidth + 'px';
                }
            };

            const handleMouseUp = () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);

                // 새로운 종료일 계산
                const newLeft = parseInt(milestoneBar.style.left);
                const newWidth = parseInt(milestoneBar.style.width);
                const newRight = newLeft + newWidth;

                const newStartDate = pixelToDate(newLeft);
                const nextDayDate = pixelToDate(newRight);
                const newEndDate = new Date(nextDayDate);
                newEndDate.setDate(nextDayDate.getDate() - 1);

                updateMilestone(milestoneId, {
                    startdate: formatDate(newStartDate),
                    enddate: formatDate(newEndDate)
                });
            };

            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
        });
    });

    // 마일스톤 상태 계산 (클라이언트 사이드)
    function calculateMilestoneStatus(startdate, enddate, progressPercentage) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);  // 시간 제거

        const start = new Date(startdate);
        start.setHours(0, 0, 0, 0);

        const end = new Date(enddate);
        end.setHours(0, 0, 0, 0);

        // 100% 완료
        if (progressPercentage >= 100) {
            return 'completed';
        }

        // 시작 전
        if (today < start) {
            return 'not_started';
        }

        // 지연
        if (today > end) {
            return 'overdue';
        }

        // 진행 중
        return 'in_progress';
    }

    // 마일스톤 업데이트 API 함수 (API Client 사용)
    async function updateMilestone(milestoneId, data) {
        try {
            const response = await apiClient.patch(
                `/teams/${window.teamData.id}/milestones/${milestoneId}/`,
                data
            );

            if (response.success) {
                console.log('마일스톤 업데이트 성공:', response.message);

                // 좌측 정보 패널의 날짜 정보도 업데이트
                const infoItem = document.querySelector(`.milestone-info-item[data-milestone-id="${milestoneId}"]`);
                const timelineItem = document.querySelector(`.milestone-timeline-item[data-milestone-id="${milestoneId}"]`);

                if (infoItem && response.milestone) {
                    const dateRange = infoItem.querySelector('.date-range');
                    const newStart = new Date(response.milestone.startdate);
                    const newEnd = new Date(response.milestone.enddate);
                    dateRange.textContent = `${(newStart.getMonth()+1).toString().padStart(2,'0')}/${newStart.getDate().toString().padStart(2,'0')} - ${(newEnd.getMonth()+1).toString().padStart(2,'0')}/${newEnd.getDate().toString().padStart(2,'0')}`;

                    // 진행률 업데이트 (있는 경우)
                    if (response.milestone.progress_percentage !== undefined) {
                        const progressElement = infoItem.querySelector('.progress');
                        if (progressElement) {
                            progressElement.textContent = `${response.milestone.progress_percentage}%`;
                        }
                    }

                    // ⭐ 상태 재계산 및 data-status 업데이트
                    const newStatus = calculateMilestoneStatus(
                        response.milestone.startdate,
                        response.milestone.enddate,
                        response.milestone.progress_percentage || 0
                    );

                    // 좌측 패널 상태 업데이트
                    infoItem.setAttribute('data-status', newStatus);

                    // 타임라인 아이템 상태 업데이트
                    if (timelineItem) {
                        timelineItem.setAttribute('data-status', newStatus);
                        timelineItem.setAttribute('data-start', response.milestone.startdate);
                        timelineItem.setAttribute('data-end', response.milestone.enddate);
                    }

                    // ⭐ 필터 재적용 (상태 변경 시 필터에서 보이거나 숨겨질 수 있음)
                    applyFilter();
                }

                showDjangoToast(response.message || '마일스톤이 업데이트되었습니다.', 'success');
            } else {
                throw new Error(response.error || '업데이트에 실패했습니다.');
            }
        } catch (error) {
            console.error('마일스톤 업데이트 실패:', error);
            showDjangoToast(`업데이트에 실패했습니다: ${error.message}`, 'error');
            location.reload(); // 실패시 페이지 새로고침
        }
    }

    // 오늘 날짜 마커 추가
    function addTodayMarker() {
        // 로컬 시간대의 오늘 날짜 (시간 정보 제거 후 다음날로)
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        today.setDate(today.getDate() + 1); // 다음날로 설정
        const todayPixel = dateToPixel(today);

        const todayMarker = document.createElement('div');
        todayMarker.className = 'today-marker';
        todayMarker.style.cssText = `
            position: absolute;
            left: ${todayPixel}px;
            top: 0;
            bottom: 0;
            width: 3px;
            background: #10b981;
            z-index: 100;
            pointer-events: none;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
        `;

        // 오늘 날짜 레이블
        const todayLabel = document.createElement('div');
        todayLabel.className = 'today-label';
        todayLabel.textContent = '오늘';
        todayLabel.style.cssText = `
            position: absolute;
            left: ${todayPixel + 8}px;
            top: 10px;
            background: #10b981;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            z-index: 101;
            pointer-events: none;
            white-space: nowrap;
        `;

        scrollContent.appendChild(todayMarker);
        scrollContent.appendChild(todayLabel);

        console.log(`오늘 날짜: ${today.getFullYear()}-${(today.getMonth()+1).toString().padStart(2,'0')}-${today.getDate().toString().padStart(2,'0')}`);
        console.log(`오늘 날짜 마커 추가: ${todayPixel}px`);
    }

    // 페이지 로드 시 현재 날짜 위치로 스크롤
    function scrollToCurrentDate() {
        // 로컬 시간대의 오늘 날짜 (시간 정보 제거 후 다음날로)
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        today.setDate(today.getDate() + 1); // 다음날로 설정
        const todayPixel = dateToPixel(today);
        const scrollContainer = document.querySelector('.timeline-scroll-area');

        // 타임라인 컨테이너 너비의 절반을 빼서 현재 날짜가 중앙에 오도록 조정
        const containerWidth = scrollContainer.clientWidth;
        const scrollPosition = Math.max(0, todayPixel - (containerWidth / 2));

        // 부드러운 스크롤 효과
        scrollContainer.scrollTo({
            left: scrollPosition,
            behavior: 'smooth'
        });

        console.log(`오늘 날짜 (${today.toDateString()})로 스크롤: ${scrollPosition}px`);
    }

    // 오늘 날짜 마커 추가 및 스크롤 실행
    addTodayMarker();
    setTimeout(scrollToCurrentDate, 100);

    // 필터 기능 초기화
    initializeFilters();

    // 마일스톤 생성 모달 초기화
    initializeCreateMilestoneModal();
});

// ========================================
// 필터 기능
// ========================================

// 필터 상태 저장
const filterState = {
    status: ['in_progress', 'not_started', 'overdue', 'completed'],  // 기본: 전체
    priority: ['critical', 'high', 'medium', 'low', 'minimal']
};

function initializeFilters() {
    // localStorage에서 필터 상태 복원
    const savedFilter = localStorage.getItem('milestoneFilter');
    if (savedFilter) {
        try {
            const parsed = JSON.parse(savedFilter);
            Object.assign(filterState, parsed);

            // 저장된 프리셋 적용
            const activePreset = localStorage.getItem('milestoneFilterPreset') || 'all';
            updateFilterButtonState(activePreset);
        } catch (e) {
            console.error('필터 복원 실패:', e);
        }
    }

    // 필터 버튼 이벤트 등록
    const filterButtons = document.querySelectorAll('.filter-preset');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const preset = btn.dataset.preset;
            applyFilterPreset(preset);

            // 버튼 상태 업데이트
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // localStorage에 저장
            localStorage.setItem('milestoneFilterPreset', preset);
        });
    });

    // 초기 필터 적용
    const activePreset = localStorage.getItem('milestoneFilterPreset') || 'all';
    applyFilterPreset(activePreset);
}

function applyFilterPreset(preset) {
    switch(preset) {
        case 'all':
            filterState.status = ['in_progress', 'not_started', 'overdue', 'completed'];
            break;
        case 'active':
            filterState.status = ['in_progress'];
            break;
        case 'overdue':
            filterState.status = ['overdue'];
            break;
        case 'incomplete':
            filterState.status = ['in_progress', 'not_started', 'overdue'];
            break;
    }

    applyFilter();

    // localStorage에 저장
    localStorage.setItem('milestoneFilter', JSON.stringify(filterState));
}

function applyFilter() {
    // 타임라인 아이템 필터링
    const timelineItems = document.querySelectorAll('.milestone-timeline-item');
    timelineItems.forEach(item => {
        const status = item.dataset.status;
        const priority = item.dataset.priority;

        const visible =
            filterState.status.includes(status) &&
            filterState.priority.includes(priority);

        item.style.display = visible ? 'block' : 'none';
    });

    // 좌측 정보 패널 필터링
    const infoItems = document.querySelectorAll('.milestone-info-item');
    infoItems.forEach(item => {
        const status = item.dataset.status;
        const priority = item.dataset.priority;

        const visible =
            filterState.status.includes(status) &&
            filterState.priority.includes(priority);

        item.style.display = visible ? 'flex' : 'none';
    });
}

function updateFilterButtonState(preset) {
    const filterButtons = document.querySelectorAll('.filter-preset');
    filterButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.preset === preset);
    });
}

// ========================================
// 마일스톤 생성 모달
// ========================================

function initializeCreateMilestoneModal() {
    const modal = document.getElementById('createMilestoneModal');
    const openBtn = document.getElementById('addMilestoneBtn');
    const closeBtn = document.getElementById('createModalClose');
    const cancelBtn = document.getElementById('createCancelBtn');
    const form = document.getElementById('createMilestoneForm');

    // 모달 열기
    openBtn.addEventListener('click', () => {
        modal.classList.add('active');
        // 시작일을 오늘로 기본 설정
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('startdate').value = today;
    });

    // 모달 닫기
    const closeModal = () => {
        modal.classList.remove('active');
        form.reset();
    };

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    // 모달 외부 클릭 시 닫기
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // 입력 필드 참조
    const titleInput = document.getElementById('title');
    const startDateInput = document.getElementById('startdate');
    const endDateInput = document.getElementById('enddate');
    const priorityInput = document.getElementById('priority');

    // 입력 시 에러 상태 제거
    [titleInput, startDateInput, endDateInput, priorityInput].forEach(input => {
        input.addEventListener('input', function() {
            if (this.value.trim()) {
                clearFieldError(this);
            }
        });
    });

    // 폼 제출
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 필수 필드 검증
        const isValid = validateRequiredFields([
            { input: titleInput, message: '마일스톤 제목을 입력해주세요.' },
            { input: startDateInput, message: '시작일을 선택해주세요.' },
            { input: endDateInput, message: '종료일을 선택해주세요.' },
            { input: priorityInput, message: '우선순위를 선택해주세요.' }
        ]);

        if (!isValid) return;

        const formData = {
            title: titleInput.value,
            description: document.getElementById('description').value,
            startdate: startDateInput.value,
            enddate: endDateInput.value,
            priority: priorityInput.value
        };

        // 날짜 유효성 검사
        if (new Date(formData.startdate) > new Date(formData.enddate)) {
            showDjangoToast('종료일은 시작일보다 이후여야 합니다.', 'error');
            return;
        }

        try {
            const response = await apiClient.post(
                `/teams/${window.teamData.id}/milestones/`,
                formData
            );

            if (response.success) {
                showDjangoToast(response.message || '마일스톤이 추가되었습니다.', 'success');
                closeModal();
                // 페이지 새로고침으로 새 마일스톤 표시
                setTimeout(() => location.reload(), 500);
            } else {
                throw new Error(response.error || '마일스톤 추가에 실패했습니다.');
            }
        } catch (error) {
            console.error('마일스톤 생성 실패:', error);
            showDjangoToast(`마일스톤 추가에 실패했습니다: ${error.message}`, 'error');
        }
    });
}

// ========================================
// 마일스톤 삭제 함수
// ========================================

async function deleteMilestone(milestoneId, milestoneName) {
    showConfirmModal(
        `정말로 '<strong>${milestoneName}</strong>' 마일스톤을 삭제하시겠습니까?<br><small style="color: #6b7280;">이 작업은 되돌릴 수 없습니다.</small>`,
        async () => {
            try {
                const response = await apiClient.delete(
                    `/teams/${window.teamData.id}/milestones/${milestoneId}/`
                );

                if (response.success) {
                    showDjangoToast(response.message || '마일스톤이 삭제되었습니다.', 'success');
                    // 페이지 새로고침으로 UI 업데이트
                    setTimeout(() => location.reload(), 500);
                } else {
                    throw new Error(response.error || '삭제에 실패했습니다.');
                }
            } catch (error) {
                console.error('마일스톤 삭제 실패:', error);
                showDjangoToast(`삭제에 실패했습니다: ${error.message}`, 'error');
                location.reload();
            }
        }
    );
}