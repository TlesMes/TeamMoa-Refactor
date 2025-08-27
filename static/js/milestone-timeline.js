// Milestone Timeline JavaScript - Drag & Drop Functionality
class MilestoneTimeline {
    constructor() {
        this.currentView = 'month';
        this.draggedMilestone = null;
        this.isDragging = false;
        this.isResizing = false;
        this.resizeDirection = null;
        
        this.init();
    }
    
    init() {
        this.generateTimelineDates();
        this.setupEventListeners();
        this.calculateMilestonePositions();
    }
    
    generateTimelineDates() {
        const datesContainer = document.getElementById('timelineDates');
        if (!datesContainer) return;
        
        // 현재 연도의 12개월 생성
        const currentYear = new Date().getFullYear();
        const months = [];
        
        for (let i = 0; i < 12; i++) {
            const date = new Date(currentYear, i, 1);
            const monthName = date.toLocaleDateString('ko-KR', { month: 'short' });
            months.push({
                month: i + 1,
                name: monthName,
                days: new Date(currentYear, i + 1, 0).getDate()
            });
        }
        
        // 각 월을 고정 비율로 설정 (총 4800px를 12개월로 나눠서 각 월의 일수 비율로 배분)
        const totalDays = months.reduce((sum, month) => sum + month.days, 0);
        
        // 월별 구분선 생성 (4800px 전체 영역에 걸쳐서)
        let cumulativeDays = 0;
        
        datesContainer.innerHTML = months.map((month, index) => {
            const monthStart = (cumulativeDays / totalDays) * 4800;
            cumulativeDays += month.days;
            
            return `
                <div class="timeline-month" data-month="${month.month}" style="left: ${monthStart}px;">
                    <div class="month-label">${month.name}</div>
                </div>
            `;
        }).join('');
        
        // 수직 그리드 라인 생성
        this.generateGridLines();
    }
    
    generateGridLines() {
        const timelineContent = document.getElementById('timelineMilestones');
        if (!timelineContent) return;
        
        // 기존 그리드 라인 제거
        const existingGridLines = timelineContent.querySelectorAll('.grid-line');
        existingGridLines.forEach(line => line.remove());
        
        // 고정 크기 기반으로 월별 그리드 라인 생성
        const currentYear = new Date().getFullYear();
        const yearStart = new Date(currentYear, 0, 1);
        const totalDays = Math.floor((new Date(currentYear, 11, 31) - yearStart) / (1000 * 60 * 60 * 24)) + 1;
        const availableWidth = 4800; // 전체 타임라인 영역 너비
        
        let cumulativeDays = 0;
        
        for (let month = 0; month < 12; month++) {
            const daysInMonth = new Date(currentYear, month + 1, 0).getDate();
            
            if (month > 0) { // 1월은 건너뛰기
                const monthStartX = (cumulativeDays / totalDays) * availableWidth;
                
                // 수직선 생성
                const gridLine = document.createElement('div');
                gridLine.className = 'grid-line';
                gridLine.style.cssText = `
                    position: absolute;
                    top: 0;
                    bottom: 0;
                    left: ${monthStartX}px;
                    width: 1px;
                    background-color: #dee2e6;
                    pointer-events: none;
                    z-index: 1;
                `;
                
                timelineContent.appendChild(gridLine);
            }
            
            cumulativeDays += daysInMonth;
        }
    }
    
    calculateMilestonePositions() {
        const milestoneRows = document.querySelectorAll('.milestone-timeline-row');
        if (milestoneRows.length === 0) return;
        
        const currentYear = new Date().getFullYear();
        const yearStart = new Date(currentYear, 0, 1);
        const yearEnd = new Date(currentYear, 11, 31);
        const totalDays = Math.floor((yearEnd - yearStart) / (1000 * 60 * 60 * 24)) + 1;
        
        // 전체 타임라인 너비 (4800px)
        const availableWidth = 4800;
        
        milestoneRows.forEach(row => {
            const milestoneBar = row.querySelector('.milestone-bar');
            if (!milestoneBar) return;
            
            const startDate = new Date(milestoneBar.dataset.start);
            const endDate = new Date(milestoneBar.dataset.end);
            
            // 시작일이 올해 범위를 벗어나면 조정
            const clampedStart = startDate < yearStart ? yearStart : startDate;
            const clampedEnd = endDate > yearEnd ? yearEnd : endDate;
            
            const startOffset = Math.floor((clampedStart - yearStart) / (1000 * 60 * 60 * 24));
            const duration = Math.floor((clampedEnd - clampedStart) / (1000 * 60 * 60 * 24)) + 1;
            
            const startPixels = (startOffset / totalDays) * availableWidth;
            const widthPixels = (duration / totalDays) * availableWidth;
            
            milestoneBar.style.left = `${startPixels}px`;
            milestoneBar.style.width = `${Math.max(widthPixels, 8)}px`; // 최소 8px (시각적 인식 가능한 최소 크기)
        });
    }
    
    
    setupEventListeners() {
        // 드래그 앤 드롭 이벤트
        const timelineContent = document.getElementById('timelineMilestones');
        if (timelineContent) {
            timelineContent.addEventListener('dragstart', this.handleDragStart.bind(this));
            timelineContent.addEventListener('dragover', this.handleDragOver.bind(this));
            timelineContent.addEventListener('drop', this.handleDrop.bind(this));
            timelineContent.addEventListener('dragend', this.handleDragEnd.bind(this));
        }
        
        // 마우스 이벤트 (리사이징)
        document.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // 타임라인 뷰 변경 버튼
        const viewButtons = document.querySelectorAll('.timeline-btn');
        viewButtons.forEach(btn => {
            btn.addEventListener('click', this.handleViewChange.bind(this));
        });
        
        // 진행률 바 클릭 이벤트
        const progressBars = document.querySelectorAll('.milestone-progress');
        progressBars.forEach(bar => {
            bar.addEventListener('click', this.handleProgressClick.bind(this));
        });
        
        // 마일스톤 바 더블클릭 (상세 모달)
        const milestoneBars = document.querySelectorAll('.milestone-bar');
        milestoneBars.forEach(bar => {
            bar.addEventListener('dblclick', this.showMilestoneModal.bind(this));
        });
        
        // 모달 닫기
        const modalClose = document.getElementById('modalClose');
        if (modalClose) {
            modalClose.addEventListener('click', this.hideMilestoneModal.bind(this));
        }
        
        // 모달 배경 클릭 시 닫기
        const modal = document.getElementById('milestoneModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideMilestoneModal();
                }
            });
        }
    }
    
    handleDragStart(e) {
        if (!e.target.classList.contains('milestone-bar')) return;
        
        this.draggedMilestone = e.target;
        e.target.classList.add('dragging');
        this.isDragging = true;
        
        // 드래그 데이터 설정
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.outerHTML);
    }
    
    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }
    
    handleDrop(e) {
        e.preventDefault();
        if (!this.isDragging || !this.draggedMilestone) return;
        
        // 드롭 위치 계산 (스크롤 영역에서만)
        const timelineContainer = e.currentTarget;
        const rect = timelineContainer.getBoundingClientRect();
        const dropX = e.clientX - rect.left;
        const containerWidth = 4800; // 타임라인 고정 너비
        
        // 새로운 시작 날짜 계산
        const dropPercentage = Math.max(0, Math.min(100, (dropX / containerWidth) * 100));
        const newStartDate = this.percentageToDate(dropPercentage);
        
        // 기존 기간 유지
        const currentStart = new Date(this.draggedMilestone.dataset.start);
        const currentEnd = new Date(this.draggedMilestone.dataset.end);
        const duration = currentEnd.getTime() - currentStart.getTime();
        const newEndDate = new Date(newStartDate.getTime() + duration);
        
        // UI 업데이트
        this.updateMilestoneUI(this.draggedMilestone, newStartDate, newEndDate);
        
        // 서버에 업데이트 전송
        this.updateMilestoneServer(
            this.draggedMilestone.dataset.milestoneId,
            newStartDate,
            newEndDate
        );
    }
    
    handleDragEnd(e) {
        if (e.target.classList.contains('milestone-bar')) {
            e.target.classList.remove('dragging');
        }
        this.isDragging = false;
        this.draggedMilestone = null;
    }
    
    handleMouseDown(e) {
        if (e.target.classList.contains('resize-handle')) {
            e.preventDefault();
            this.isResizing = true;
            this.resizeDirection = e.target.classList.contains('left') ? 'left' : 'right';
            this.draggedMilestone = e.target.closest('.milestone-bar');
            document.body.style.cursor = 'ew-resize';
        }
    }
    
    handleMouseMove(e) {
        if (!this.isResizing || !this.draggedMilestone) return;
        
        e.preventDefault();
        const timelineRow = this.draggedMilestone.closest('.milestone-timeline-row');
        const timelineContainer = document.getElementById('timelineMilestones');
        const rect = timelineContainer.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const containerWidth = 4800;
        
        const mousePercentage = Math.max(0, Math.min(100, (mouseX / containerWidth) * 100));
        const newDate = this.percentageToDate(mousePercentage);
        
        const currentStart = new Date(this.draggedMilestone.dataset.start);
        const currentEnd = new Date(this.draggedMilestone.dataset.end);
        
        if (this.resizeDirection === 'left') {
            // 시작일 변경 (종료일보다 이전이어야 함)
            if (newDate < currentEnd) {
                this.updateMilestoneUI(this.draggedMilestone, newDate, currentEnd);
            }
        } else {
            // 종료일 변경 (시작일보다 이후여야 함)
            if (newDate > currentStart) {
                this.updateMilestoneUI(this.draggedMilestone, currentStart, newDate);
            }
        }
    }
    
    handleMouseUp(e) {
        if (this.isResizing && this.draggedMilestone) {
            // 서버에 변경사항 전송
            const newStart = new Date(this.draggedMilestone.dataset.start);
            const newEnd = new Date(this.draggedMilestone.dataset.end);
            
            this.updateMilestoneServer(
                this.draggedMilestone.dataset.milestoneId,
                newStart,
                newEnd
            );
        }
        
        this.isResizing = false;
        this.resizeDirection = null;
        this.draggedMilestone = null;
        document.body.style.cursor = '';
    }
    
    handleViewChange(e) {
        const buttons = document.querySelectorAll('.timeline-btn');
        buttons.forEach(btn => btn.classList.remove('active'));
        e.target.classList.add('active');
        
        this.currentView = e.target.dataset.view;
        this.generateTimelineDates();
        this.calculateMilestonePositions();
    }
    
    handleProgressClick(e) {
        e.stopPropagation();
        const progressBar = e.target;
        const milestoneBar = progressBar.closest('.milestone-bar');
        const rect = progressBar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const newProgress = Math.round((clickX / rect.width) * 100);
        
        // UI 업데이트
        progressBar.style.width = `${newProgress}%`;
        
        // 진행률 정보 업데이트 (고정 영역에서 찾기)
        const milestoneId = milestoneBar.dataset.milestoneId;
        const milestoneInfoItem = document.querySelector(`.milestone-info-item[data-milestone-id="${milestoneId}"]`);
        const progressSpan = milestoneInfoItem ? milestoneInfoItem.querySelector('.progress') : null;
        if (progressSpan) {
            progressSpan.textContent = `${newProgress}%`;
        }
        
        // 서버에 업데이트 전송
        this.updateProgressServer(milestoneBar.dataset.milestoneId, newProgress);
    }
    
    showMilestoneModal(e) {
        const milestoneId = e.target.dataset.milestoneId;
        const milestone = milestones.find(m => m.id == milestoneId);
        
        if (!milestone) return;
        
        const modal = document.getElementById('milestoneModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalDetail = document.getElementById('milestoneDetail');
        
        modalTitle.textContent = milestone.title;
        modalDetail.innerHTML = `
            <div class="milestone-detail-item">
                <strong>설명:</strong>
                <p>${milestone.description || '설명이 없습니다.'}</p>
            </div>
            <div class="milestone-detail-item">
                <strong>기간:</strong>
                <p>${milestone.startDate} ~ ${milestone.endDate}</p>
            </div>
            <div class="milestone-detail-item">
                <strong>우선순위:</strong>
                <span class="priority priority-${milestone.priority}">${milestone.priorityDisplay}</span>
            </div>
            <div class="milestone-detail-item">
                <strong>진행률:</strong>
                <p>${milestone.progress}%</p>
            </div>
            <div class="milestone-detail-item">
                <strong>상태:</strong>
                <p>${milestone.isCompleted ? '완료됨' : '진행중'}</p>
            </div>
        `;
        
        modal.classList.add('active');
    }
    
    hideMilestoneModal() {
        const modal = document.getElementById('milestoneModal');
        modal.classList.remove('active');
    }
    
    percentageToDate(percentage) {
        const currentYear = new Date().getFullYear();
        const yearStart = new Date(currentYear, 0, 1);
        const yearEnd = new Date(currentYear, 11, 31);
        const totalDays = Math.floor((yearEnd - yearStart) / (1000 * 60 * 60 * 24)) + 1;
        
        const dayOffset = Math.round((percentage / 100) * totalDays);
        const resultDate = new Date(yearStart);
        resultDate.setDate(resultDate.getDate() + dayOffset);
        
        return resultDate;
    }
    
    updateMilestoneUI(milestoneBar, startDate, endDate) {
        // 데이터 속성 업데이트
        milestoneBar.dataset.start = startDate.toISOString().split('T')[0];
        milestoneBar.dataset.end = endDate.toISOString().split('T')[0];
        
        // 날짜 텍스트 업데이트
        const datesElement = milestoneBar.querySelector('.milestone-dates');
        if (datesElement) {
            const startStr = `${startDate.getMonth() + 1}/${startDate.getDate()}`;
            const endStr = `${endDate.getMonth() + 1}/${endDate.getDate()}`;
            datesElement.textContent = `${startStr} - ${endStr}`;
        }
        
        // 위치 재계산
        this.calculateMilestonePositions();
        
        // 그리드 라인도 다시 생성
        setTimeout(() => {
            this.generateGridLines();
        }, 100);
    }
    
    async updateMilestoneServer(milestoneId, startDate, endDate) {
        try {
            const response = await fetch(`/teams/${teamId}/milestone/${milestoneId}/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    startdate: startDate.toISOString().split('T')[0],
                    enddate: endDate.toISOString().split('T')[0]
                })
            });
            
            if (!response.ok) {
                throw new Error('서버 업데이트 실패');
            }
            
            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || '업데이트 실패');
            }
            
        } catch (error) {
            console.error('마일스톤 업데이트 오류:', error);
            alert('마일스톤 업데이트 중 오류가 발생했습니다.');
        }
    }
    
    async updateProgressServer(milestoneId, progress) {
        try {
            const response = await fetch(`/teams/${teamId}/milestone/${milestoneId}/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    progress_percentage: progress
                })
            });
            
            if (!response.ok) {
                throw new Error('진행률 업데이트 실패');
            }
            
            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || '업데이트 실패');
            }
            
        } catch (error) {
            console.error('진행률 업데이트 오류:', error);
            alert('진행률 업데이트 중 오류가 발생했습니다.');
        }
    }
    
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }
}

// DOM 로드 완료 후 타임라인 초기화
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('timelineChart')) {
        new MilestoneTimeline();
    }
});