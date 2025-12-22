/**
 * scheduler_page.js
 * API 기반 팀 가용성 실시간 조회
 */

document.addEventListener('DOMContentLoaded', function() {
    const weekInput = document.querySelector('input[type="week"]');
    const teamId = extractTeamIdFromURL();

    if (!weekInput || !teamId) {
        console.error('Required elements not found');
        return;
    }

    // 페이지 로드 시 현재 주차 데이터 자동 로드
    if (weekInput.value) {
        loadTeamAvailability(weekInput.value);
    }

    // 주차 입력 변경 시 자동 로드
    weekInput.addEventListener('change', function() {
        if (this.value) {
            loadTeamAvailability(this.value);
        }
    });

    /**
     * URL에서 팀 ID 추출
     */
    function extractTeamIdFromURL() {
        const pathParts = window.location.pathname.split('/');
        const scheduleIndex = pathParts.indexOf('scheduler_page');
        if (scheduleIndex !== -1 && pathParts[scheduleIndex + 1]) {
            return pathParts[scheduleIndex + 1];
        }
        return null;
    }

    /**
     * ISO week format (YYYY-W##) → YYYY-MM-DD (월요일)
     * scheduler_upload.js의 getWeekStartDate()와 동일한 로직
     */
    function getWeekStartDate(weekValue) {
        const [year, week] = weekValue.split('-W').map(Number);

        // ISO 주차 규칙: 1월 4일이 포함된 주가 Week 1
        const simple = new Date(year, 0, 4); // 1월 4일
        const dayOfWeek = simple.getDay() || 7; // 일요일 = 7
        const mondayOfWeek1 = new Date(simple);
        mondayOfWeek1.setDate(simple.getDate() - dayOfWeek + 1); // 첫 주 월요일

        // 목표 주의 월요일 계산
        const mondayOfTargetWeek = new Date(mondayOfWeek1);
        mondayOfTargetWeek.setDate(mondayOfWeek1.getDate() + (week - 1) * 7);

        // YYYY-MM-DD 형식으로 반환
        const yyyy = mondayOfTargetWeek.getFullYear();
        const mm = String(mondayOfTargetWeek.getMonth() + 1).padStart(2, '0');
        const dd = String(mondayOfTargetWeek.getDate()).padStart(2, '0');

        return `${yyyy}-${mm}-${dd}`;
    }

    /**
     * ISO week 형식(YYYY-Www)을 시작일/종료일로 변환
     * @param {string} weekString - ISO week 형식 (예: "2025-W40")
     * @returns {{startDate: string, endDate: string}} - ISO 형식 날짜 (YYYY-MM-DD)
     */
    function weekToDateRange(weekString) {
        const startDate = getWeekStartDate(weekString);
        const endDate = new Date(startDate);
        endDate.setDate(new Date(startDate).getDate() + 6);

        const yyyy = endDate.getFullYear();
        const mm = String(endDate.getMonth() + 1).padStart(2, '0');
        const dd = String(endDate.getDate()).padStart(2, '0');

        return {
            startDate: startDate,
            endDate: `${yyyy}-${mm}-${dd}`
        };
    }

    /**
     * API를 통해 팀 가용성 데이터 로드
     * @param {string} weekString - ISO week 형식 (예: "2025-W40")
     */
    async function loadTeamAvailability(weekString) {
        const { startDate, endDate } = weekToDateRange(weekString);
        const apiURL = `/api/v1/teams/${teamId}/schedules/team-availability/?start_date=${startDate}&end_date=${endDate}`;

        // 로딩 상태 표시
        showLoadingState(true);

        try {
            const response = await fetch(apiURL, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (response.ok && result.success) {
                updateScheduleTable(result.data);
                showDjangoToast('팀 가용성을 조회했습니다.', 'success');
            } else {
                throw new Error(result.error || '팀 가용성을 불러오는데 실패했습니다.');
            }
        } catch (error) {
            console.error('API Error:', error);
            showDjangoToast(error.message || '네트워크 오류가 발생했습니다.', 'error');
        } finally {
            showLoadingState(false);
        }
    }

    /**
     * 스케줄 테이블 업데이트
     * @param {Array} availabilityData - API 응답 데이터
     * [{date: "2025-09-29", availability: {0: 3, 1: 5, ...}}, ...]
     */
    function updateScheduleTable(availabilityData) {
        const scheduleGrid = document.querySelector('.schedule-grid');
        if (!scheduleGrid) {
            console.error('schedule-grid를 찾을 수 없습니다.');
            return;
        }

        // 기존 schedule-column 요소들 제거 (time-column은 유지)
        const existingColumns = scheduleGrid.querySelectorAll('.schedule-column');
        existingColumns.forEach(col => col.remove());

        // 각 날짜별로 column 동적 생성
        availabilityData.forEach((dayData, dayIndex) => {
            const dateObj = new Date(dayData.date + 'T00:00:00');
            const monthDay = `${dateObj.getMonth() + 1}/${dateObj.getDate()}`;
            const dayOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][dateObj.getDay()];

            // column div 생성
            const columnDiv = document.createElement('div');
            columnDiv.className = 'schedule-column';
            columnDiv.id = `schedulediv${dayIndex + 1}`;

            // 날짜 헤더 생성
            const header = document.createElement('div');
            header.className = 'schedule-day-header';
            header.innerHTML = `
                <div class="date-line">${monthDay}</div>
                <div class="day-line">(${dayOfWeek})</div>
            `;
            columnDiv.appendChild(header);

            // 24시간 슬롯 생성
            for (let hour = 0; hour < 24; hour++) {
                const availableCount = dayData.availability[hour] || 0;
                const slot = document.createElement('div');
                slot.className = `schedule-slot availability-${availableCount}`;
                slot.textContent = availableCount;
                columnDiv.appendChild(slot);
            }

            scheduleGrid.appendChild(columnDiv);
        });
    }

    /**
     * 로딩 상태 표시/숨김
     * @param {boolean} isLoading - 로딩 중 여부
     */
    function showLoadingState(isLoading) {
        const grid = document.querySelector('.schedule-grid');
        if (!grid) return;

        if (isLoading) {
            grid.style.opacity = '0.5';
            grid.style.pointerEvents = 'none';
        } else {
            grid.style.opacity = '1';
            grid.style.pointerEvents = 'auto';
        }
    }
});
