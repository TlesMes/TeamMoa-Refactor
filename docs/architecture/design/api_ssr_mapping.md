# TeamMoa 기능별 상세 API/SSR 매핑

**작성일**: 2025.10.17
**목적**: 각 기능의 URL 패턴, 뷰 이름, HTTP 메서드, 사용 방식을 상세하게 문서화

---

## 📑 목차
1. [Accounts App (인증 시스템)](#1-accounts-app)
2. [Teams App (팀 관리)](#2-teams-app)
3. [Members App (멤버 관리)](#3-members-app)
4. [Schedules App (스케줄 관리)](#4-schedules-app)
5. [Mindmaps App (마인드맵)](#5-mindmaps-app)
6. [Shares App (게시판)](#6-shares-app)

---

## 1. Accounts App

### 사용 방식: **SSR 중심** (django-allauth 혼합)

### 1.1 커스텀 인증 뷰 (SSR)

| 기능 | URL 패턴 | 뷰 클래스/함수 | HTTP 메서드 | 템플릿 | 설명 |
|------|----------|----------------|-------------|--------|------|
| **홈/랜딩** | `/accounts/` | `home` | GET | `accounts/home.html` | 미로그인: 랜딩, 로그인: 팀 목록 리다이렉트 |
| **회원가입** | `/accounts/signup/` | `SignupView` | GET, POST | `accounts/signup.html` | 커스텀 회원가입 폼 |
| **회원가입 성공** | `/accounts/signup/success/` | `SignupSuccessView` | GET | `accounts/signup_success.html` | 이메일 인증 안내 페이지 |
| **이메일 인증** | `/accounts/activate/<uid64>/<token>` | `ActivateView` | GET | (redirect) | 이메일 링크 클릭 시 계정 활성화 |
| **인증 재발송** | `/accounts/resend-activation/` | `resend_activation_email` | POST | (JSON) | AJAX 방식 인증 이메일 재발송 |
| **로그인** | `/accounts/login/` | `LoginView` | GET, POST | `accounts/login.html` | 커스텀 로그인 폼 |
| **로그아웃** | `/accounts/logout/` | `LogoutView` | GET | (redirect) | 세션 종료 후 랜딩으로 리다이렉트 |
| **프로필 수정** | `/accounts/update/` | `UpdateView` | GET, POST | `accounts/update.html` | 사용자 정보 수정 |
| **비밀번호 변경** | `/accounts/password/` | `PasswordChangeView` | GET, POST | `accounts/password.html` | 로그인된 사용자 비밀번호 변경 |
| **소셜 계정 관리** | `/accounts/social-connections/` | `social_connections` | GET | `accounts/social_connections.html` | 연결된 소셜 계정 목록/해제 |

**서비스 레이어**: `accounts/services.py` - `AuthService`
- `register_user()`: 회원가입 + 이메일 발송
- `activate_account()`: 토큰 검증 + 계정 활성화
- `resend_activation()`: 인증 이메일 재발송

---

### 1.2 django-allauth 뷰 (SSR)

**URL 프리픽스**: `/accounts/` (프로젝트 `urls.py`에서 `include('allauth.urls')`)

#### 소셜 로그인 (OAuth 2.0)

| 기능 | URL 패턴 | 뷰 | HTTP 메서드 | 설명 |
|------|----------|-----|-------------|------|
| **Google 로그인** | `/accounts/google/login/` | `allauth.socialaccount` | GET | Google OAuth 리다이렉트 |
| **Google 콜백** | `/accounts/google/login/callback/` | `allauth.socialaccount` | GET | OAuth 인증 후 콜백 처리 |
| **GitHub 로그인** | `/accounts/github/login/` | `allauth.socialaccount` | GET | GitHub OAuth 리다이렉트 |
| **GitHub 콜백** | `/accounts/github/login/callback/` | `allauth.socialaccount` | GET | OAuth 인증 후 콜백 처리 |
| **소셜 계정 연결** | `/accounts/social/connections/` | `ConnectionsView` | GET, POST | 소셜 계정 추가/제거 |

**커스텀 어댑터**: `accounts/adapters.py`
- `CustomSocialAccountAdapter`: 이메일 기반 자동 계정 연결, 프로필 매핑
- `CustomAccountAdapter`: 메시지 시스템 한글화

---

### 1.3 이메일 인증 재발송 (AJAX 지원)

| 기능 | URL 패턴 | 뷰 클래스 | HTTP 메서드 | 응답 형식 | 설명 |
|------|----------|----------|-------------|-----------|------|
| **이메일 인증 재발송** | `/accounts/resend-activation/` | `ResendActivationEmailView` | POST | JSON (AJAX) / Redirect (일반) | AJAX 요청 시 JSON 응답, 일반 요청 시 리다이렉트 |

**사용 위치**: `accounts/templates/accounts/signup_success.html` (Form 제출)

**특징**:
- **AJAX 감지**: `X-Requested-With` 헤더로 AJAX 여부 판단
- **JSON 응답**: `{status: 'success/warning/error', message: '...'}`
- **일반 요청**: 세션에 메시지 저장 후 `signup_success` 페이지로 리다이렉트

**서비스 레이어**: `AuthService.resend_activation_email()` - 재발송 제한, 이메일 검증

---

### 1.4 allauth 이메일 관리 (SSR)

| 기능 | URL 패턴 | 뷰 | HTTP 메서드 | 설명 |
|------|----------|-----|-------------|------|
| **이메일 관리** | `/accounts/email/` | `EmailView` | GET, POST | 이메일 추가/제거/주 이메일 설정 |
| **이메일 인증 확인** | `/accounts/confirm-email/<key>/` | `ConfirmEmailView` | GET | allauth 이메일 인증 (소셜 로그인용) |

---

## 2. Teams App

### 사용 방식: **하이브리드** (SSR + API)

### 2.1 팀 관리 (SSR)

| 기능 | URL 패턴 | 뷰 함수 | HTTP 메서드 | 템플릿 | 설명 |
|------|----------|---------|-------------|--------|------|
| **메인 페이지** | `/teams/` | `main_page` | GET | `teams/main_authenticated.html` (로그인) <br> `teams/main_landing.html` (비로그인) | 사용자별 팀 목록 표시 |
| **팀 생성** | `/teams/team_create/` | `team_create` | GET, POST | `teams/team_create.html` | Form 기반 팀 생성 |
| **팀 검색** | `/teams/team_search/` | `team_search` | GET | `teams/team_search.html` | 팀 이름 검색 + 페이지네이션 |
| **팀 정보 수정** | `/teams/team_info_change/<int:pk>/` | `team_info_change` | GET, POST | `teams/team_info_change.html` | Form 기반 팀 정보 수정 (팀장 전용) |
| **팀 홈** | `/teams/team_main_page/<int:pk>/` | `team_main_page` | GET | `teams/team_main_page.html` | 팀 대시보드 (멤버 목록, 마일스톤 요약) |
| **팀 해체** | `/teams/team_disband/<int:pk>/` | `team_disband` | POST | (redirect) | 팀 삭제 (팀장 전용) |

**서비스 레이어**: `teams/services.py` - `TeamService`
- `create_team()`: 팀 생성 + 팀장 자동 등록
- `update_team()`: 팀 정보 수정
- `delete_team()`: 팀 삭제 + 관련 데이터 정리

---

### 2.2 팀 가입 (AJAX 엔드포인트)

| 기능 | URL 패턴 | 뷰 클래스 | HTTP 메서드 | 응답 형식 | 사용 위치 |
|------|----------|----------|-------------|-----------|----------|
| **팀 코드 검증** | `/teams/ajax/team-verify/` | `TeamVerifyCodeView` | POST | JSON | `team_search.html` (Step 1) |
| **팀 가입 처리** | `/teams/ajax/team-join/` | `TeamJoinProcessView` | POST | JSON | `team_search.html` (Step 2) |

**JavaScript**: `teams/templates/teams/team_search.html` (인라인 `fetch()` 코드)

**사용 이유**:
- SSR 페이지 내에서 AJAX로 처리 (페이지 새로고침 방지)
- 보안 강화 (URL에 팀 ID 노출 방지)
- 단계별 가입 프로세스 (코드 검증 → 비밀번호 입력 → 완료)

**서비스 레이어**: `TeamService.verify_team_code()`, `TeamService.join_team()`

---

### 2.3 팀 탈퇴/추방 (REST API)

| 기능 | API 엔드포인트 | HTTP 메서드 | ViewSet 액션 | JavaScript 함수 | 설명 |
|------|----------------|-------------|--------------|------------------|------|
| **멤버 제거** | `/api/v1/teams/<pk>/members/<user_id>/` | DELETE | `TeamViewSet.remove_member` | `teamApi.removeMember()` | 팀장: 추방 / 본인: 탈퇴 |

**JavaScript**: `static/js/pages/team_main.js`, `static/js/api/client.js`

**주요 기능**:
- **권한 분기**: 팀장은 모든 멤버 추방 가능, 일반 멤버는 본인만 탈퇴 가능
- **UI 분기**: 탈퇴 시 팀 목록으로 리다이렉트, 추방 시 페이지 갱신
- 확인 모달 표시 (`showConfirmModal()`)

**서비스 레이어**: `TeamService.remove_member()` - 권한 검증, 팀장 탈퇴 방지

---

### 2.4 마일스톤 타임라인 (하이브리드)

#### SSR (초기 로드)

| 기능 | URL 패턴 | 뷰 함수 | HTTP 메서드 | 템플릿 | 설명 |
|------|----------|---------|-------------|--------|------|
| **마일스톤 타임라인** | `/teams/team_milestone_timeline/<int:pk>/` | `team_milestone_timeline` | GET | `teams/team_milestone_timeline.html` | 연간 타임라인 뷰 (초기 마일스톤 데이터 포함) |

#### API (실시간 CRUD)

| 기능 | API 엔드포인트 | HTTP 메서드 | ViewSet | JavaScript 함수 | 설명 |
|------|----------------|-------------|---------|------------------|------|
| **마일스톤 목록 조회** | `/api/v1/teams/<team_pk>/milestones/` | GET | `MilestoneViewSet.list` | N/A | 초기 로드 시 서버 렌더링 |
| **마일스톤 생성** | `/api/v1/teams/<team_pk>/milestones/` | POST | `MilestoneViewSet.create` | `teamApi.createMilestone()` | 모달에서 생성 |
| **마일스톤 조회** | `/api/v1/teams/<team_pk>/milestones/<pk>/` | GET | `MilestoneViewSet.retrieve` | N/A | 미사용 |
| **마일스톤 수정** | `/api/v1/teams/<team_pk>/milestones/<pk>/` | PUT, PATCH | `MilestoneViewSet.update` | `teamApi.updateMilestone()` | 드래그 앤 드롭 날짜 변경 |
| **마일스톤 삭제** | `/api/v1/teams/<team_pk>/milestones/<pk>/` | DELETE | `MilestoneViewSet.destroy` | `teamApi.deleteMilestone()` | 삭제 버튼 클릭 |

**JavaScript**: `static/js/pages/milestone_timeline.js`

**주요 기능**:
- 드래그 앤 드롭으로 시작일/종료일 변경
- 좌/우 핸들로 기간 조정
- 필터링 (상태별, 우선순위별)
- 모달 기반 생성/삭제

**서비스 레이어**: `teams/services.py` - `MilestoneService`
- `create_milestone()`: 마일스톤 생성
- `update_milestone()`: 마일스톤 수정
- `delete_milestone()`: 마일스톤 삭제

---

## 3. Members App

### 사용 방식: **하이브리드** (SSR + API)

### 3.1 멤버 페이지 (SSR - 초기 로드 + TODO 생성)

| 기능 | URL 패턴 | 뷰 함수 | HTTP 메서드 | 템플릿 | 설명 |
|------|----------|---------|-------------|--------|------|
| **팀 멤버 페이지** | `/members/team_members_page/<int:pk>/` | `team_members_page` | GET | `members/team_members_page.html` | 멤버 목록 + TODO 보드 초기 렌더링 |
| **TODO 생성 (Form)** | `/members/team_members_page/<int:pk>/` | `team_members_page` | POST | (리다이렉트) | Django Form으로 TODO 생성 후 페이지 새로고침 |

**서버 렌더링 데이터**:
- 팀 멤버 목록 (권한 포함)
- TODO 보드 (미할당, 멤버별 할당, 완료)
- 현재 사용자 권한 정보
- TODO 생성 폼 (CreateTodoForm)

**TODO 생성 방식**:
- **SSR Form 사용** (API 미사용)
- 이유: 단일 필드 입력, Django Messages 활용, 코드 간결성
- `<form method="POST">` → `TeamMembersPageView.post()` → 리다이렉트

---

### 3.2 TODO 기본 CRUD (REST API)

| 기능 | API 엔드포인트 | HTTP 메서드 | ViewSet | JavaScript 함수 | 설명 |
|------|----------------|-------------|---------|------------------|------|
| ~~**TODO 목록 조회**~~ | `/api/v1/teams/<team_pk>/todos/` | GET | `TodoViewSet.list` | N/A | **미사용** (초기 로드는 SSR) |
| ~~**TODO 생성**~~ | `/api/v1/teams/<team_pk>/todos/` | POST | `TodoViewSet.create` | N/A | **미사용** (SSR Form 사용) |
| ~~**TODO 조회**~~ | `/api/v1/teams/<team_pk>/todos/<pk>/` | GET | `TodoViewSet.retrieve` | N/A | **미사용** |
| ~~**TODO 수정**~~ | `/api/v1/teams/<team_pk>/todos/<pk>/` | PUT, PATCH | `TodoViewSet.update` | N/A | **미사용** |
| **TODO 삭제** | `/api/v1/teams/<team_pk>/todos/<pk>/` | DELETE | `TodoViewSet.destroy` | `todoApi.deleteTodo()` | ✅ **사용 중** (삭제 버튼) |

**참고**: ModelViewSet 기본 액션(list, create, retrieve, update)은 구현되어 있지만 실제로는 사용하지 않음

---

### 3.3 TODO 상태 관리 (API - 커스텀 액션)

| 기능 | API 엔드포인트 | HTTP 메서드 | ViewSet 액션 | JavaScript 함수 | 설명 |
|------|----------------|-------------|--------------|------------------|------|
| **TODO 할당** | `/api/v1/teams/<team_pk>/todos/<pk>/assign/` | POST | `TodoViewSet.assign` | `todoApi.assignTodo()` | 멤버에게 TODO 드래그 앤 드롭 |
| **TODO 완료 토글** | `/api/v1/teams/<team_pk>/todos/<pk>/complete/` | POST | `TodoViewSet.complete` | `todoApi.completeTodo()` | 체크박스 클릭 |
| **TODO 보드로 이동** | `/api/v1/teams/<team_pk>/todos/<pk>/move-to-todo/` | POST | `TodoViewSet.move_to_todo` | `todoApi.moveTodoToTodoBoard()` | DONE → TODO 보드 |
| **DONE 보드로 이동** | `/api/v1/teams/<team_pk>/todos/<pk>/move-to-done/` | POST | `TodoViewSet.move_to_done` | `todoApi.moveTodoToDoneBoard()` | TODO/멤버 → DONE 보드 |

**JavaScript**: `static/js/pages/team_members.js`, `static/js/utils/todo-dom-utils.js`

**주요 기능**:
- 드래그 앤 드롭 (TODO 보드 ↔ 멤버 ↔ DONE 보드)
- Optimistic UI 업데이트 (즉시 DOM 조작 후 API 호출)
- 권한 기반 드래그 제한 (팀장: 모든 TODO, 일반: 자신 것만)
- 실시간 멤버별 TODO 카운터 업데이트

**서비스 레이어**: `members/services.py` - `TodoService`
- `assign_todo()`: TODO 할당
- `complete_todo()`: 완료 상태 토글
- `move_todo_to_board()`: 보드 간 이동
- `delete_todo()`: TODO 삭제

---

### 3.4 레거시 뷰 정리 완료 ✅

#### SSR 뷰 - **삭제 완료**

| 기능 | URL 패턴 | 뷰 클래스 | 대체 REST API | 삭제일 |
|------|----------|----------|---------------|--------|
| ✅ **TODO 완료 (SSR)** | `/members/member_complete_Todo/<pk>/<todo_id>` | `MemberCompleteTodoView` | `/api/v1/teams/<team_pk>/todos/<pk>/complete/` | 2025.10.19 |
| ✅ **TODO 삭제 (SSR)** | `/members/member_delete_Todo/<pk>/<todo_id>` | `MemberDeleteTodoView` | `/api/v1/teams/<team_pk>/todos/<pk>/` (DELETE) | 2025.10.19 |

#### AJAX 엔드포인트 - **삭제 완료**

| 기능 | URL 패턴 | 뷰 클래스 | 대체 REST API | 삭제일 |
|------|----------|----------|---------------|--------|
| ✅ **TODO 이동** | `/members/api/<pk>/move-todo/` | `MoveTodoView` | `/api/v1/teams/<team_pk>/todos/<pk>/move-to-todo/` | 2025.10.18 |
| ✅ **TODO 할당** | `/members/api/<pk>/assign-todo/` | `AssignTodoView` | `/api/v1/teams/<team_pk>/todos/<pk>/assign/` | 2025.10.18 |
| ✅ **TODO 완료** | `/members/api/<pk>/complete-todo/` | `CompleteTodoView` | `/api/v1/teams/<team_pk>/todos/<pk>/complete/` | 2025.10.18 |
| ✅ **TODO 복귀** | `/members/api/<pk>/return-to-board/` | `ReturnToBoardView` | `/api/v1/teams/<team_pk>/todos/<pk>/move-to-done/` | 2025.10.18 |

**참고**: Members App 레거시 코드 완전 정리 완료 (총 6개 뷰 삭제)

---

## 4. Schedules App

### 사용 방식: **하이브리드** (SSR + API)

### 4.1 스케줄 페이지 (SSR - 초기 로드)

| 기능 | URL 패턴 | 뷰 함수 | HTTP 메서드 | 템플릿 | 설명 |
|------|----------|---------|-------------|--------|------|
| **팀 스케줄 조회** | `/schedules/scheduler_page/<int:pk>/` | `scheduler_page` | GET | `schedules/scheduler_page.html` | 주간 팀 가용성 표시 (7일×24시간) |
| **개인 스케줄 업로드** | `/schedules/scheduler_upload_page/<int:pk>/` | `scheduler_upload_page` | GET | `schedules/scheduler_upload_page.html` | 개인 스케줄 입력 폼 (7일×24시간) |

**서버 렌더링 데이터**:
- 현재 주차 팀 가용성 (초기값)
- 내 개인 스케줄 (업로드 페이지)

---

### 4.2 스케줄 API (실시간 조회/저장)

| 기능 | API 엔드포인트 | HTTP 메서드 | ViewSet 액션 | JavaScript 함수 | 설명 |
|------|----------------|-------------|--------------|------------------|------|
| **개인 스케줄 저장** | `/api/v1/teams/<team_pk>/schedules/save-personal/` | POST | `ScheduleViewSet.save_personal_schedule` | `scheduleApi.savePersonalSchedule()` | JSON 기반 스케줄 저장 |
| **팀 가용성 조회** | `/api/v1/teams/<team_pk>/schedules/team-availability/` | GET | `ScheduleViewSet.get_team_availability` | `fetch()` (직접 호출) | 주차 변경 시 실시간 조회 |
| **내 스케줄 조회** | `/api/v1/teams/<team_pk>/schedules/my-schedule/` | GET | `ScheduleViewSet.get_my_schedule` | N/A | 미사용 (서버 렌더링으로 대체) |

**JavaScript**:
- `static/js/pages/scheduler_upload.js`: 드래그 앤 드롭 선택 + 저장
- `static/js/pages/scheduler_page.js`: 주차 선택 시 실시간 팀 가용성 조회

**주요 기능**:
- **scheduler_upload.js**:
  - 드래그 앤 드롭으로 시간대 선택
  - 빠른 선택 도구 (업무시간, 저녁시간, 평일/주말)
  - JSON 형식으로 스케줄 저장 (`{time_9-1: true, ...}`)

- **scheduler_page.js**:
  - `<input type="week">` 변경 시 자동 API 호출
  - 팀 가용성 테이블 동적 업데이트 (0~N명)
  - ISO week 형식(YYYY-Www) → 날짜 범위 변환

**서비스 레이어**: `schedules/services.py` - `ScheduleService`
- `save_personal_schedule()`: 개인 스케줄 저장 (JSON)
- `get_team_availability()`: 팀원 스케줄 집계
- `get_my_schedule()`: 개인 스케줄 조회

---

## 5. Mindmaps App

### 사용 방식: **하이브리드** (SSR + API + WebSocket)

### 5.1 마인드맵 관리 (SSR)

| 기능 | URL 패턴 | 뷰 함수 | HTTP 메서드 | 템플릿 | 설명 |
|------|----------|---------|-------------|--------|------|
| **마인드맵 목록** | `/mindmaps/mindmap_list_page/<int:pk>` | `mindmap_list_page` | GET | `mindmaps/mindmap_list_page.html` | 팀 마인드맵 목록 표시 |
| **마인드맵 생성** | `/mindmaps/mindmap_create/<int:pk>` | `mindmap_create` | POST | (redirect) | Form 기반 마인드맵 생성 |
| **마인드맵 삭제** | `/mindmaps/mindmap_delete/<int:pk>/<int:mindmap_id>` | `mindmap_delete` | POST | (redirect) | 마인드맵 삭제 (권한 체크) |
| **권한 부여** | `/mindmaps/mindmap_empower/<int:pk>/<int:mindmap_id>/<int:user_id>` | `mindmap_empower` | POST | (redirect) | 편집 권한 추가/제거 |

---

### 5.2 마인드맵 에디터 (하이브리드)

#### SSR (초기 로드)

| 기능 | URL 패턴 | 뷰 함수 | HTTP 메서드 | 템플릿 | 설명 |
|------|----------|---------|-------------|--------|------|
| **마인드맵 에디터** | `/mindmaps/mindmap_detail_page/<int:pk>/<int:mindmap_id>` | `mindmap_detail_page` | GET | `mindmaps/mindmap_detail_page.html` | Canvas 에디터 (초기 노드/연결선 데이터 포함) |

**서버 렌더링 데이터**:
- 마인드맵 메타 정보
- 모든 노드 목록 (위치, 제목, 내용)
- 모든 연결선 목록

---

#### API (실시간 CRUD)

##### 노드 관리

| 기능 | API 엔드포인트 | HTTP 메서드 | ViewSet | JavaScript 함수 | 설명 |
|------|----------------|-------------|---------|------------------|------|
| **노드 생성** | `/api/v1/teams/<team_pk>/mindmaps/<mindmap_pk>/nodes/` | POST | `NodeViewSet.create` | `createNodeAt()` | 더블클릭 시 모달에서 생성 |
| **노드 위치 수정** | `/api/v1/teams/<team_pk>/mindmaps/<mindmap_pk>/nodes/<pk>/` | PATCH | `NodeViewSet.partial_update` | `onMouseUp()` (드래그 종료 시) | 드래그 앤 드롭 위치 변경 |
| **노드 삭제** | `/api/v1/teams/<team_pk>/mindmaps/<mindmap_pk>/nodes/<pk>/` | DELETE | `NodeViewSet.destroy` | (노드 상세 페이지) | 노드 상세 페이지에서 삭제 |

##### 연결선 관리

| 기능 | API 엔드포인트 | HTTP 메서드 | ViewSet | JavaScript 함수 | 설명 |
|------|----------------|-------------|---------|------------------|------|
| **연결선 생성** | `/api/v1/teams/<team_pk>/mindmaps/<mindmap_pk>/connections/` | POST | `NodeConnectionViewSet.create` | `createConnection()` | Ctrl+클릭 후 노드 연결 |
| **연결선 삭제** | `/api/v1/teams/<team_pk>/mindmaps/<mindmap_pk>/connections/<pk>/` | DELETE | `NodeConnectionViewSet.destroy` | `deleteConnection()` | 연결선 선택 후 Delete 키 |

**JavaScript**: `static/js/pages/mindmap_detail.js`

**주요 기능**:
- Canvas 기반 마인드맵 에디터 (가상 캔버스 5400×3600px)
- 드래그 앤 드롭 노드 이동
- 줌/팬 (마우스 휠, 버튼)
- 더블클릭 노드 생성
- Ctrl+클릭 연결선 생성
- Delete 키 연결선 삭제
- 둥근 모서리, 그라데이션, 드롭 섀도우 렌더링

---

#### WebSocket (실시간 협업)

**WebSocket URL**: `ws://host/ws/mindmap/<team_id>/<mindmap_id>/`

| 이벤트 타입 | 송신 → 수신 | 데이터 | 설명 |
|-------------|-------------|--------|------|
| `node_move` | Client → Server | `{node_id, x, y}` | 노드 위치 변경 시 브로드캐스트 |
| `node_moved` | Server → Client | `{node_id, x, y}` | 다른 사용자의 노드 이동 반영 |
| `cursor_move` | Client → Server | `{x, y}` | 커서 위치 전송 (스로틀링 50ms) |
| `cursor_moved` | Server → Client | `{user_id, username, x, y}` | 다른 사용자 커서 표시 |
| `connection_create` | Client → Server | `{from_node_id, to_node_id}` | 연결선 생성 브로드캐스트 |
| `connection_created` | Server → Client | `{connection_id, from_node_id, to_node_id}` | 연결선 추가 반영 |
| `connection_delete` | Client → Server | `{connection_id}` | 연결선 삭제 브로드캐스트 |
| `connection_deleted` | Server → Client | `{connection_id}` | 연결선 제거 반영 |
| `user_joined` | Server → Client | `{user_id, username}` | 새 사용자 접속 알림 |
| `user_left` | Server → Client | `{user_id, username}` | 사용자 퇴장 알림 |

**주요 기능**:
- 실시간 다중 사용자 커서 표시
- 노드 위치 실시간 동기화
- 연결선 생성/삭제 실시간 반영

---

### 5.3 노드 상세 페이지 (하이브리드)

#### SSR (초기 로드)

| 기능 | URL 패턴 | 뷰 함수 | HTTP 메서드 | 템플릿 | 설명 |
|------|----------|---------|-------------|--------|------|
| **노드 상세** | `/mindmaps/node_detail_page/<int:pk>/<int:node_id>` | `node_detail_page` | GET | `mindmaps/node_detail_page.html` | 노드 제목, 내용, 댓글 표시 |
| **노드 삭제** | `/mindmaps/mindmap_delete_node/<int:pk>/<int:node_id>` | `mindmap_delete_node` | POST | (redirect) | Form 제출 방식 노드 삭제 |

**서버 렌더링 데이터**:
- 노드 상세 정보
- 댓글 목록
- 추천 수

**특징**:
- 노드 삭제는 노드 상세 페이지에서만 가능 (마인드맵 에디터에서는 삭제 불가)
- 삭제 버튼 클릭 시 확인 모달 후 Form 제출

---

#### API (추천 기능)

| 기능 | API 엔드포인트 | HTTP 메서드 | ViewSet 액션 | JavaScript 함수 | 설명 |
|------|----------------|-------------|--------------|------------------|------|
| **노드 추천** | `/api/v1/teams/<team_pk>/mindmaps/<mindmap_pk>/nodes/<pk>/recommend/` | POST | `NodeViewSet.recommend` | `mindmapApi.toggleNodeRecommend()` | 추천 토글 (추천↔취소) |

**JavaScript**: `static/js/pages/node_detail.js`

---

### 5.4 미사용 뷰 (레거시) - **✅ 삭제 완료**

| 기능 | URL 패턴 | 뷰 함수 | 이유 | 상태 |
|------|----------|---------|------|------|
| ✅ **노드 생성 (SSR)** | `/mindmaps/mindmap_create_node/<pk>/<mindmap_id>` | `mindmap_create_node` | API로 대체 (`POST /api/.../nodes/`) | **삭제됨** |
| ✅ **노드 투표 (SSR)** | `/mindmaps/node_vote/<pk>/<node_id>` | `node_vote` | API로 대체 (`POST /api/.../nodes/<pk>/recommend/`) | **삭제됨** |
| ✅ **노드 추천 (SSR)** | `/mindmaps/node_recommend/<pk>/<node_id>` | `node_recommend` | 하위 호환성 유지용, 실제 사용 안 함 | **삭제됨** |

**참고**: Mindmaps 미사용 뷰 3개는 2025.10.18에 삭제 완료

---

### 5.5 서비스 레이어

**서비스 레이어**: `mindmaps/services.py` - `MindmapService`, `NodeService`, `NodeConnectionService`

**주요 메서드**:
- `MindmapService.create_mindmap()`: 마인드맵 생성
- `NodeService.create_node()`: 노드 생성
- `NodeService.update_node_position()`: 노드 위치 업데이트
- `NodeService.toggle_recommendation()`: 추천 토글
- `NodeConnectionService.create_connection()`: 연결선 생성
- `NodeConnectionService.delete_connection()`: 연결선 삭제

---

## 6. Shares App

### 사용 방식: **SSR 중심** (Form 기반 CRUD)

### 6.1 게시판 기능 (SSR)

| 기능 | URL 패턴 | 뷰 클래스/함수 | HTTP 메서드 | 템플릿 | 설명 |
|------|----------|----------------|-------------|--------|------|
| **게시판 목록** | `/shares/<int:pk>/` | `PostListView` (CBV) | GET | `shares/post_list.html` | 게시물 목록 + 검색 + 페이지네이션 |
| **게시물 상세** | `/shares/<int:pk>/detail/<int:post_id>` | `post_detail_view` | GET | `shares/post_detail.html` | 게시물 상세 + 댓글 |
| **게시물 작성** | `/shares/<int:pk>/write/` | `post_write_view` | GET, POST | `shares/post_write_renew.html` | Form 기반 작성 (파일 업로드) |
| **게시물 수정** | `/shares/<int:pk>/edit/<int:post_id>` | `post_edit_view` | GET, POST | `shares/post_write_renew.html` | Form 기반 수정 (파일 업로드) |
| **게시물 삭제** | `/shares/<int:pk>/delete/<int:post_id>` | `post_delete_view` | POST | (redirect) | 게시물 삭제 |
| **파일 다운로드** | `/shares/<int:pk>/download/<int:post_id>` | `post_download_view` | GET | (file response) | 첨부파일 다운로드 |

---

### 6.2 주요 기능

#### 검색 (QuerySet 기반)
- 제목, 내용, 작성자로 검색
- `PostListView.get_queryset()`에서 `Q` 객체 사용
- URL 파라미터: `?search=검색어`

#### 페이지네이션
- 페이지당 10개 게시물
- `PostListView.paginate_by = 10`
- Django `Paginator` 사용

#### 파일 업로드/다운로드
- 드래그 앤 드롭 UI (`static/js/pages/file_upload.js`)
- Summernote 에디터 (이미지 임베드)
- 파일 다운로드 시 권한 체크 (팀 멤버만)

---

### 6.3 JavaScript

**파일**: `static/js/pages/file_upload.js`, `static/js/pages/post_write.js`

**주요 기능**:
- 드래그 앤 드롭 파일 업로드 UI
- Summernote 에디터 초기화
- 파일 크기 제한 (10MB)

---

### 6.4 서비스 레이어

**서비스 레이어**: `shares/services.py` - `PostService`

**주요 메서드**:
- `create_post()`: 게시물 생성 (파일 처리 포함)
- `update_post()`: 게시물 수정
- `delete_post()`: 게시물 삭제 (파일 삭제 포함)
- `search_posts()`: 검색 쿼리 실행

---

## 📊 전체 통계

### REST API 엔드포인트 (총 24개, 실제 사용 19개)

| 앱 | REST API 수 | 실제 사용 | 주요 기능 |
|----|-------------|----------|-----------|
| **Teams** | 4개 | 4개 ✅ | 마일스톤 CRUD (3), 멤버 제거/탈퇴 (1) |
| **Members** | 7개 | 5개 ⚠️ | TODO 상태 관리 (할당, 완료, 이동, 삭제) / **미사용**: list, create, retrieve, update |
| **Schedules** | 3개 | 2개 ⚠️ | 개인 스케줄 저장, 팀 가용성 조회 / **미사용**: 내 스케줄 조회(SSR 대체) |
| **Mindmaps** | 10개 | 10개 ✅ | 노드 CRUD (4), 연결선 CRUD (2), 추천 (1), 댓글 CRUD (3) |
| **Shares** | 0개 | 0개 | (SSR 중심) |
| **Accounts** | 0개 | 0개 | (SSR + AJAX 엔드포인트) |

---

### AJAX 엔드포인트 (총 3개 - 템플릿 뷰용)

| 앱 | AJAX 엔드포인트 수 | 주요 기능 |
|----|-------------------|-----------|
| **Accounts** | 1개 | 이메일 인증 재발송 (AJAX 지원) |
| **Teams** | 2개 | 팀 코드 검증, 팀 가입 처리 |

**참고**: AJAX 엔드포인트는 REST API 표준을 따르지 않으며, 템플릿 페이지 내에서 `fetch()`로 호출됨

---

### SSR 템플릿 뷰 (총 34개)

| 앱 | 템플릿 뷰 수 | 주요 기능 |
|----|-------------|-----------|
| **Accounts** | 10개 | 회원가입, 로그인, 프로필 관리, 소셜 로그인 |
| **Teams** | 7개 | 팀 생성, 검색, 정보 수정, 타임라인, 해체 |
| **Members** | 1개 | 멤버 페이지 (초기 로드 + TODO Form) |
| **Schedules** | 2개 | 스케줄 조회, 업로드 페이지 |
| **Mindmaps** | 8개 | 마인드맵 CRUD (4), 노드 상세 (1), 노드 삭제 (1), 권한 부여 (1), 마인드맵 에디터 (1) |
| **Shares** | 6개 | 게시판 CRUD, 파일 다운로드 |

---

### WebSocket (1개)

| 앱 | WebSocket URL | 이벤트 타입 | 주요 기능 |
|----|---------------|------------|-----------|
| **Mindmaps** | `/ws/mindmap/<team_id>/<mindmap_id>/` | 10개 | 실시간 협업 (노드 동기화, 커서 공유, 연결선 CRUD) |

---

### ✅ 레거시 코드 정리 완료

**2025.10.18 삭제**:
- **Teams**: REST API 2개 (팀 코드 검증, 가입 액션), Serializer 2개
- **Members**: AJAX 뷰 4개, URL 패턴 4개
- **Mindmaps**: SSR 뷰 3개 (노드 생성, 노드 투표, 노드 추천), URL 패턴 3개
- **API 클라이언트**: 미사용 메서드 7개 (GET 엔드포인트)

**2025.10.19 추가 삭제**:
- **Members**: SSR 뷰 2개 (`MemberCompleteTodoView`, `MemberDeleteTodoView`), URL 패턴 2개

**총 정리**: 18개 레거시 항목 삭제 완료 ✅


---

## 🎯 설계 원칙

### API 사용 기준
다음 조건을 **2개 이상** 만족하면 API 사용:
1. ✅ 실시간성 필요 (페이지 새로고침 없음)
2. ✅ 드래그 앤 드롭 UI
3. ✅ 동적 UI 업데이트 (카운터, 필터링)
4. ✅ JSON 데이터 처리 (복잡한 구조)
5. ✅ Optimistic UI 패턴

### SSR 사용 기준
다음 조건을 **1개 이상** 만족하면 SSR 사용:
1. ✅ SEO 필요 (검색 엔진 크롤링)
2. ✅ 정적 콘텐츠 (상세 페이지, 목록)
3. ✅ 복잡한 Form (파일 업로드, 다중 필드)
4. ✅ 인증 흐름 (로그인, 회원가입)
5. ✅ 초기 로딩 성능 (첫 페이지 로드)

---

**최종 업데이트**: 2025.10.19 (Members App 레거시 SSR 뷰 정리 완료)
**버전**: 2.1
