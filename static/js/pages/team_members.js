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
        const isDoneBoard = card.closest('#done-board');
        const isTodoBoard = card.closest('#todo-board');

        if (card.classList.contains('todo-card')) {
            // From todo board or done board
            if (isTodoBoard) {
                // TODO 보드에서 시작 - 멤버와 DONE 보드 하이라이트
                memberCards.forEach(member => {
                    const memberId = member.dataset.memberId;
                    if (canAssignToMember(memberId)) {
                        member.classList.add('drop-zone-active');
                    }
                });

                const doneBoard = document.getElementById('done-board');
                if (doneBoard) {
                    doneBoard.classList.add('drop-zone-active');
                }
            } else if (isDoneBoard) {
                // DONE 보드에서 시작 - 멤버와 TODO 보드 하이라이트 (DONE 제외)
                memberCards.forEach(member => {
                    const memberId = member.dataset.memberId;
                    if (canAssignToMember(memberId)) {
                        member.classList.add('drop-zone-active');
                    }
                });

                todoBoard.classList.add('drop-zone-active');
            }
        } else if (card.classList.contains('assigned-todo')) {
            // From assigned todos - highlight allowed destinations only
            const currentMemberCard = card.closest('.member-card');
            const currentMemberId = currentMemberCard ? currentMemberCard.dataset.memberId : null;

            // TODO 보드 하이라이트 (권한 있는 경우)
            if (isHost || (currentMemberId && memberPermissions[currentMemberId] && memberPermissions[currentMemberId].isCurrentUser)) {
                todoBoard.classList.add('drop-zone-active');
            }

            // 다른 멤버에게 재할당 - 권한에 따라 (현재 멤버 제외)
            memberCards.forEach(member => {
                if (member !== currentMemberCard) {
                    const memberId = member.dataset.memberId;
                    if (canAssignToMember(memberId)) {
                        member.classList.add('drop-zone-active');
                    }
                }
            });

            // DONE 보드도 하이라이트
            const doneBoardDrop = document.getElementById('done-board');
            if (doneBoardDrop) {
                doneBoardDrop.classList.add('drop-zone-active');
            }
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

    // Drop zone - Todo Board (for returning assigned todos and done todos)
    todoBoard.addEventListener('dragover', function(e) {
        if (!draggedTodo) return;

        // TODO 보드에서 시작한 경우 - 드롭 불가
        const isTodoBoard = draggedTodo.closest('#todo-board');
        if (isTodoBoard) {
            return;
        }

        // assigned-todo (멤버에서 온 것) - 권한 체크
        if (draggedTodo.classList.contains('assigned-todo')) {
            const currentMemberCard = draggedTodo.closest('.member-card');
            const currentMemberId = currentMemberCard ? currentMemberCard.dataset.memberId : null;

            if (isHost || (currentMemberId && memberPermissions[currentMemberId] && memberPermissions[currentMemberId].isCurrentUser)) {
                e.preventDefault();
            }
        }
        // DONE 보드에서 온 todo-card - 항상 허용
        else if (draggedTodo.classList.contains('todo-card') && draggedTodo.closest('#done-board')) {
            e.preventDefault();
        }
    });

    todoBoard.addEventListener('drop', function(e) {
        e.preventDefault();

        if (draggedTodo) {
            const todoId = draggedTodo.dataset.todoId;
            const isDoneBoard = draggedTodo.closest('#done-board');
            const isTodoBoard = draggedTodo.closest('#todo-board');

            // DONE 보드에서 온 TODO
            if (isDoneBoard) {
                draggedTodo.classList.remove('dragging');
                draggedTodo.dataset.isCompleted = 'false'; // TODO 보드는 미완료
                returnTodoToBoard(todoId);
                clearAllHighlighting();
                return;
            }

            // TODO 보드 내부 이동은 무시
            if (isTodoBoard && draggedTodo.classList.contains('todo-card')) {
                return;
            }

            // 멤버에서 온 assigned-todo
            if (draggedTodo.classList.contains('assigned-todo')) {
                // 권한 체크
                const currentMemberCard = draggedTodo.closest('.member-card');
                const currentMemberId = currentMemberCard ? currentMemberCard.dataset.memberId : null;

                if (!isHost && !(currentMemberId && memberPermissions[currentMemberId] && memberPermissions[currentMemberId].isCurrentUser)) {
                    return;
                }

                // 드래그 상태 즉시 정리
                draggedTodo.classList.remove('dragging');

                // TODO 보드에 드롭 → is_completed를 false로 강제 설정
                draggedTodo.dataset.isCompleted = 'false';

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
            member.classList.remove('drop-zone-active');
        });

        // 할일 리스트 하이라이팅 제거
        todosLists.forEach(list => {
            list.classList.remove('drop-zone-active');
        });

        // TODO 보드 하이라이팅 제거
        todoBoard.classList.remove('drop-zone-active');

        // DONE 보드 하이라이팅 제거
        const doneBoard = document.getElementById('done-board');
        if (doneBoard) {
            doneBoard.classList.remove('drop-zone-active');
        }
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

            // 마일스톤 정보가 포함된 토스트 메시지
            if (response.success && response.data) {
                const data = response.data;

                if (data.milestone_updated && data.milestone_id) {
                    // 마일스톤 진행률 업데이트된 경우
                    const milestone = window.teamMembersData.milestones.find(m => m.id === data.milestone_id);
                    if (milestone && data.milestone_progress !== undefined) {
                        const message = newCompletedState
                            ? `TODO 완료! "${milestone.title}" 마일스톤 진행률 ${data.milestone_progress}%`
                            : `TODO 미완료 처리. "${milestone.title}" 마일스톤 진행률 ${data.milestone_progress}%`;
                        showDjangoToast(message, 'success');
                    } else {
                        handleApiResponse(response);
                    }
                } else {
                    // 마일스톤 없는 경우 기본 메시지
                    handleApiResponse(response);
                }
            } else {
                handleApiResponse(response);
            }

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

        // is_completed 상태 확인
        const isCompleted = todoElement?.dataset.isCompleted === 'true';

        // 원본 생성일 가져오기 (data-created-at 속성에서)
        const createdAt = todoElement?.dataset.createdAt;

        // 1. 즉시 DOM 업데이트 (Optimistic UI)
        let backup;
        if (isCompleted) {
            // Done Board로 이동
            backup = TodoDOMUtils.moveTodoToDoneBoard(todoId, createdAt);
        } else {
            // Todo Board로 이동
            backup = TodoDOMUtils.moveTodoToBoard(todoId, createdAt);
        }
        TodoDOMUtils.setLoadingState(todoId, true);

        try {
            // 2. API 호출 - is_completed에 따라 다른 엔드포인트 호출
            let response;
            if (isCompleted) {
                response = await todoApi.moveTodoToDoneBoard(teamId, todoId);
            } else {
                response = await todoApi.moveTodoToTodoBoard(teamId, todoId);
            }
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

    // ==================== DONE BOARD 기능 ====================

    // DONE 보드를 드롭존으로 추가
    const doneBoard = document.getElementById('done-board');

    if (doneBoard) {
        doneBoard.addEventListener('dragover', function(e) {
            if (!draggedTodo) return;

            // DONE 보드에서 시작한 경우 - 드롭 불가
            const isDoneBoard = draggedTodo.closest('#done-board');
            if (isDoneBoard) {
                return;
            }

            e.preventDefault();
            doneBoard.classList.add('drop-zone-active');
        });

        doneBoard.addEventListener('dragleave', function(e) {
            if (e.target === doneBoard) {
                doneBoard.classList.remove('drop-zone-active');
            }
        });

        doneBoard.addEventListener('drop', async function(e) {
            e.preventDefault();

            if (draggedTodo) {
                handleDoneBoardDrop(draggedTodo);
            }

            // 드롭 완료 후 모든 하이라이팅 제거
            clearAllHighlighting();
        });
    }

    // Done 보드 드롭 처리 함수
    function handleDoneBoardDrop(draggedElement) {
        const todoId = draggedElement.dataset.todoId;
        const createdAt = draggedElement.dataset.createdAt;

        // 권한 체크
        if (!canMoveTodo(draggedElement)) {
            showDjangoToast('권한이 없습니다', 'error');
            draggedElement.classList.remove('dragging');
            draggedTodo = null;
            return;
        }

        // 드래그 상태 정리
        draggedElement.classList.remove('dragging');
        draggedTodo = null;

        // Done Board로 이동 (moveTodoToDoneBoard에서 데이터 속성 업데이트)
        moveTodoToDoneBoard(todoId, createdAt);
    }

    // Done Board로 TODO 이동
    async function moveTodoToDoneBoard(todoId, createdAt) {
        const todoElement = document.querySelector(`[data-todo-id="${todoId}"]`);
        const memberCard = todoElement?.closest('.member-card');
        const memberId = memberCard?.dataset.memberId;

        // 1. 즉시 DOM 업데이트 (Optimistic UI)
        const backup = TodoDOMUtils.moveTodoToDoneBoard(todoId, createdAt);
        TodoDOMUtils.setLoadingState(todoId, true);

        try {
            // 2. API 호출
            const response = await todoApi.moveTodoToDoneBoard(teamId, todoId);
            handleApiResponse(response);

            // 3. 성공 시 로딩 상태 해제 (카운터는 이미 DOM 유틸에서 업데이트됨)
            TodoDOMUtils.setLoadingState(todoId, false);
        } catch (error) {
            // 4. 실패 시 되돌리기
            TodoDOMUtils.revertTodoMovement(backup);
            TodoDOMUtils.setLoadingState(todoId, false);
            TodoDOMUtils.showError(todoId, 'DONE 보드로 이동에 실패했습니다');

            handleApiError(error);
        }
    }

    // ==================== 마일스톤 할당 기능 ====================

    // 마일스톤 드롭다운 이벤트 위임
    membersSection.addEventListener('change', async function(e) {
        if (e.target.classList.contains('milestone-select')) {
            const todoId = parseInt(e.target.dataset.todoId);
            const milestoneId = e.target.value ? parseInt(e.target.value) : null;

            try {
                // API 호출
                const response = await todoApi.assignToMilestone(teamId, todoId, milestoneId);

                if (response.success) {
                    // TODO 카드 업데이트
                    updateTodoMilestoneBadge(todoId, milestoneId);

                    // 토스트 메시지
                    const milestone = window.teamMembersData.milestones.find(m => m.id === milestoneId);
                    if (milestoneId) {
                        showDjangoToast(`TODO가 "${milestone.title}" 마일스톤에 할당되었습니다.`, 'success');
                    } else {
                        showDjangoToast('TODO 마일스톤 연결이 해제되었습니다.', 'info');
                    }
                } else {
                    showDjangoToast(response.message || '마일스톤 할당에 실패했습니다.', 'error');
                }
            } catch (error) {
                handleApiError(error);
                // 실패 시 드롭다운 되돌리기
                const todoCard = document.querySelector(`[data-todo-id="${todoId}"]`);
                const currentMilestoneId = todoCard?.dataset.milestoneId;
                e.target.value = currentMilestoneId !== 'null' ? currentMilestoneId : '';
            }
        }
    });

    // TODO 카드의 마일스톤 배지 업데이트 함수
    function updateTodoMilestoneBadge(todoId, milestoneId) {
        const todoCard = document.querySelector(`[data-todo-id="${todoId}"]`);
        if (!todoCard) return;

        // data-milestone-id 업데이트
        todoCard.dataset.milestoneId = milestoneId || 'null';

        // 드롭다운 업데이트 (TODO 보드에만 존재)
        const milestoneSelect = todoCard.querySelector('.milestone-select');
        if (milestoneSelect) {
            milestoneSelect.value = milestoneId || '';
        }

        // 기존 배지 제거
        const existingBadge = todoCard.querySelector('.todo-milestone-badge');
        if (existingBadge) {
            existingBadge.remove();
        }

        // 새 배지 추가 (milestoneId가 있는 경우)
        if (milestoneId) {
            const milestone = window.teamMembersData.milestones.find(m => m.id === milestoneId);
            if (milestone) {
                const badge = document.createElement('div');
                badge.className = `todo-milestone-badge priority-${milestone.priority}`;
                badge.innerHTML = `
                    <i class="ri-flag-line"></i>
                    <span>${milestone.title}</span>
                `;

                // todo-content 다음에 배지 삽입
                const todoContent = todoCard.querySelector('.todo-content, .todo-text');
                if (todoContent) {
                    todoContent.insertAdjacentElement('afterend', badge);
                }
            }
        }
    }

});