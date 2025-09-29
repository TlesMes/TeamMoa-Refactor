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
     * TODO 이동 (상태/순서 변경)
     */
    async moveTodo(teamId, todoId, newStatus, newOrder = 0) {
        return this.api.post(`/teams/${teamId}/todos/${todoId}/move/`, {
            new_status: newStatus,
            new_order: newOrder
        });
    }

    /**
     * TODO 할당
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
     * TODO 보드로 되돌리기
     */
    async returnTodoToBoard(teamId, todoId) {
        return this.api.post(`/teams/${teamId}/todos/${todoId}/return_to_board/`, {});
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
 * 전역 API 클라이언트 인스턴스
 */
window.apiClient = new ApiClient();
window.todoApi = new TodoApiClient(window.apiClient);
window.teamMemberApi = new TeamMemberApiClient(window.apiClient);

// ApiError를 전역으로 export
window.ApiError = ApiError;

/**
 * API 응답을 토스트로 표시하는 헬퍼 함수
 */
window.handleApiResponse = function(response, successCallback = null) {
    // 성공 메시지가 있으면 Django 토스트로 표시
    if (response.message) {
        if (window.showDjangoToast) {
            showDjangoToast(response.message, 'success');
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
 * API 에러를 토스트로 표시하는 헬퍼 함수
 */
window.handleApiError = function(error, errorCallback = null) {
    console.error('API Error:', error);

    // 에러 메시지 Django 토스트로 표시
    if (error instanceof ApiError) {
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