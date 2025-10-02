/**
 * TODO DOM 조작 유틸리티 클래스
 * Members App의 실시간 UI 업데이트를 위한 중앙화된 DOM 관리
 */
class TodoDOMUtils {
    /**
     * 날짜를 "m/d" 또는 "mm/dd" 형식으로 변환 (Django 템플릿과 동일하게 0 패딩)
     * @param {Date|string} date - 변환할 날짜
     * @returns {string} 형식화된 날짜 문자열
     */
    static formatDate(date) {
        const d = date instanceof Date ? date : new Date(date);
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${month}/${day}`;
    }
    /**
     * TODO를 멤버 카드로 이동
     * @param {string} todoId - 이동할 TODO ID
     * @param {string} memberId - 대상 멤버 ID
     * @returns {Object} 백업 정보 (되돌리기용)
     */
    static moveTodoToMember(todoId, memberId) {
        const todoElement = document.querySelector(`[data-todo-id="${todoId}"]`);
        const memberCard = document.querySelector(`[data-member-id="${memberId}"]`);

        if (!todoElement || !memberCard) {
            return null;
        }

        // 백업 생성
        const backup = this.createBackup(todoElement);

        // 원본 요소 복제 및 드래그 상태 클래스 제거
        const clonedTodo = todoElement.cloneNode(true);
        clonedTodo.classList.remove('dragging'); // 드래그 상태 제거

        // 미할당 TODO를 할당된 TODO로 변환
        if (clonedTodo.classList.contains('todo-card')) {
            // 원본 생성일 보존 (data-created-at 속성)
            const createdAt = todoElement.dataset.createdAt;
            const isCompleted = todoElement.dataset.isCompleted === 'true';

            // 클래스 변경 (completed 상태 유지)
            clonedTodo.classList.remove('todo-card');
            clonedTodo.classList.add('assigned-todo');
            if (!clonedTodo.classList.contains('draggable')) {
                clonedTodo.classList.add('draggable');
            }
            // completed 클래스는 유지됨
            clonedTodo.setAttribute('draggable', 'true');

            // inline style 제거 (opacity 등)
            clonedTodo.style.opacity = '';
            clonedTodo.style.transition = '';

            // data-created-at 속성 보존
            if (createdAt) {
                clonedTodo.dataset.createdAt = createdAt;
            }

            // 텍스트 컨테이너 클래스 변경: .todo-content → .todo-text
            const contentElement = clonedTodo.querySelector('.todo-content');
            if (contentElement) {
                contentElement.className = 'todo-text';
            }

            // todo-meta 제거 (assigned-todo에는 meta가 없음)
            const metaElement = clonedTodo.querySelector('.todo-meta');
            if (metaElement) {
                metaElement.remove();
            }

            // 체크박스를 template과 동일한 구조로 추가 (checkbox-label 형태)
            const checkboxLabel = document.createElement('label');
            checkboxLabel.className = 'checkbox-label';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'complete-checkbox';
            checkbox.dataset.todoId = todoId;
            checkbox.checked = isCompleted; // 완료 상태 반영

            const checkmark = document.createElement('span');
            checkmark.className = 'checkmark';

            checkboxLabel.appendChild(checkbox);
            checkboxLabel.appendChild(checkmark);

            // 액션 버튼들 추가
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'todo-actions';

            const returnBtn = document.createElement('button');
            returnBtn.className = 'action-btn return-btn';
            returnBtn.title = '보드로 되돌리기';
            returnBtn.innerHTML = '↩';

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'action-btn delete-btn';
            deleteBtn.title = '삭제';
            deleteBtn.innerHTML = '✕';

            // 액션들을 올바른 순서로 추가
            actionsDiv.appendChild(checkboxLabel);  // 체크박스를 액션에 추가
            actionsDiv.appendChild(returnBtn);
            actionsDiv.appendChild(deleteBtn);
            clonedTodo.appendChild(actionsDiv);

            // data 속성 업데이트 (중요!)
            clonedTodo.dataset.assigneeId = memberId;
            clonedTodo.dataset.isCompleted = isCompleted ? 'true' : 'false';
            if (createdAt) {
                clonedTodo.dataset.createdAt = createdAt;
            }
        } else if (clonedTodo.classList.contains('assigned-todo')) {
            // 이미 assigned-todo인 경우 (멤버 간 이동)
            // data 속성 업데이트
            clonedTodo.dataset.assigneeId = memberId;
        }

        // 멤버 카드의 todos-list에 추가
        const todosList = memberCard.querySelector('.todos-list');
        if (todosList) {
            todosList.appendChild(clonedTodo);
        }

        // 보드에서 제거되는 경우 빈 메시지 복원 체크
        const parentTodoBoard = todoElement.closest('#todo-board');
        const parentDoneBoard = todoElement.closest('#done-board');

        // 원본 요소 제거
        todoElement.remove();

        // 보드 카운터 업데이트 및 빈 메시지 복원 체크
        if (parentTodoBoard) {
            this.updateBoardCounter();
            this.restoreEmptyMessage(parentTodoBoard);
        } else if (parentDoneBoard) {
            this.updateBoardCounter();
            this.restoreEmptyMessage(parentDoneBoard);
        }

        // 등장 애니메이션 효과
        clonedTodo.classList.add('entering');
        setTimeout(() => {
            clonedTodo.classList.remove('entering');
        }, 300);

        return backup;
    }

    /**
     * TODO를 보드로 이동
     * @param {string} todoId - 이동할 TODO ID
     * @param {string} createdAt - 원본 생성일 (ISO 형식)
     * @returns {Object} 백업 정보 (되돌리기용)
     */
    static moveTodoToBoard(todoId, createdAt) {
        const todoElement = document.querySelector(`[data-todo-id="${todoId}"]`);
        const todoBoard = document.getElementById('todo-board');

        if (!todoElement || !todoBoard) {
            return null;
        }

        // 백업 생성
        const backup = this.createBackup(todoElement);

        // 원본 요소 복제 및 드래그 상태 클래스 제거
        const clonedTodo = todoElement.cloneNode(true);
        clonedTodo.classList.remove('dragging'); // 드래그 상태 제거

        // 할당된 TODO를 미할당 TODO로 변환
        if (clonedTodo.classList.contains('assigned-todo')) {
            // 클래스 변경 (completed 상태 제거 - TODO 보드는 미완료만)
            clonedTodo.classList.remove('assigned-todo', 'completed');
            clonedTodo.classList.add('todo-card');
            if (!clonedTodo.classList.contains('draggable')) {
                clonedTodo.classList.add('draggable');
            }
            clonedTodo.setAttribute('draggable', 'true');

            // inline style 제거 (opacity 등)
            clonedTodo.style.opacity = '';
            clonedTodo.style.transition = '';

            // 텍스트 컨테이너 클래스 변경: .todo-text → .todo-content
            const textElement = clonedTodo.querySelector('.todo-text');
            if (textElement) {
                textElement.className = 'todo-content';
            }

            // 기존 체크박스와 액션 버튼들 제거
            const checkboxContainer = clonedTodo.querySelector('.checkbox-container');
            if (checkboxContainer) {
                checkboxContainer.remove();
            }

            const actionsDiv = clonedTodo.querySelector('.todo-actions');
            if (actionsDiv) {
                actionsDiv.remove();
            }

            // todo-card에 맞는 todo-meta div 생성
            const todoMeta = document.createElement('div');
            todoMeta.className = 'todo-meta';

            // 날짜 스팬 추가 (원본 생성일 사용)
            const todoDate = document.createElement('span');
            todoDate.className = 'todo-date';

            // createdAt을 "mm/dd" 형식으로 변환 (0 패딩)
            if (createdAt) {
                todoDate.textContent = this.formatDate(createdAt);
            } else {
                // fallback: createdAt이 없으면 현재 날짜 사용
                todoDate.textContent = this.formatDate(new Date());
            }

            // 삭제 버튼 추가 (template과 동일한 구조)
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'todo-delete-btn';
            deleteBtn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c0-1 1-2 2-2v2"/>
                </svg>
            `;

            todoMeta.appendChild(todoDate);
            todoMeta.appendChild(deleteBtn);
            clonedTodo.appendChild(todoMeta);
        } else if (clonedTodo.classList.contains('todo-card')) {
            // DONE 보드에서 온 todo-card인 경우
            clonedTodo.classList.remove('completed');

            // inline style 제거
            clonedTodo.style.opacity = '';
            clonedTodo.style.transition = '';

            // 완료 날짜를 생성일로 변경
            const todoDate = clonedTodo.querySelector('.todo-date');
            if (todoDate && createdAt) {
                todoDate.textContent = this.formatDate(createdAt);
            }
        }

        // data 속성 업데이트 (중요!)
        clonedTodo.dataset.isCompleted = 'false';
        clonedTodo.dataset.assigneeId = 'null';
        if (createdAt) {
            clonedTodo.dataset.createdAt = createdAt;
        }

        // 빈 메시지 제거 (TODO가 추가되므로)
        this.removeEmptyMessage(todoBoard);

        // 보드에 추가
        todoBoard.appendChild(clonedTodo);

        // 원본 요소 제거
        todoElement.remove();

        // 보드 카운터 업데이트 (보드에 추가되었으므로)
        this.updateBoardCounter();

        // 등장 애니메이션 효과
        clonedTodo.classList.add('entering');
        setTimeout(() => {
            clonedTodo.classList.remove('entering');
        }, 300);

        return backup;
    }

    /**
     * TODO 완료 상태 UI 토글
     * @param {string} todoId - 대상 TODO ID
     * @param {boolean} isCompleted - 완료 상태
     */
    static toggleTodoCompleteUI(todoId, isCompleted) {
        const todoElement = document.querySelector(`[data-todo-id="${todoId}"]`);
        const checkbox = todoElement?.querySelector('.complete-checkbox');

        if (!todoElement) {
            return;
        }

        // 체크박스가 있으면 상태 확실히 설정 (체크박스가 이미 변경되었을 수도 있으므로)
        if (checkbox) {
            checkbox.checked = isCompleted;
        }

        // data 속성 업데이트 (중요!)
        todoElement.dataset.isCompleted = isCompleted ? 'true' : 'false';

        // 시각적 완료 상태 반영 (부드러운 전환 효과)
        todoElement.style.transition = 'all 0.3s ease';

        if (isCompleted) {
            todoElement.classList.add('completed');
            // 완료된 항목은 약간 투명하게 표시
            todoElement.style.opacity = '0.6';
        } else {
            todoElement.classList.remove('completed');
            // 완료 해제된 항목은 원래 투명도로 복원
            todoElement.style.opacity = '1';
        }

    }

    /**
     * DOM에서 TODO 제거
     * @param {string} todoId - 제거할 TODO ID
     * @returns {Object} 백업 정보 (되돌리기용)
     */
    static removeTodoFromDOM(todoId) {
        const todoElement = document.querySelector(`[data-todo-id="${todoId}"]`);

        if (!todoElement) {
            return null;
        }

        // 백업 생성
        const backup = this.createBackup(todoElement);

        // 부드러운 제거 애니메이션
        todoElement.classList.add('leaving');

        setTimeout(() => {
            if (todoElement.parentNode) {
                const parentTodoBoard = todoElement.closest('#todo-board');
                const parentDoneBoard = todoElement.closest('#done-board');
                todoElement.remove();

                // 보드에서 제거된 경우 빈 메시지 복원 체크 및 카운터 업데이트
                if (parentTodoBoard) {
                    this.restoreEmptyMessage(parentTodoBoard);
                    this.updateBoardCounter();
                } else if (parentDoneBoard) {
                    this.restoreEmptyMessage(parentDoneBoard);
                    this.updateBoardCounter();
                }

            }
        }, 300);

        return backup;
    }

    /**
     * 멤버별 할당된 TODO 카운터 업데이트
     * @param {string} memberId - 멤버 ID
     */
    static updateMemberCounter(memberId) {
        const memberCard = document.querySelector(`[data-member-id="${memberId}"]`);

        if (!memberCard) {
            return;
        }

        const todosList = memberCard.querySelector('.todos-list');
        const counter = memberCard.querySelector('.assigned-count');

        if (todosList && counter) {
            const assignedTodos = todosList.querySelectorAll('.assigned-todo');
            const count = assignedTodos.length;

            // 카운터 업데이트 애니메이션 ("N개" 형태로 일관성 유지)
            counter.classList.add('updating');
            counter.textContent = `${count}개`;

            setTimeout(() => {
                counter.classList.remove('updating');
            }, 200);

        }
    }

    /**
     * 모든 멤버의 카운터 업데이트
     */
    static updateAllMemberCounters() {
        const memberCards = document.querySelectorAll('.member-card[data-member-id]');

        memberCards.forEach(memberCard => {
            const memberId = memberCard.dataset.memberId;
            if (memberId) {
                this.updateMemberCounter(memberId);
            }
        });
    }

    /**
     * TODO 이동 실패 시 되돌리기
     * @param {Object} backup - 백업 정보
     */
    static revertTodoMovement(backup) {
        if (!backup) {
            return;
        }

        const { element, parent, nextSibling } = backup;

        // 현재 DOM에서 해당 TODO 제거 (실패한 이동 결과)
        const currentElement = document.querySelector(`[data-todo-id="${element.dataset.todoId}"]`);
        if (currentElement) {
            currentElement.remove();
        }

        // 원래 위치로 복원
        if (nextSibling) {
            parent.insertBefore(element, nextSibling);
        } else {
            parent.appendChild(element);
        }

        // 복원 애니메이션
        element.style.opacity = '0.5';
        element.style.transition = 'opacity 0.3s ease';

        requestAnimationFrame(() => {
            element.style.opacity = '1';
        });

        // 보드로 복원된 경우 빈 메시지 제거 및 카운터 업데이트
        if (parent && parent.id === 'todo-board') {
            this.removeEmptyMessage(parent);
            this.updateBoardCounter();
        }
        // 보드에서 제거된 경우 빈 메시지 복원 체크
        else if (currentElement && currentElement.closest('#todo-board')) {
            const todoBoard = document.getElementById('todo-board');
            if (todoBoard) {
                this.restoreEmptyMessage(todoBoard);
                this.updateBoardCounter();
            }
        }

    }

    /**
     * 요소 백업 생성
     * @param {HTMLElement} element - 백업할 요소
     * @returns {Object} 백업 정보
     */
    static createBackup(element) {
        return {
            element: element.cloneNode(true),
            parent: element.parentNode,
            nextSibling: element.nextSibling
        };
    }

    /**
     * 로딩 상태 표시
     * @param {string} todoId - 로딩을 표시할 TODO ID
     * @param {boolean} isLoading - 로딩 상태
     */
    static setLoadingState(todoId, isLoading) {
        const todoElement = document.querySelector(`[data-todo-id="${todoId}"]`);

        if (!todoElement) {
            return;
        }

        if (isLoading) {
            todoElement.classList.add('loading');

            // 로딩 오버레이 추가
            const overlay = document.createElement('div');
            overlay.className = 'todo-loading-overlay';
            overlay.innerHTML = '<div class="loading-spinner"></div>';
            todoElement.appendChild(overlay);
        } else {
            todoElement.classList.remove('loading');

            // 로딩 오버레이 제거
            const overlay = todoElement.querySelector('.todo-loading-overlay');
            if (overlay) {
                overlay.remove();
            }
        }
    }

    /**
     * 에러 상태 표시
     * @param {string} todoId - 에러를 표시할 TODO ID
     * @param {string} message - 에러 메시지
     */
    static showError(todoId, message) {
        const todoElement = document.querySelector(`[data-todo-id="${todoId}"]`);

        if (!todoElement) {
            return;
        }

        // 에러 상태 클래스 추가
        todoElement.classList.add('error');

        // 에러 메시지 표시
        const errorDiv = document.createElement('div');
        errorDiv.className = 'todo-error-message';
        errorDiv.textContent = message;
        todoElement.appendChild(errorDiv);

        // Django 토스트로도 에러 메시지 표시
        if (window.showDjangoToast) {
            window.showDjangoToast(message, 'error');
        }

        // 3초 후 에러 상태 제거
        setTimeout(() => {
            todoElement.classList.remove('error');
            const errorMsg = todoElement.querySelector('.todo-error-message');
            if (errorMsg) {
                errorMsg.remove();
            }
        }, 3000);
    }

    /**
     * 성공 메시지 표시 (기존 Django 토스트 활용)
     * @param {string} message - 성공 메시지
     */
    static showSuccess(message) {
        if (window.showDjangoToast) {
            window.showDjangoToast(message, 'success');
        }
    }

    /**
     * 경고 메시지 표시 (기존 Django 토스트 활용)
     * @param {string} message - 경고 메시지
     */
    static showWarning(message) {
        if (window.showDjangoToast) {
            window.showDjangoToast(message, 'warning');
        }
    }

    /**
     * 정보 메시지 표시 (기존 Django 토스트 활용)
     * @param {string} message - 정보 메시지
     */
    static showInfo(message) {
        if (window.showDjangoToast) {
            window.showDjangoToast(message, 'info');
        }
    }

    /**
     * 보드의 빈 메시지 제거
     * @param {HTMLElement} todoBoard - 할 일 보드 요소
     */
    static removeEmptyMessage(todoBoard) {
        const emptyMessage = todoBoard.querySelector('.empty-todos');
        if (emptyMessage) {
            emptyMessage.remove();
        }
    }

    /**
     * 보드가 비어있을 때 빈 메시지 복원
     * @param {HTMLElement} todoBoard - 할 일 보드 요소
     */
    static restoreEmptyMessage(todoBoard) {
        const todos = todoBoard.querySelectorAll('.todo-card');
        if (todos.length === 0 && !todoBoard.querySelector('.empty-todos')) {
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'empty-todos';

            // 보드 종류에 따라 다른 메시지 표시
            if (todoBoard.id === 'done-board') {
                emptyDiv.innerHTML = '<p>완료된 할 일이 없습니다</p>';
            } else {
                emptyDiv.innerHTML = '<p>아직 할 일이 없습니다. 새로운 할 일을 추가해보세요!</p>';
            }

            todoBoard.appendChild(emptyDiv);
        }
    }

    /**
     * 보드의 TODO 카운터 업데이트
     */
    static updateBoardCounter() {
        // TODO 보드 카운터 업데이트
        const todoBoard = document.getElementById('todo-board');
        const todoBoardSection = todoBoard?.closest('.todo-board-section');
        const todoCounter = todoBoardSection?.querySelector('.todo-count');

        if (todoBoard && todoCounter) {
            const todoCards = todoBoard.querySelectorAll('.todo-card');
            const count = todoCards.length;

            // 카운터 업데이트 애니메이션
            todoCounter.classList.add('updating');
            todoCounter.textContent = `${count}개`;

            setTimeout(() => {
                todoCounter.classList.remove('updating');
            }, 200);
        }

        // DONE 보드 카운터 업데이트
        const doneBoard = document.getElementById('done-board');
        const doneBoardSection = doneBoard?.closest('.done-board-section');
        const doneCounter = doneBoardSection?.querySelector('.todo-count');

        if (doneBoard && doneCounter) {
            const doneCards = doneBoard.querySelectorAll('.todo-card');
            const count = doneCards.length;

            // 카운터 업데이트 애니메이션
            doneCounter.classList.add('updating');
            doneCounter.textContent = `${count}개`;

            setTimeout(() => {
                doneCounter.classList.remove('updating');
            }, 200);
        }
    }

    /**
     * TODO를 생성일 기준으로 정렬하여 보드에 삽입
     * @param {HTMLElement} board - 대상 보드
     * @param {HTMLElement} todoElement - 삽입할 TODO 요소
     * @param {string} createdAt - 생성일 (ISO 문자열)
     */
    static insertTodoInOrder(board, todoElement, createdAt) {
        if (!board || !todoElement) {
            return;
        }

        const existingTodos = Array.from(board.querySelectorAll('.todo-card, .assigned-todo'));

        // 빈 메시지 제거
        this.removeEmptyMessage(board);

        // 삽입 위치 찾기 (생성일 기준 오름차순)
        let insertIndex = existingTodos.length;
        for (let i = 0; i < existingTodos.length; i++) {
            const existingCreatedAt = existingTodos[i].dataset.createdAt;
            if (createdAt && existingCreatedAt && createdAt < existingCreatedAt) {
                insertIndex = i;
                break;
            }
        }

        // 삽입
        if (insertIndex >= existingTodos.length) {
            board.appendChild(todoElement);
        } else {
            board.insertBefore(todoElement, existingTodos[insertIndex]);
        }
    }

    /**
     * TODO를 Done 보드로 이동
     * @param {string} todoId - 이동할 TODO ID
     * @param {string} createdAt - 생성일 (정렬용)
     * @returns {Object} 백업 정보 (되돌리기용)
     */
    static moveTodoToDoneBoard(todoId, createdAt) {
        const todoElement = document.querySelector(`[data-todo-id="${todoId}"]`);
        const doneBoard = document.getElementById('done-board');

        if (!todoElement || !doneBoard) {
            return null;
        }

        // 백업 생성
        const backup = this.createBackup(todoElement);

        // 원본 요소 복제
        const clonedTodo = todoElement.cloneNode(true);
        clonedTodo.classList.remove('dragging');

        // Todo 카드로 변환 (assigned-todo → todo-card)
        if (clonedTodo.classList.contains('assigned-todo')) {
            // 클래스 변경 (completed 추가)
            clonedTodo.classList.remove('assigned-todo');
            clonedTodo.classList.add('todo-card', 'completed');
            if (!clonedTodo.classList.contains('draggable')) {
                clonedTodo.classList.add('draggable');
            }

            // inline style 제거 (opacity 등)
            clonedTodo.style.opacity = '';
            clonedTodo.style.transition = '';

            // todo-text를 todo-content로 변경
            const textElement = clonedTodo.querySelector('.todo-text');
            if (textElement) {
                textElement.className = 'todo-content';
            }

            // todo-actions를 todo-meta로 변경
            const actionsElement = clonedTodo.querySelector('.todo-actions');
            if (actionsElement) {
                actionsElement.remove();
            }

            // todo-meta 추가 (완료 날짜 포함)
            const todoMeta = document.createElement('div');
            todoMeta.className = 'todo-meta';

            const todoDate = document.createElement('span');
            todoDate.className = 'todo-date';
            todoDate.textContent = `완료: ${this.formatDate(new Date())}`;

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'todo-delete-btn';
            deleteBtn.dataset.todoId = todoId;
            deleteBtn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c0-1 1-2 2-2v2"/>
                </svg>
            `;

            todoMeta.appendChild(todoDate);
            todoMeta.appendChild(deleteBtn);
            clonedTodo.appendChild(todoMeta);
        } else {
            // 이미 todo-card면 completed 클래스 추가하고 날짜 업데이트
            clonedTodo.classList.add('completed');

            // inline style 제거
            clonedTodo.style.opacity = '';
            clonedTodo.style.transition = '';

            // 기존 todo-date를 완료 날짜로 업데이트
            const todoDate = clonedTodo.querySelector('.todo-date');
            if (todoDate) {
                todoDate.textContent = `완료: ${this.formatDate(new Date())}`;
            }
        }

        // data 속성 업데이트
        clonedTodo.dataset.isCompleted = 'true';
        clonedTodo.dataset.assigneeId = 'null';
        if (createdAt) {
            clonedTodo.dataset.createdAt = createdAt;
        }

        // 원본이 속한 멤버 카드 체크 (멤버 카운터 업데이트용)
        const parentMemberCard = todoElement.closest('.member-card');
        const memberId = parentMemberCard?.dataset.memberId;

        // Done 보드에 추가 (생성일 기준 정렬)
        this.insertTodoInOrder(doneBoard, clonedTodo, createdAt);

        // 원본 제거
        todoElement.remove();

        // 카운터 업데이트
        this.updateBoardCounter(); // TODO 보드와 DONE 보드
        if (memberId) {
            this.updateMemberCounter(memberId); // 멤버 카운터
        }

        // 등장 애니메이션 효과
        clonedTodo.classList.add('entering');
        setTimeout(() => {
            clonedTodo.classList.remove('entering');
        }, 300);

        return backup;
    }
}

// 전역 스코프에 노출
window.TodoDOMUtils = TodoDOMUtils;