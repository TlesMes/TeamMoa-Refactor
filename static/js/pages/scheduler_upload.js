// 스케줄 업로드 페이지 전용 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const weekInput = document.getElementById('week');
    const scheduleForm = document.querySelector('.form-container');
    const teamId = window.TEAM_ID || window.location.pathname.match(/\/scheduler_upload_page\/(\d+)\//)?.[1];

    // 폼 제출 이벤트를 API 호출로 대체
    if (scheduleForm) {
        scheduleForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            // 필수 필드 검증
            const isValid = validateRequiredFields([
                { input: weekInput, message: '주차를 선택해주세요.' }
            ]);

            if (!isValid) return;

            const weekValue = weekInput.value;

            // ISO week format (YYYY-W##)을 YYYY-MM-DD 형식으로 변환
            const weekStart = getWeekStartDate(weekValue);

            // 체크된 모든 체크박스 수집
            const scheduleData = {};
            document.querySelectorAll('.schedule-checkbox').forEach(checkbox => {
                if (checkbox.checked) {
                    scheduleData[checkbox.name] = true;
                }
            });

            // 체크된 항목이 없으면 경고
            const checkedCount = Object.keys(scheduleData).length;
            if (checkedCount === 0) {
                showConfirmModal('가능한 시간대를 선택하지 않았습니다. 빈 스케줄로 저장하시겠습니까?', async () => {
                    await saveSchedule(teamId, weekStart, scheduleData);
                });
                return;
            }

            await saveSchedule(teamId, weekStart, scheduleData);
        });
    }

    // 주차 입력 변경 시 날짜 업데이트 및 에러 상태 제거
    if (weekInput) {
        weekInput.addEventListener('change', function() {
            // 값이 입력되면 에러 상태 제거
            if (this.value) {
                clearFieldError(this);
            }

            updateWeekDates(this.value);
        });

        // 초기값이 있으면 업데이트
        if (weekInput.value) {
            updateWeekDates(weekInput.value);
        }
    }

    const scheduleGrid = document.querySelector('.schedule-grid');

    // 개별 클릭 처리
    document.querySelectorAll('.schedule-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const slot = this.closest('.schedule-slot');
            updateSlotVisual(slot, this.checked);
        });
    });

    // 빠른 선택 도구 버튼 이벤트 리스너 등록
    const toolButtons = document.querySelectorAll('.tool-btn');
    toolButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            // 버튼 텍스트로 기능 판별
            const buttonText = this.textContent.trim();
            if (buttonText.includes('전체 선택')) {
                selectAllSlots();
            } else if (buttonText.includes('전체 해제')) {
                clearAllSlots();
            } else if (buttonText.includes('업무시간')) {
                selectWorkingHours();
            } else if (buttonText.includes('저녁시간')) {
                selectEveningHours();
            } else if (buttonText.includes('평일만')) {
                selectWeekdays();
            } else if (buttonText.includes('주말만')) {
                selectWeekends();
            }
        });
    });

    // 드래그 시작 (마우스)
    scheduleGrid.addEventListener('mousedown', function(e) {
        if (e.target.closest('.schedule-slot')) {
            const slot = e.target.closest('.schedule-slot');
            const checkbox = slot.querySelector('input[type="checkbox"]');

            isDragging = true;
            dragStartSlot = slot;
            hasMoved = false;

            // 드래그 모드 결정 (현재 상태의 반대)
            dragMode = checkbox.checked ? 'deselect' : 'select';

            // 첫 번째 슬롯 토글
            toggleSlot(slot);

            // 드래그 시각적 피드백
            scheduleGrid.classList.add('dragging');

            e.preventDefault(); // 텍스트 선택 방지
        }
    });

    // 드래그 중 (마우스)
    scheduleGrid.addEventListener('mouseover', function(e) {
        if (isDragging && e.target.closest('.schedule-slot')) {
            const slot = e.target.closest('.schedule-slot');
            const checkbox = slot.querySelector('input[type="checkbox"]');

            // 시작 슬롯이 아닌 경우에만 처리
            if (slot !== dragStartSlot) {
                hasMoved = true;

                // 드래그 모드에 따라 선택/해제
                if (dragMode === 'select' && !checkbox.checked) {
                    checkbox.checked = true;
                    checkbox.dispatchEvent(new Event('change'));
                } else if (dragMode === 'deselect' && checkbox.checked) {
                    checkbox.checked = false;
                    checkbox.dispatchEvent(new Event('change'));
                }
            }
        }
    });

    // 드래그 끝 (마우스)
    document.addEventListener('mouseup', function(e) {
        if (isDragging) {
            const slot = e.target.closest('.schedule-slot');

            // 시작점에서 끝났고 실제로 이동하지 않았다면 (단일 클릭)
            if (slot === dragStartSlot) {
                // 시작점의 토글을 되돌림 (단일 클릭 무효화)
                toggleSlot(dragStartSlot);
            }

            // 드래그는 무조건 중지
            isDragging = false;
            dragMode = null;
            dragStartSlot = null;
            hasMoved = false;
            scheduleGrid.classList.remove('dragging');
        }
    });

    // 터치 이벤트 (모바일 지원)
    scheduleGrid.addEventListener('touchstart', function(e) {
        if (e.target.closest('.schedule-slot')) {
            const slot = e.target.closest('.schedule-slot');
            const checkbox = slot.querySelector('input[type="checkbox"]');

            isDragging = true;
            dragStartSlot = slot;
            hasMoved = false;

            dragMode = checkbox.checked ? 'deselect' : 'select';
            toggleSlot(slot);

            e.preventDefault();
        }
    });

    scheduleGrid.addEventListener('touchmove', function(e) {
        if (isDragging) {
            e.preventDefault();
            const touch = e.touches[0];
            const element = document.elementFromPoint(touch.clientX, touch.clientY);
            const slot = element?.closest('.schedule-slot');

            if (slot && slot !== dragStartSlot) {
                hasMoved = true;
                const checkbox = slot.querySelector('input[type="checkbox"]');
                if (dragMode === 'select' && !checkbox.checked) {
                    checkbox.checked = true;
                    checkbox.dispatchEvent(new Event('change'));
                } else if (dragMode === 'deselect' && checkbox.checked) {
                    checkbox.checked = false;
                    checkbox.dispatchEvent(new Event('change'));
                }
            }
        }
    });

    document.addEventListener('touchend', function(e) {
        if (isDragging) {
            // 터치 종료 시점의 요소 확인
            const touch = e.changedTouches[0];
            const element = document.elementFromPoint(touch.clientX, touch.clientY);
            const slot = element?.closest('.schedule-slot');

            // 시작점에서 끝났다면 (단일 터치이든 드래그 후 복귀든)
            if (slot === dragStartSlot) {
                // 시작점의 토글을 되돌림
                toggleSlot(dragStartSlot);
            }

            // 드래그는 무조건 중지
            isDragging = false;
            dragMode = null;
            dragStartSlot = null;
            hasMoved = false;
            scheduleGrid.classList.remove('dragging');
        }
    });

    // 드래그 중 선택 방지
    scheduleGrid.addEventListener('selectstart', function(e) {
        if (isDragging) {
            e.preventDefault();
        }
    });
});

// 빠른 선택 도구 JavaScript 함수들
function selectAllSlots() {
    document.querySelectorAll('.schedule-checkbox').forEach(checkbox => {
        checkbox.checked = true;
        checkbox.dispatchEvent(new Event('change'));
    });
}

function clearAllSlots() {
    document.querySelectorAll('.schedule-checkbox').forEach(checkbox => {
        checkbox.checked = false;
        checkbox.dispatchEvent(new Event('change'));
    });
}

function selectWorkingHours() {
    clearAllSlots();
    // 9시부터 18시까지 (인덱스 9-17)
    for (let hour = 9; hour <= 17; hour++) {
        for (let day = 1; day <= 7; day++) {
            const checkbox = document.getElementById(`id_time_${hour}_${day}`);
            if (checkbox) {
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change'));
            }
        }
    }
}

function selectEveningHours() {
    clearAllSlots();
    // 18시부터 22시까지 (인덱스 18-21)
    for (let hour = 18; hour <= 21; hour++) {
        for (let day = 1; day <= 7; day++) {
            const checkbox = document.getElementById(`id_time_${hour}_${day}`);
            if (checkbox) {
                checkbox.checked = true;
                checkbox.dispatchEvent(new Event('change'));
            }
        }
    }
}

function selectWeekdays() {
    // 월요일(1)부터 금요일(5)까지
    document.querySelectorAll('.schedule-checkbox').forEach(checkbox => {
        const name = checkbox.name;
        const dayMatch = name.match(/time_\d+-(\d+)/);
        if (dayMatch) {
            const day = parseInt(dayMatch[1]);
            checkbox.checked = (day >= 1 && day <= 5);
            checkbox.dispatchEvent(new Event('change'));
        }
    });
}

function selectWeekends() {
    // 토요일(6), 일요일(7)
    document.querySelectorAll('.schedule-checkbox').forEach(checkbox => {
        const name = checkbox.name;
        const dayMatch = name.match(/time_\d+-(\d+)/);
        if (dayMatch) {
            const day = parseInt(dayMatch[1]);
            checkbox.checked = (day === 6 || day === 7);
            checkbox.dispatchEvent(new Event('change'));
        }
    });
}

// 주차 선택 시 날짜 업데이트
function updateWeekDates(weekValue) {
    if (!weekValue) return;

    // 정의된 getWeekStartDate 함수 사용
    const mondayOfTargetWeek = new Date(getWeekStartDate(weekValue));

    // 각 요일의 날짜 계산 및 업데이트
    for (let i = 0; i < 7; i++) {
        const currentDate = new Date(mondayOfTargetWeek.getTime() + i * 24 * 60 * 60 * 1000);
        const dayOfWeek = i === 6 ? 0 : i + 1; // 일요일은 0, 월~토는 1~6

        const header = document.querySelector(`[data-day="${dayOfWeek}"]`);
        if (header) {
            const dateLine = header.querySelector('.date-line');
            if (dateLine) {
                dateLine.textContent = `${currentDate.getMonth() + 1}/${currentDate.getDate()}`;
            }
        }
    }
}

// 드래그 선택 기능을 위한 전역 변수
let isDragging = false;
let dragMode = null; // 'select' 또는 'deselect'
let dragStartSlot = null; // 드래그 시작 슬롯
let hasMoved = false; // 드래그 중 실제로 움직였는지 확인

// 슬롯 토글 함수
function toggleSlot(slot) {
    const checkbox = slot.querySelector('input[type="checkbox"]');
    checkbox.checked = !checkbox.checked;
    checkbox.dispatchEvent(new Event('change'));
}

// 슬롯 시각적 업데이트 함수
function updateSlotVisual(slot, isChecked) {
    if (isChecked) {
        slot.classList.add('selected');
    } else {
        slot.classList.remove('selected');
    }
}

/**
 * API를 통한 스케줄 저장
 */
async function saveSchedule(teamId, weekStart, scheduleData) {
    try {
        const response = await scheduleApi.savePersonalSchedule(teamId, weekStart, scheduleData);

        if (response.success) {
            // 리다이렉트 후 표시할 메시지를 sessionStorage에 저장
            if (response.messages && response.messages.length > 0) {
                sessionStorage.setItem('pendingMessages', JSON.stringify(response.messages));
            }

            // 즉시 리다이렉트
            window.location.href = `/schedules/scheduler_page/${teamId}/`;
        } else {
            showDjangoToast(response.error || '스케줄 저장에 실패했습니다.', 'error');
        }
    } catch (error) {
        handleApiError(error);
    }
}

/**
 * ISO week format (YYYY-W##) → YYYY-MM-DD (월요일)
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
