// 마일스톤 타임라인 페이지 전용 JavaScript

// 월별 실제 일수 기반 타임라인 시스템 (Today-based Rolling Window ±6개월, 확장 가능)
document.addEventListener('DOMContentLoaded', function() {
    const scrollContent = document.querySelector('.timeline-scroll-content');
    const monthHeaders = document.getElementById('monthHeaders');
    const dayWidth = 12; // 일당 픽셀 너비

    // ==================== 확장 상태 관리 ====================
    let expandedLeft = false;   // 과거 방향 확장 여부
    let expandedRight = false;  // 미래 방향 확장 여부

    // ==================== 서버 시간 기준 Rolling Window 계산 ====================

    // 서버에서 전달받은 오늘 날짜 파싱 (YYYY-MM-DD)
    const today = new Date(window.teamData.today);
    today.setHours(0, 0, 0, 0);

    // 타임라인 범위 계산 함수 (확장 상태에 따라 동적 계산)
    function calculateTimelineRange() {
        const leftMonths = expandedLeft ? 12 : 6;
        const rightMonths = expandedRight ? 12 : 6;

        // 타임라인 시작일 (오늘 -leftMonths개월)
        const start = new Date(today);
        start.setMonth(start.getMonth() - leftMonths);
        start.setDate(1); // 월 첫째 날로 설정

        // 타임라인 종료일 (오늘 +rightMonths개월)
        const end = new Date(today);
        end.setMonth(end.getMonth() + rightMonths);
        // 해당 월의 마지막 날로 설정
        end.setMonth(end.getMonth() + 1);
        end.setDate(0);

        return { start, end };
    }

    let timelineRange = calculateTimelineRange();
    let timelineStart = timelineRange.start;
    let timelineEnd = timelineRange.end;

    // 각 월의 일수 계산 (윤년 고려)
    function getDaysInMonth(year, month) {
        return new Date(year, month + 1, 0).getDate();
    }

    // 월별 일수 배열과 누적 위치 계산 (동적 범위)
    let monthDays = [];
    let monthOffsets = [];
    let monthYears = []; // 각 월의 연도 저장 (연도 구분선용)
    let totalOffset = 0;

    // timelineStart부터 timelineEnd까지 순회
    const currentMonth = new Date(timelineStart);
    let monthIndex = 0;

    while (currentMonth <= timelineEnd) {
        const year = currentMonth.getFullYear();
        const month = currentMonth.getMonth();

        monthOffsets[monthIndex] = totalOffset;
        monthYears[monthIndex] = year;
        const daysInMonth = getDaysInMonth(year, month);
        monthDays[monthIndex] = daysInMonth;
        totalOffset += daysInMonth * dayWidth;

        // 다음 달로 이동
        currentMonth.setMonth(currentMonth.getMonth() + 1);
        monthIndex++;
    }

    let totalWidth = totalOffset; // 전체 타임라인 너비
    let totalMonths = monthIndex; // 총 월 개수

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

    // 월 헤더 동적 생성 (연도 포함)
    const monthNames = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
    // ========================================
    // 📌 함수 정의: 타임라인 구조 렌더링
    // ========================================
    function renderTimelineStructure() {
        // 기존 타임라인 요소 제거
        monthHeaders.innerHTML = '';
        const markers = scrollContent.querySelectorAll('.month-marker, .day-marker, .today-marker, .today-label');
        markers.forEach(marker => marker.remove());

        // 월 헤더 동적 생성
        const startMonth = new Date(timelineStart);

        for (let i = 0; i < totalMonths; i++) {
            const year = monthYears[i];
            const month = startMonth.getMonth();
            const nextYear = i < totalMonths - 1 ? monthYears[i + 1] : year;
            const isYearChanging = year !== nextYear;

            const monthHeader = document.createElement('div');
            monthHeader.className = 'month-header';

            if (i === 0 || month === 0 || isYearChanging) {
                monthHeader.textContent = `${year}년 ${monthNames[month]}`;
            } else {
                monthHeader.textContent = monthNames[month];
            }

            monthHeader.style.cssText = `
                position: absolute;
                left: ${monthOffsets[i]}px;
                width: ${monthDays[i] * dayWidth}px;
            `;
            monthHeaders.appendChild(monthHeader);

            startMonth.setMonth(startMonth.getMonth() + 1);
        }

        // 월별 구분선 및 연도 구분선 동적 생성
        for (let i = 1; i < totalMonths; i++) {
            const monthMarker = document.createElement('div');
            monthMarker.className = 'month-marker';

            const currentYear = monthYears[i];
            const prevYear = monthYears[i - 1];

            if (currentYear !== prevYear) {
                monthMarker.style.cssText = `
                    position: absolute;
                    left: ${monthOffsets[i]}px;
                    top: 0;
                    bottom: 0;
                    width: 2px;
                    background: #6b7280;
                    pointer-events: none;
                    z-index: 50;
                `;
            } else {
                monthMarker.style.cssText = `
                    position: absolute;
                    left: ${monthOffsets[i]}px;
                    top: 0;
                    bottom: 0;
                    width: 2px;
                    background: #d1d5db;
                    pointer-events: none;
                `;
            }

            scrollContent.appendChild(monthMarker);
        }

        // 일별 구분선 생성
        for (let i = 0; i < totalMonths; i++) {
            for (let day = 1; day <= monthDays[i]; day++) {
                const dayPos = monthOffsets[i] + ((day - 1) * dayWidth);
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
    }

    const milestoneItems = document.querySelectorAll('.milestone-timeline-item');

    // 날짜 <-> 픽셀 변환 함수들 (연도 고려, Rolling Window 기반)
    function dateToPixel(date) {
        const targetDate = new Date(date);
        targetDate.setHours(0, 0, 0, 0);

        // 타임라인 범위를 벗어나면 경계값 반환
        if (targetDate < timelineStart) return 0;
        if (targetDate > timelineEnd) return totalWidth;

        // 타임라인 시작일부터 해당 날짜까지의 픽셀 계산
        const currentDate = new Date(timelineStart);
        let pixel = 0;
        let monthIdx = 0;

        while (currentDate < targetDate && monthIdx < totalMonths) {
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth();

            // 같은 년월이면 일수 차이 계산
            if (targetDate.getFullYear() === year && targetDate.getMonth() === month) {
                pixel += (targetDate.getDate() - 1) * dayWidth;
                break;
            }

            // 다른 월이면 전체 월 일수만큼 더하고 다음 달로
            pixel += monthDays[monthIdx] * dayWidth;
            currentDate.setMonth(currentDate.getMonth() + 1);
            monthIdx++;
        }

        return pixel;
    }

    function pixelToDate(pixel) {
        // 어느 월에 속하는지 찾기
        let monthIdx = 0;
        for (let i = 0; i < totalMonths; i++) {
            if (pixel >= monthOffsets[i] && (i === totalMonths - 1 || pixel < monthOffsets[i + 1])) {
                monthIdx = i;
                break;
            }
        }

        // 해당 월 내에서의 일수 계산
        const dayInMonth = Math.floor((pixel - monthOffsets[monthIdx]) / dayWidth) + 1;
        const validDay = Math.min(Math.max(dayInMonth, 1), monthDays[monthIdx]);

        // timelineStart로부터 monthIdx만큼 이동한 날짜 계산
        const resultDate = new Date(timelineStart);
        resultDate.setMonth(timelineStart.getMonth() + monthIdx);
        resultDate.setDate(validDay);

        return resultDate;
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
        let monthIdx = 0;
        for (let i = 0; i < totalMonths; i++) {
            if (pixel >= monthOffsets[i] && (i === totalMonths - 1 || pixel < monthOffsets[i + 1])) {
                monthIdx = i;
                break;
            }
        }

        // 해당 월 내에서의 일수 계산하고 반올림
        const pixelInMonth = pixel - monthOffsets[monthIdx];
        const dayInMonth = Math.round(pixelInMonth / dayWidth);
        const validDay = Math.min(Math.max(dayInMonth, 0), monthDays[monthIdx] - 1);

        return monthOffsets[monthIdx] + (validDay * dayWidth);
    }

    // ========================================
    // 📌 함수 정의: 마일스톤 렌더링 (범위 체크 및 위치 설정)
    // ========================================
    function renderMilestones() {
        const milestoneItems = document.querySelectorAll('.milestone-timeline-item');

        milestoneItems.forEach(item => {
            const startDate = new Date(item.dataset.start);
            const endDate = new Date(item.dataset.end);

            // 범위 밖 마일스톤 숨김 처리
            if (endDate < timelineStart || startDate > timelineEnd) {
                item.style.display = 'none';
                return;
            }

            // 범위 내 마일스톤 표시
            item.style.display = '';
            const startPixel = dateToPixel(startDate);
            const endPixel = dateToPixel(endDate) + dayWidth;
            const width = endPixel - startPixel;

            const milestoneBar = item.querySelector('.milestone-bar');
            milestoneBar.style.left = startPixel + 'px';
            milestoneBar.style.width = width + 'px';
        });
    }

    // ========================================
    // 📌 함수 정의: 마일스톤 이벤트 리스너 초기화 (한 번만 실행)
    // ========================================
    function initializeMilestoneEvents() {
        milestoneItems.forEach(item => {
            const milestoneId = item.dataset.milestoneId;
            const milestoneBar = item.querySelector('.milestone-bar');

            // 툴팁 이벤트
        milestoneBar.addEventListener('mouseenter', function(e) {
            const title = this.dataset.title;

            // 최신 날짜를 data 속성에서 다시 읽기 (드래그 업데이트 반영)
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
    }

    // ========================================
    // 📌 초기 렌더링 실행
    // ========================================
    renderTimelineStructure();
    renderMilestones();
    initializeMilestoneEvents();

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

    // 마일스톤 업데이트 API 함수 (TeamApiClient 사용)
    async function updateMilestone(milestoneId, data) {
        try {
            const response = await window.teamApi.updateMilestone(
                window.teamData.id,
                milestoneId,
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

    // 오늘 날짜 마커 추가 (서버 시간 기준)
    function addTodayMarker() {
        // 서버에서 받은 오늘 날짜 사용 (이미 위에서 파싱됨)
        const todayMarkerDate = new Date(today);
        todayMarkerDate.setDate(todayMarkerDate.getDate() + 1); // 다음날로 설정
        const todayPixel = dateToPixel(todayMarkerDate);

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

        console.log(`오늘 날짜 (서버): ${formatDate(today)}`);
        console.log(`오늘 날짜 마커 추가: ${todayPixel}px`);
    }

    // 페이지 로드 시 현재 날짜 위치로 스크롤 (서버 시간 기준)
    function scrollToCurrentDate() {
        // 서버에서 받은 오늘 날짜 사용
        const todayMarkerDate = new Date(today);
        todayMarkerDate.setDate(todayMarkerDate.getDate() + 1); // 다음날로 설정
        const todayPixel = dateToPixel(todayMarkerDate);
        const scrollContainer = document.querySelector('.timeline-scroll-area');

        // 타임라인 컨테이너 너비의 절반을 빼서 현재 날짜가 중앙에 오도록 조정
        const containerWidth = scrollContainer.clientWidth;
        const scrollPosition = Math.max(0, todayPixel - (containerWidth / 2));

        // 부드러운 스크롤 효과
        scrollContainer.scrollTo({
            left: scrollPosition,
            behavior: 'smooth'
        });

        console.log(`오늘 날짜 (서버 ${formatDate(today)})로 스크롤: ${scrollPosition}px`);
    }

    // 오늘 날짜 마커 추가 및 스크롤 실행
    addTodayMarker();
    setTimeout(scrollToCurrentDate, 100);

    // ==================== 타임라인 범위 확장 기능 ====================

    // 마일스톤 정렬 (범위 내 마일스톤 위, 범위 밖 마일스톤 아래)
    function sortMilestonesByRange() {
        const leftPanel = document.querySelector('.milestone-info-list');
        const rightTimeline = document.querySelector('.timeline-scroll-content');

        if (!leftPanel || !rightTimeline) return;

        // 좌측 패널 아이템들
        const leftItems = Array.from(leftPanel.querySelectorAll('.milestone-info-item'));
        // 우측 타임라인 아이템들
        const rightItems = Array.from(rightTimeline.querySelectorAll('.milestone-timeline-item'));

        // 마일스톤을 범위 내/밖으로 분류
        const inRangeIds = [];
        const outOfRangeIds = [];

        rightItems.forEach(item => {
            const milestoneId = item.dataset.milestoneId;
            const startDate = new Date(item.dataset.start);
            const endDate = new Date(item.dataset.end);

            // 범위 체크
            if (endDate < timelineStart || startDate > timelineEnd) {
                outOfRangeIds.push(milestoneId);
            } else {
                inRangeIds.push(milestoneId);
            }
        });

        // 좌측 패널 정렬
        const sortedLeftItems = [
            ...leftItems.filter(item => inRangeIds.includes(item.dataset.milestoneId)),
            ...leftItems.filter(item => outOfRangeIds.includes(item.dataset.milestoneId))
        ];
        sortedLeftItems.forEach(item => leftPanel.appendChild(item));

        // 우측 타임라인 정렬
        const sortedRightItems = [
            ...rightItems.filter(item => inRangeIds.includes(item.dataset.milestoneId)),
            ...rightItems.filter(item => outOfRangeIds.includes(item.dataset.milestoneId))
        ];
        sortedRightItems.forEach(item => rightTimeline.appendChild(item));

        console.log(`마일스톤 정렬 완료 - 범위 내: ${inRangeIds.length}개, 범위 밖: ${outOfRangeIds.length}개`);
    }

    // 범위 외 마일스톤 개수 계산
    function countOutOfRangeMilestones() {
        const allMilestones = document.querySelectorAll('.milestone-timeline-item');
        let leftCount = 0;
        let rightCount = 0;

        console.log('=== countOutOfRangeMilestones 디버깅 ===');
        console.log(`타임라인 범위: ${formatDate(timelineStart)} ~ ${formatDate(timelineEnd)}`);
        console.log(`전체 마일스톤 개수: ${allMilestones.length}`);

        allMilestones.forEach(item => {
            const startDate = new Date(item.dataset.start);
            const endDate = new Date(item.dataset.end);

            // 마일스톤이 현재 타임라인 범위 밖에 있는지 확인
            if (endDate < timelineStart) {
                leftCount++; // 과거 (타임라인 시작 전)
                console.log(`좌측 범위 밖: ${formatDate(startDate)} ~ ${formatDate(endDate)}`);
            } else if (startDate > timelineEnd) {
                rightCount++; // 미래 (타임라인 종료 후)
                console.log(`우측 범위 밖: ${formatDate(startDate)} ~ ${formatDate(endDate)}`);
            }
        });

        console.log(`좌측 개수: ${leftCount}, 우측 개수: ${rightCount}`);
        console.log('========================================');

        return { left: leftCount, right: rightCount };
    }

    // 확장 인디케이터 상태 업데이트
    function updateExpandButtons() {
        const counts = countOutOfRangeMilestones();
        const leftIndicator = document.getElementById('expandLeftIndicator');
        const rightIndicator = document.getElementById('expandRightIndicator');
        const leftCount = document.getElementById('leftMilestoneCount');
        const rightCount = document.getElementById('rightMilestoneCount');

        console.log('=== updateExpandButtons 디버깅 ===');
        console.log(`expandedLeft: ${expandedLeft}, expandedRight: ${expandedRight}`);
        console.log(`leftIndicator 존재: ${!!leftIndicator}, rightIndicator 존재: ${!!rightIndicator}`);

        // 왼쪽 (과거) 인디케이터
        if (leftIndicator) {
            if (counts.left === 0) {
                // 범위 밖 마일스톤이 없으면 숨김
                leftIndicator.style.display = 'none';
                console.log(`좌측 인디케이터 숨김 (count: ${counts.left})`);
            } else if (expandedLeft) {
                // 최대 범위 도달 + 범위 밖 마일스톤 있음 → 비활성 인디케이터 표시
                leftIndicator.style.display = 'flex';
                leftIndicator.classList.add('disabled');
                leftCount.textContent = `${counts.left}개`;
                console.log(`좌측 인디케이터 비활성 표시 (최대 범위, ${counts.left}개)`);
            } else {
                // 확장 가능 + 범위 밖 마일스톤 있음 → 활성 인디케이터 표시
                leftIndicator.style.display = 'flex';
                leftIndicator.classList.remove('disabled');
                leftCount.textContent = `${counts.left}개`;
                console.log(`좌측 인디케이터 활성 표시 (${counts.left}개)`);
            }
        }

        // 오른쪽 (미래) 인디케이터
        if (rightIndicator) {
            // 우측 인디케이터 위치를 타임라인 콘텐츠 끝으로 설정
            rightIndicator.style.left = (totalWidth - 80) + 'px';

            if (counts.right === 0) {
                // 범위 밖 마일스톤이 없으면 숨김
                rightIndicator.style.display = 'none';
                console.log(`우측 인디케이터 숨김 (count: ${counts.right})`);
            } else if (expandedRight) {
                // 최대 범위 도달 + 범위 밖 마일스톤 있음 → 비활성 인디케이터 표시
                rightIndicator.style.display = 'flex';
                rightIndicator.classList.add('disabled');
                rightCount.textContent = `${counts.right}개`;
                console.log(`우측 인디케이터 비활성 표시 (최대 범위, ${counts.right}개, left: ${totalWidth - 80}px)`);
            } else {
                // 확장 가능 + 범위 밖 마일스톤 있음 → 활성 인디케이터 표시
                rightIndicator.style.display = 'flex';
                rightIndicator.classList.remove('disabled');
                rightCount.textContent = `${counts.right}개`;
                console.log(`우측 인디케이터 활성 표시 (${counts.right}개, left: ${totalWidth - 80}px)`);
            }
        }
        console.log('=====================================');
    }

    // 타임라인 재렌더링 (확장 시 호출)
    function rerenderTimeline() {
        // 0. 현재 스크롤 위치 저장 (날짜 기준)
        const scrollContainer = document.querySelector('.timeline-scroll-area');
        const currentScrollLeft = scrollContainer.scrollLeft;
        const currentDate = pixelToDate(currentScrollLeft);

        // 1. 범위 재계산
        timelineRange = calculateTimelineRange();
        timelineStart = timelineRange.start;
        timelineEnd = timelineRange.end;

        // 2. 월별 데이터 재계산
        const newMonthDays = [];
        const newMonthOffsets = [];
        const newMonthYears = [];
        let newTotalOffset = 0;

        const currentMonth = new Date(timelineStart);
        let monthIdx = 0;

        while (currentMonth <= timelineEnd) {
            const year = currentMonth.getFullYear();
            const month = currentMonth.getMonth();

            newMonthOffsets[monthIdx] = newTotalOffset;
            newMonthYears[monthIdx] = year;
            const daysInMonth = getDaysInMonth(year, month);
            newMonthDays[monthIdx] = daysInMonth;
            newTotalOffset += daysInMonth * dayWidth;

            currentMonth.setMonth(currentMonth.getMonth() + 1);
            monthIdx++;
        }

        // 전역 변수 업데이트
        monthDays = newMonthDays;
        monthOffsets = newMonthOffsets;
        monthYears = newMonthYears;
        totalWidth = newTotalOffset;
        totalMonths = monthIdx;

        // 3. 타임라인 구조 재렌더링
        renderTimelineStructure();

        // 4. 마일스톤 재렌더링
        renderMilestones();

        // 5. 오늘 마커 재추가
        addTodayMarker();

        // 6. 스크롤 위치 복원 (확장 전 보던 날짜 유지)
        setTimeout(() => {
            const newScrollLeft = dateToPixel(currentDate);
            scrollContainer.scrollLeft = newScrollLeft;
            console.log(`스크롤 위치 복원: ${formatDate(currentDate)} -> ${newScrollLeft}px`);
        }, 50);

        // 7. 마일스톤 정렬 (범위 밖 마일스톤 아래로)
        sortMilestonesByRange();

        // 8. 확장 버튼 상태 업데이트
        updateExpandButtons();

        console.log(`타임라인 재렌더링 완료 (leftExpanded: ${expandedLeft}, rightExpanded: ${expandedRight})`);
    }

    // 왼쪽 (과거) 확장 인디케이터 클릭 이벤트
    const expandLeftIndicator = document.getElementById('expandLeftIndicator');
    if (expandLeftIndicator) {
        expandLeftIndicator.addEventListener('click', function() {
            if (!expandedLeft) {
                expandedLeft = true;
                rerenderTimeline();
                showDjangoToast('과거 6개월 범위가 추가되었습니다.', 'info');
            } else {
                // 이미 최대 범위 (비활성 상태)
                showDjangoToast('이미 최대 범위(±12개월)입니다.', 'warning');
            }
        });
    }

    // 오른쪽 (미래) 확장 인디케이터 클릭 이벤트
    const expandRightIndicator = document.getElementById('expandRightIndicator');
    if (expandRightIndicator) {
        expandRightIndicator.addEventListener('click', function() {
            if (!expandedRight) {
                expandedRight = true;
                rerenderTimeline();
                showDjangoToast('미래 6개월 범위가 추가되었습니다.', 'info');
            } else {
                // 이미 최대 범위 (비활성 상태)
                showDjangoToast('이미 최대 범위(±12개월)입니다.', 'warning');
            }
        });
    }

    // 오늘 버튼 이벤트 (기존 scrollToCurrentDate 함수 재사용)
    document.getElementById('todayBtn').addEventListener('click', function() {
        scrollToCurrentDate();
    });

    // 초기 마일스톤 정렬 (범위 밖 마일스톤 아래로)
    sortMilestonesByRange();

    // 초기 확장 인디케이터 상태 설정
    updateExpandButtons();

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
            const startDate = new Date(item.dataset.start);
            const endDate = new Date(item.dataset.end);

            // 필터 조건 체크
            const matchesFilter =
                filterState.status.includes(status) &&
                filterState.priority.includes(priority);

            // 타임라인 범위 체크
            const inTimelineRange = !(endDate < timelineStart || startDate > timelineEnd);

            // 필터와 범위 모두 만족해야 표시
            item.style.display = (matchesFilter && inTimelineRange) ? 'block' : 'none';
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

    // 필터 기능 초기화
    initializeFilters();

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
            const response = await window.teamApi.createMilestone(
                window.teamData.id,
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

    // 마일스톤 생성 모달 초기화
    initializeCreateMilestoneModal();
});

// ========================================
// 마일스톤 삭제 함수 (전역)
// ========================================

async function deleteMilestone(milestoneId, milestoneName) {
    showConfirmModal(
        `정말로 '<strong>${milestoneName}</strong>' 마일스톤을 삭제하시겠습니까?<br><small style="color: #6b7280;">이 작업은 되돌릴 수 없습니다.</small>`,
        async () => {
            try {
                const response = await window.teamApi.deleteMilestone(
                    window.teamData.id,
                    milestoneId
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