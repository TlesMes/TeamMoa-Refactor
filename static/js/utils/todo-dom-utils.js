/**
 * TODO DOM 조작 유틸리티 클래스
 * Members App의 실시간 UI 업데이트를 위한 중앙화된 DOM 관리
 */
class TodoDOMUtils {
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
            // 클래스 순서를 정확히 맞추기 위해 className 전체 재설정
            clonedTodo.className = 'assigned-todo draggable';
            clonedTodo.setAttribute('draggable', 'true');

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
        }

        // 멤버 카드의 todos-list에 추가
        const todosList = memberCard.querySelector('.todos-list');
        if (todosList) {
            todosList.appendChild(clonedTodo);
        }

        // 보드에서 제거되는 경우 빈 메시지 복원 체크
        const parentBoard = todoElement.closest('#todo-board');

        // 원본 요소 제거
        todoElement.remove();

        // 보드 카운터 업데이트 및 빈 메시지 복원 체크
        if (parentBoard) {
            this.updateBoardCounter();
            this.restoreEmptyMessage(parentBoard);
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
     * @returns {Object} 백업 정보 (되돌리기용)
     */
    static moveTodoToBoard(todoId) {
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
            // 클래스 순서를 정확히 맞추기 위해 className 전체 재설정
            clonedTodo.className = 'todo-card draggable';
            clonedTodo.setAttribute('draggable', 'true');

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

            // 날짜 스팬 추가 (현재 날짜로)
            const todoDate = document.createElement('span');
            todoDate.className = 'todo-date';
            const now = new Date();
            todoDate.textContent = `${now.getMonth() + 1}/${now.getDate()}`;

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
                const parentBoard = todoElement.closest('#todo-board');
                todoElement.remove();

                // 보드에서 제거된 경우 빈 메시지 복원 체크 및 카운터 업데이트
                if (parentBoard) {
                    this.restoreEmptyMessage(parentBoard);
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
            emptyDiv.innerHTML = '<p>아직 할 일이 없습니다. 새로운 할 일을 추가해보세요!</p>';
            todoBoard.appendChild(emptyDiv);
        }
    }

    /**
     * 보드의 TODO 카운터 업데이트
     */
    static updateBoardCounter() {
        const todoBoard = document.getElementById('todo-board');
        const boardCounter = document.querySelector('.todo-count');

        if (todoBoard && boardCounter) {
            const todoCards = todoBoard.querySelectorAll('.todo-card');
            const count = todoCards.length;

            // 카운터 업데이트 애니메이션 ("N개" 형태로 일관성 유지)
            boardCounter.classList.add('updating');
            boardCounter.textContent = `${count}개`;

            setTimeout(() => {
                boardCounter.classList.remove('updating');
            }, 200);

        }
    }
}

// 전역 스코프에 노출
window.TodoDOMUtils = TodoDOMUtils;