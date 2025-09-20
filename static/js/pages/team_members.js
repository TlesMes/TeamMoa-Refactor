// 팀 멤버 관리 페이지 전용 JavaScript

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

    // Drag start - for both unassigned and assigned todos
    todoCards.forEach(card => {
        card.addEventListener('dragstart', function(e) {
            // 권한 체크 - 드래그할 수 없는 경우 막기
            if (!canMoveTodo(this)) {
                e.preventDefault();
                return;
            }

            draggedTodo = this;
            this.classList.add('dragging');

            // Add visual feedback based on source and permissions
            if (this.classList.contains('todo-card')) {
                // From todo board - highlight only allowed member drop zones
                memberCards.forEach(member => {
                    const memberId = member.dataset.memberId;
                    if (canAssignToMember(memberId)) {
                        member.classList.add('drop-zone-active');
                    }
                });
            } else if (this.classList.contains('assigned-todo')) {
                // From assigned todos - highlight allowed destinations only

                // 할 일 보드로 되돌리기는 본인 할일이거나 팀장만 가능
                const currentMemberCard = this.closest('.member-card');
                const currentMemberId = currentMemberCard ? currentMemberCard.dataset.memberId : null;

                if (isHost || (currentMemberId && memberPermissions[currentMemberId] && memberPermissions[currentMemberId].isCurrentUser)) {
                    todoBoard.classList.add('drop-zone-active');
                }

                // 다른 멤버에게 재할당 - 권한에 따라
                memberCards.forEach(member => {
                    // 현재 멤버 카드는 제외
                    if (member !== currentMemberCard) {
                        const memberId = member.dataset.memberId;
                        if (canAssignToMember(memberId)) {
                            member.classList.add('drop-zone-active');
                        }
                    }
                });
            }
        });

        card.addEventListener('dragend', function(e) {
            this.classList.remove('dragging');
            draggedTodo = null;

            // Remove all visual feedback
            memberCards.forEach(member => {
                member.classList.remove('drop-zone-active');
            });
            todosLists.forEach(list => {
                list.classList.remove('drop-zone-active');
            });
            todoBoard.classList.remove('drop-zone-active');
        });
    });

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
                    console.log('Permission denied - cannot assign to this member');
                    return;
                }

                // Check if dropping on the same member (avoid unnecessary Ajax)
                const currentMemberCard = draggedTodo.closest('.member-card');
                if (currentMemberCard && currentMemberCard === this) {
                    console.log('Same member drop - no action needed');
                    return; // Don't send Ajax request
                }

                assignTodoToMember(todoId, memberId);
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
                console.log('Already on todo board - no action needed');
                return; // Don't send Ajax request
            }

            // Only process assigned todos being returned to board
            if (draggedTodo.classList.contains('assigned-todo')) {
                // 권한 체크
                const currentMemberCard = draggedTodo.closest('.member-card');
                const currentMemberId = currentMemberCard ? currentMemberCard.dataset.memberId : null;

                if (!isHost && !(currentMemberId && memberPermissions[currentMemberId] && memberPermissions[currentMemberId].isCurrentUser)) {
                    console.log('Permission denied - cannot return this todo to board');
                    return;
                }

                const todoId = draggedTodo.dataset.todoId;
                returnTodoToBoard(todoId);
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

    // API Functions
    function assignTodoToMember(todoId, memberId) {
        fetch(`/members/api/${teamId}/assign-todo/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                todo_id: todoId,
                member_id: memberId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Always reload to show Django messages
            window.location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            // Reload to show error messages from Django
            window.location.reload();
        });
    }

    function toggleTodoComplete(todoId) {
        fetch(`/members/api/${teamId}/complete-todo/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                todo_id: todoId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Always reload to show Django messages
            window.location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            // Reload to show error messages from Django
            window.location.reload();
        });
    }

    // Return todo to board function (used by both drag&drop and button)
    function returnTodoToBoard(todoId) {
        fetch(`/members/api/${teamId}/return-to-board/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                todo_id: todoId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Always reload to show Django messages
            window.location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            // Reload to show error messages from Django
            window.location.reload();
        });
    }

    function deleteTodo(todoId) {
        if (confirm('이 할 일을 삭제하시겠습니까?')) {
            // Use existing delete endpoint
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/members/member_delete_Todo/${teamId}/${todoId}`;

            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrfToken;

            form.appendChild(csrfInput);
            document.body.appendChild(form);
            form.submit();
        }
    }
});