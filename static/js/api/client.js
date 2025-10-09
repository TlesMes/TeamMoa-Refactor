// TeamMoa API 클라이언트
// 공통 API 호출 함수들과 에러 처리를 제공합니다.

class ApiClient {
    constructor() {
        this.baseURL = '/api/v1';
        this.csrfToken = this.getCSRFToken();
    }

    /**
     * CSRF 토큰 가져오기
     */
    getCSRFToken() {
        // 1. 폼의 hidden input에서 가져오기
        const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfElement && csrfElement.value) {
            return csrfElement.value;
        }

        // 2. 쿠키에서 가져오기 (fallback)
        const cookieToken = this.getCSRFTokenFromCookie();
        if (cookieToken) {
            return cookieToken;
        }

        return '';
    }

    /**
     * 쿠키에서 CSRF 토큰 가져오기
     */
    getCSRFTokenFromCookie() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return null;
    }

    /**
     * 기본 fetch 옵션 생성
     */
    getDefaultOptions(method = 'GET', data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken,
            },
            credentials: 'same-origin'
        };

        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            options.body = JSON.stringify(data);
        }

        return options;
    }

    /**
     * API 요청 실행
     */
    async request(url, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}${url}`, options);

            // 응답 데이터 파싱
            let data;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            if (!response.ok) {
                throw new ApiError(response.status, data, response.statusText);
            }

            return data;

        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }

            // 네트워크 오류 등
            throw new ApiError(0, {
                error: '네트워크 오류가 발생했습니다.'
            }, 'Network Error');
        }
    }

    /**
     * GET 요청
     */
    async get(url) {
        const options = this.getDefaultOptions('GET');
        return this.request(url, options);
    }

    /**
     * POST 요청
     */
    async post(url, data = null) {
        const options = this.getDefaultOptions('POST', data);
        return this.request(url, options);
    }

    /**
     * PUT 요청
     */
    async put(url, data = null) {
        const options = this.getDefaultOptions('PUT', data);
        return this.request(url, options);
    }

    /**
     * PATCH 요청
     */
    async patch(url, data = null) {
        const options = this.getDefaultOptions('PATCH', data);
        return this.request(url, options);
    }

    /**
     * DELETE 요청
     */
    async delete(url) {
        const options = this.getDefaultOptions('DELETE');
        return this.request(url, options);
    }
}

/**
 * API 에러 클래스
 */
class ApiError extends Error {
    constructor(status, data, statusText) {
        super();
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
        this.statusText = statusText;

        // 에러 메시지 설정
        if (typeof data === 'object' && data.error) {
            this.message = data.error;
        } else if (typeof data === 'string') {
            this.message = data;
        } else {
            this.message = statusText || '알 수 없는 오류가 발생했습니다.';
        }
    }
}

/**
 * TODO API 클라이언트
 */
class TodoApiClient {
    constructor(apiClient) {
        this.api = apiClient;
    }

    /**
     * 팀의 TODO 목록 조회
     */
    async getTodos(teamId) {
        return this.api.get(`/teams/${teamId}/todos/`);
    }

    /**
     * TODO 생성
     */
    async createTodo(teamId, content) {
        return this.api.post(`/teams/${teamId}/todos/`, {
            content: content
        });
    }

    /**
     * TODO를 TODO 보드로 이동
     */
    async moveTodoToTodoBoard(teamId, todoId) {
        return this.api.post(`/teams/${teamId}/todos/${todoId}/move-to-todo/`, {});
    }

    /**
     * TODO를 DONE 보드로 이동
     */
    async moveTodoToDoneBoard(teamId, todoId) {
        return this.api.post(`/teams/${teamId}/todos/${todoId}/move-to-done/`, {});
    }

    /**
     * TODO 할당 (Member 보드로 이동)
     */
    async assignTodo(teamId, todoId, memberId) {
        return this.api.post(`/teams/${teamId}/todos/${todoId}/assign/`, {
            member_id: memberId
        });
    }

    /**
     * TODO 완료 토글
     */
    async completeTodo(teamId, todoId) {
        return this.api.post(`/teams/${teamId}/todos/${todoId}/complete/`, {});
    }

    /**
     * TODO 삭제
     */
    async deleteTodo(teamId, todoId) {
        return this.api.delete(`/teams/${teamId}/todos/${todoId}/`);
    }
}

/**
 * 팀 멤버 API 클라이언트
 */
class TeamMemberApiClient {
    constructor(apiClient) {
        this.api = apiClient;
    }

    /**
     * 팀 멤버 목록 조회
     */
    async getMembers(teamId) {
        return this.api.get(`/teams/${teamId}/members/`);
    }
}

/**
 * 스케줄 API 클라이언트
 */
class ScheduleApiClient {
    constructor(apiClient) {
        this.api = apiClient;
    }

    /**
     * 개인 주간 스케줄 저장
     */
    async savePersonalSchedule(teamId, weekStart, scheduleData) {
        return this.api.post(`/teams/${teamId}/schedules/save-personal/`, {
            week_start: weekStart,
            schedule_data: scheduleData
        });
    }

    /**
     * 팀 가용성 조회
     */
    async getTeamAvailability(teamId, startDate, endDate) {
        return this.api.get(`/teams/${teamId}/schedules/team-availability/?start_date=${startDate}&end_date=${endDate}`);
    }

    /**
     * 내 스케줄 조회
     */
    async getMySchedule(teamId, startDate, endDate) {
        return this.api.get(`/teams/${teamId}/schedules/my-schedule/?start_date=${startDate}&end_date=${endDate}`);
    }
}

/**
 * 팀 API 클라이언트
 */
class TeamApiClient {
    constructor(apiClient) {
        this.api = apiClient;
    }

    /**
     * 팀 멤버 제거 (추방/탈퇴)
     */
    async removeMember(teamId, userId) {
        return this.api.delete(`/teams/${teamId}/members/${userId}/`);
    }
}

/**
 * 마인드맵 API 클라이언트
 */
class MindmapApiClient {
    constructor(apiClient) {
        this.api = apiClient;
    }

    /**
     * 팀의 마인드맵 목록 조회
     */
    async getMindmaps(teamId) {
        return this.api.get(`/teams/${teamId}/mindmaps/`);
    }

    /**
     * 마인드맵 상세 조회 (노드 및 연결선 포함)
     */
    async getMindmap(teamId, mindmapId) {
        return this.api.get(`/teams/${teamId}/mindmaps/${mindmapId}/`);
    }

    /**
     * 마인드맵 생성
     */
    async createMindmap(teamId, title) {
        return this.api.post(`/teams/${teamId}/mindmaps/`, {
            title: title
        });
    }

    /**
     * 마인드맵 삭제
     */
    async deleteMindmap(teamId, mindmapId) {
        return this.api.delete(`/teams/${teamId}/mindmaps/${mindmapId}/`);
    }

    /**
     * 노드 생성
     */
    async createNode(teamId, mindmapId, nodeData) {
        return this.api.post(`/teams/${teamId}/mindmaps/${mindmapId}/nodes/`, nodeData);
    }

    /**
     * 노드 위치 업데이트
     */
    async updateNodePosition(teamId, mindmapId, nodeId, posX, posY) {
        return this.api.patch(`/teams/${teamId}/mindmaps/${mindmapId}/nodes/${nodeId}/`, {
            posX: posX,
            posY: posY
        });
    }

    /**
     * 노드 삭제
     */
    async deleteNode(teamId, mindmapId, nodeId) {
        return this.api.delete(`/teams/${teamId}/mindmaps/${mindmapId}/nodes/${nodeId}/`);
    }

    /**
     * 노드 추천 토글
     */
    async toggleNodeRecommend(teamId, mindmapId, nodeId) {
        return this.api.post(`/teams/${teamId}/mindmaps/${mindmapId}/nodes/${nodeId}/recommend/`, {});
    }

    /**
     * 노드 댓글 조회
     */
    async getNodeComments(teamId, mindmapId, nodeId) {
        return this.api.get(`/teams/${teamId}/mindmaps/${mindmapId}/nodes/${nodeId}/comments/`);
    }

    /**
     * 노드 댓글 작성
     */
    async createNodeComment(teamId, mindmapId, nodeId, comment) {
        return this.api.post(`/teams/${teamId}/mindmaps/${mindmapId}/nodes/${nodeId}/comments/`, {
            comment: comment
        });
    }

    /**
     * 노드 연결 생성
     */
    async createConnection(teamId, mindmapId, fromNodeId, toNodeId) {
        return this.api.post(`/teams/${teamId}/mindmaps/${mindmapId}/connections/`, {
            from_node_id: fromNodeId,
            to_node_id: toNodeId
        });
    }

    /**
     * 노드 연결 삭제
     */
    async deleteConnection(teamId, mindmapId, connectionId) {
        return this.api.delete(`/teams/${teamId}/mindmaps/${mindmapId}/connections/${connectionId}/`);
    }
}

/**
 * 전역 API 클라이언트 인스턴스
 */
window.apiClient = new ApiClient();
window.todoApi = new TodoApiClient(window.apiClient);
window.teamApi = new TeamApiClient(window.apiClient);
window.teamMemberApi = new TeamMemberApiClient(window.apiClient);
window.scheduleApi = new ScheduleApiClient(window.apiClient);
window.mindmapApi = new MindmapApiClient(window.apiClient);

// ApiError를 전역으로 export
window.ApiError = ApiError;

/**
 * API 응답을 토스트로 표시하는 헬퍼 함수
 */
window.handleApiResponse = function(response, successCallback = null) {
    // Django messages 배열이 있으면 모두 표시
    if (response.messages && Array.isArray(response.messages)) {
        response.messages.forEach(msg => {
            if (window.showDjangoToast) {
                showDjangoToast(msg.message, msg.level);
            } else {
                showToast(msg.message);
            }
        });
    }
    // 하위 호환성: 단일 message 필드도 지원
    else if (response.message) {
        const level = response.success === false ? 'error' : 'success';
        if (window.showDjangoToast) {
            showDjangoToast(response.message, level);
        } else {
            showToast(response.message);
        }
    }

    // 성공 콜백 실행
    if (successCallback && typeof successCallback === 'function') {
        successCallback(response);
    }

    return response;
};

/**
 * API 에러를 콘솔과 토스트로 표시하는 헬퍼 함수
 */
window.handleApiError = function(error, errorCallback = null) {
    // 콘솔에 상세 에러 정보 출력
    console.group('🔴 API Error Details');
    console.error('Error Object:', error);

    if (error instanceof ApiError) {
        console.error('Status:', error.status);
        console.error('Message:', error.message);
        console.error('Data:', error.data);
        console.error('URL:', error.url);
    } else {
        console.error('Non-API Error:', error.message || error);
        console.error('Stack:', error.stack);
    }
    console.groupEnd();

    // HTML 에러 페이지인 경우 (Django 디버그 페이지) 전체 페이지로 표시
    if (error instanceof ApiError && typeof error.data === 'string' && error.data.includes('<!DOCTYPE html>')) {
        document.open();
        document.write(error.data);
        document.close();
        return error;
    }

    // 에러 응답에서 Django messages 처리
    if (error instanceof ApiError && error.data && error.data.messages) {
        error.data.messages.forEach(msg => {
            if (window.showDjangoToast) {
                showDjangoToast(msg.message, msg.level || 'error');
            } else {
                showToast(msg.message, 'error');
            }
        });
    }
    // 일반 에러 메시지 표시
    else if (error instanceof ApiError) {
        if (window.showDjangoToast) {
            showDjangoToast(error.message, 'error');
        } else {
            showToast(error.message, 'error');
        }
    } else {
        if (window.showDjangoToast) {
            showDjangoToast('오류가 발생했습니다. 다시 시도해주세요.', 'error');
        } else {
            showToast('오류가 발생했습니다. 다시 시도해주세요.', 'error');
        }
    }

    // 에러 콜백 실행
    if (errorCallback && typeof errorCallback === 'function') {
        errorCallback(error);
    }

    return error;
};