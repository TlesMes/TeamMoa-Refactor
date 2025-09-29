// 팀 멤버 관리 페이지 전용 JavaScript

// TodoDOMUtils 스크립트 로드 확인
if (typeof TodoDOMUtils === 'undefined') {
    console.error('TodoDOMUtils가 로드되지 않았습니다. todo-dom-utils.js를 확인하세요.');
}

document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    let draggedTodo = null;

    // Django 데이터를 전역으로 설정 (템플릿에서 설정)
    const currentUserId = window.teamMembersData.currentUserId;
    const isHost = window.teamMembersData.isHost;
    const memberPermissions = window.teamMembersData.memberPermissions;
    const teamId = window.teamMembersData.teamId;

    // 권한 체크 함수들
    function canAssignToMember(memberId) {
        // 팀장은 모든 멤버에게 할당 가능
        if (isHost) return true;

        // 일반 멤버는 자신에게만 할당 가능
        return memberPermissions[memberId] && memberPermissions[memberId].isCurrentUser;
    }

    function canMoveTodo(todoElement) {
        // 팀장은 모든 할일 조작 가능
        if (isHost) return true;

        // 미할당 할일은 누구나 자신에게 할당 가능
        if (todoElement.classList.contains('todo-card')) return true;

        // 할당된 할일은 본인 것만 조작 가능
        if (todoElement.classList.contains('assigned-todo')) {
            const memberCard = todoElement.closest('.member-card');
            if (memberCard) {
                const memberId = memberCard.dataset.memberId;
                return memberPermissions[memberId] && memberPermissions[memberId].isCurrentUser;
            }
        }

        return false;
    }

    // Drag & Drop for Todo Cards
    const todoCards = document.querySelectorAll('.draggable');
    const memberCards = document.querySelectorAll('.member-card.drop-zone');
    const todoBoard = document.getElementById('todo-board');
    const todosLists = document.querySelectorAll('.todos-list');

    // 초기 권한 기반 시각적 피드백 설정
    todoCards.forEach(card => {
        if (!canMoveTodo(card)) {
            card.classList.add('no-drag-permission');
            card.setAttribute('draggable', 'false');
        }
    });

    // members 섹션 내에서만 이벤트 위임 - 성능과 범위 최적화
    const membersSection = document.querySelector('.members-section');
    if (membersSection) {
        membersSection.addEventListener('dragstart', function(e) {
            const card = e.target.closest('.draggable');
            if (!card) return;
        // 권한 체크 - 드래그할 수 없는 경우 막기
        if (!canMoveTodo(card)) {
            e.preventDefault();
            return;
        }

        draggedTodo = card;
        card.classList.add('dragging');

        // Add visual feedback based on source and permissions
        if (card.classList.contains('todo-card')) {
                // From todo board - highlight only allowed member drop zones
                memberCards.forEach(member => {
                    const memberId = member.dataset.memberId;
                    if (canAssignToMember(memberId)) {
                        member.classList.add('drag-over');
                    }
                });
        } else if (card.classList.contains('assigned-todo')) {
                // From assigned todos - highlight allowed destinations only

            // 할 일 보드로 되돌리기는 본인 할일이거나 팀장만 가능
            const currentMemberCard = card.closest('.member-card');
            const currentMemberId = currentMemberCard ? currentMemberCard.dataset.memberId : null;

            if (isHost || (currentMemberId && memberPermissions[currentMemberId] && memberPermissions[currentMemberId].isCurrentUser)) {
                todoBoard.classList.add('drag-over');
            }

            // 다른 멤버에게 재할당 - 권한에 따라
            memberCards.forEach(member => {
                // 현재 멤버 카드는 제외
                if (member !== currentMemberCard) {
                    const memberId = member.dataset.memberId;
                    if (canAssignToMember(memberId)) {
                        member.classList.add('drag-over');
                    }
                }
            });
        }
    });

        // members 섹션 내에서만 드래그 종료 처리
        membersSection.addEventListener('dragend', function(e) {
            const card = e.target.closest('.draggable');
            if (!card) return;

            card.classList.remove('dragging');
            draggedTodo = null;

            // 모든 하이라이팅 제거
            clearAllHighlighting();
        });
    }

    // Drop zones - Member cards
    memberCards.forEach(member => {
        member.addEventListener('dragover', function(e) {
            // 권한이 있는 드롭 존만 허용
            const memberId = this.dataset.memberId;
            if (draggedTodo && canAssignToMember(memberId)) {
                e.preventDefault();
            }
        });

        member.addEventListener('drop', function(e) {
            e.preventDefault();

            if (draggedTodo) {
                const todoId = draggedTodo.dataset.todoId;
                const memberId = this.dataset.memberId;

                // 권한 체크
                if (!canAssignToMember(memberId)) {
                    return;
                }

                // Check if dropping on the same member (avoid unnecessary Ajax)
                const currentMemberCard = draggedTodo.closest('.member-card');
                if (currentMemberCard && currentMemberCard === this) {
                    return; // Don't send Ajax request
                }

                // 드래그 상태 즉시 정리
                if (draggedTodo) {
                    draggedTodo.classList.remove('dragging');
                }

                // 드래그앤드롭도 동일한 DOM 조작 + API 호출
                assignTodoToMember(todoId, memberId);

                // 드롭 완료 후 모든 하이라이팅 제거
                clearAllHighlighting();
            }
        });
    });

    // Drop zone - Todo Board (for returning assigned todos)
    todoBoard.addEventListener('dragover', function(e) {
        // 권한이 있는 경우만 드롭 허용
        if (draggedTodo && draggedTodo.classList.contains('assigned-todo')) {
            const currentMemberCard = draggedTodo.closest('.member-card');
            const currentMemberId = currentMemberCard ? currentMemberCard.dataset.memberId : null;

            if (isHost || (currentMemberId && memberPermissions[currentMemberId] && memberPermissions[currentMemberId].isCurrentUser)) {
                e.preventDefault();
            }
        }
    });

    todoBoard.addEventListener('drop', function(e) {
        e.preventDefault();

        if (draggedTodo) {
            // Check if already on todo board (avoid unnecessary Ajax)
            if (draggedTodo.classList.contains('todo-card')) {
                return; // Don't send Ajax request
            }

            // Only process assigned todos being returned to board
            if (draggedTodo.classList.contains('assigned-todo')) {
                // 권한 체크
                const currentMemberCard = draggedTodo.closest('.member-card');
                const currentMemberId = currentMemberCard ? currentMemberCard.dataset.memberId : null;

                if (!isHost && !(currentMemberId && memberPermissions[currentMemberId] && memberPermissions[currentMemberId].isCurrentUser)) {
                    return;
                }

                const todoId = draggedTodo.dataset.todoId;

                // 드래그 상태 즉시 정리
                if (draggedTodo) {
                    draggedTodo.classList.remove('dragging');
                }

                // 드래그앤드롭도 동일한 DOM 조작 + API 호출
                returnTodoToBoard(todoId);

                // 드롭 완료 후 모든 하이라이팅 제거
                clearAllHighlighting();
            }
        }
    });

    // Complete Todo Checkboxes
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('complete-checkbox')) {
            const todoId = e.target.dataset.todoId;
            toggleTodoComplete(todoId);
        }
    });

    // 삭제 버튼 이벤트 리스너
    document.addEventListener('click', function(e) {
        if (e.target.closest('.todo-delete-btn')) {
            e.preventDefault();
            const todoCard = e.target.closest('.todo-card');
            if (todoCard) {
                const todoId = todoCard.dataset.todoId;
                deleteTodo(todoId);
            }
        }

        if (e.target.closest('.delete-btn')) {
            e.preventDefault();
            const assignedTodo = e.target.closest('.assigned-todo');
            if (assignedTodo) {
                const todoId = assignedTodo.dataset.todoId;
                deleteTodo(todoId);
            }
        }

        if (e.target.closest('.return-btn')) {
            e.preventDefault();
            const assignedTodo = e.target.closest('.assigned-todo');
            if (assignedTodo) {
                const todoId = assignedTodo.dataset.todoId;
                returnTodoToBoard(todoId);
            }
        }
    });

    // 모든 드래그 관련 하이라이팅 제거
    function clearAllHighlighting() {
        // 멤버 카드 하이라이팅 제거
        memberCards.forEach(member => {
            member.classList.remove('drag-over');
        });

        // 할일 리스트 하이라이팅 제거
        todosLists.forEach(list => {
            list.classList.remove('drag-over');
        });

        // 보드 하이라이팅 제거
        todoBoard.classList.remove('drag-over');

    }

    // API Functions
    async function assignTodoToMember(todoId, memberId) {

        // 1. 즉시 DOM 업데이트 (Optimistic UI) - 실패하면 페이지 리로드로 처리
        const backup = TodoDOMUtils.moveTodoToMember(todoId, memberId);
        if (backup) {
            TodoDOMUtils.setLoadingState(todoId, true);
        }

        try {
            // 2. API 호출
            const response = await todoApi.assignTodo(teamId, todoId, memberId);
            handleApiResponse(response);

            // 3. 성공 시 처리
            if (backup) {
                // DOM 조작이 성공했으면 카운터 업데이트
                TodoDOMUtils.updateMemberCounter(memberId);
                TodoDOMUtils.setLoadingState(todoId, false);
            } else {
                // DOM 조작이 실패했으면 페이지 리로드
                setTimeout(() => location.reload(), 1000); // 토스트 메시지를 본 후 리로드
            }
        } catch (error) {
            // 4. 실패 시 처리
            if (backup) {
                // DOM 조작이 성공했었으면 되돌리기
                TodoDOMUtils.revertTodoMovement(backup);
                TodoDOMUtils.setLoadingState(todoId, false);
                TodoDOMUtils.showError(todoId, '할 일 할당에 실패했습니다');
            } else {
                // DOM 조작이 실패했으면 에러만 표시 (페이지 상태는 그대로)
                if (window.showDjangoToast) {
                    window.showDjangoToast('할 일 할당에 실패했습니다', 'error');
                }
            }

            handleApiError(error);
        }
    }

    async function toggleTodoComplete(todoId) {
        const todoElement = document.querySelector(`[data-todo-id="${todoId}"]`);
        const checkbox = todoElement?.querySelector('.complete-checkbox');

        if (!checkbox) {
            return;
        }

        // 체크박스가 이미 클릭되어 변경된 상태를 사용
        const newCompletedState = checkbox.checked;

        // 1. 즉시 UI 업데이트 (Optimistic UI)
        TodoDOMUtils.toggleTodoCompleteUI(todoId, newCompletedState);
        TodoDOMUtils.setLoadingState(todoId, true);

        try {
            // 2. API 호출
            const response = await todoApi.completeTodo(teamId, todoId);
            handleApiResponse(response);
            TodoDOMUtils.setLoadingState(todoId, false);
        } catch (error) {
            // 3. 실패 시 되돌리기
            TodoDOMUtils.toggleTodoCompleteUI(todoId, !newCompletedState);
            TodoDOMUtils.setLoadingState(todoId, false);
            TodoDOMUtils.showError(todoId, '완료 상태 변경에 실패했습니다');

            handleApiError(error);
        }
    }

    // Return todo to board function (used by both drag&drop and button)
    async function returnTodoToBoard(todoId) {
        const todoElement = document.querySelector(`[data-todo-id="${todoId}"]`);
        const memberCard = todoElement?.closest('.member-card');
        const memberId = memberCard?.dataset.memberId;

        // 1. 즉시 DOM 업데이트 (Optimistic UI)
        const backup = TodoDOMUtils.moveTodoToBoard(todoId);
        TodoDOMUtils.setLoadingState(todoId, true);

        try {
            // 2. API 호출
            const response = await todoApi.returnTodoToBoard(teamId, todoId);
            handleApiResponse(response);

            // 3. 성공 시 카운터 업데이트 (서버에서 이미 메시지 제공)
            if (memberId) {
                TodoDOMUtils.updateMemberCounter(memberId);
            }
            TodoDOMUtils.setLoadingState(todoId, false);
        } catch (error) {
            // 4. 실패 시 되돌리기
            TodoDOMUtils.revertTodoMovement(backup);
            TodoDOMUtils.setLoadingState(todoId, false);
            TodoDOMUtils.showError(todoId, '보드 복귀에 실패했습니다');

            handleApiError(error);
        }
    }

    async function deleteTodo(todoId) {
        showConfirmModal('이 할 일을 삭제하시겠습니까?', async function() {
            const todoElement = document.querySelector(`[data-todo-id="${todoId}"]`);
            const memberCard = todoElement?.closest('.member-card');
            const memberId = memberCard?.dataset.memberId;

            // 1. 즉시 DOM에서 제거 (Optimistic UI)
            const backup = TodoDOMUtils.removeTodoFromDOM(todoId);

            try {
                // 2. API 호출
                const response = await todoApi.deleteTodo(teamId, todoId);
                handleApiResponse(response);

                // 3. 성공 시 카운터 업데이트 (서버에서 이미 메시지 제공)
                if (memberId) {
                    TodoDOMUtils.updateMemberCounter(memberId);
                }
            } catch (error) {
                // 4. 실패 시 복원
                TodoDOMUtils.revertTodoMovement(backup);
                TodoDOMUtils.showError(todoId, '할 일 삭제에 실패했습니다');

                handleApiError(error);
            }
        });
    }

});