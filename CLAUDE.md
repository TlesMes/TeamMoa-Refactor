# TeamMoa 프로젝트 메모

## 📋 프로젝트 요약
Django 기반 팀 프로젝트 관리 시스템
- 팀 관리, 스케줄링, 마인드맵, 공유 게시판, TODO 관리
- 총 28개 핵심 페이지 보유

## 🎯 현재 진행 중인 작업

### 🧪 테스트 커버리지 구축 (2025.10.19~)

| 앱 | 테스트 수 | 상태 | 커버리지 |
|---|---------|------|---------|
| **Teams** | 66개 | ✅ 완료 | 서비스(36) + API(17) + SSR(13) |
| **Members** | 33개 | ✅ 완료 | 서비스(20) + API(10) + SSR(3) |
| **Schedules** | 30개 | ✅ 완료 | 서비스(15) + API(10) + SSR(5) |
| **Shares** | 24개 | ✅ 완료 | 서비스(13) + SSR(11) |
| **Mindmaps** | 0개 | ⏳ 예정 | 서비스 + API + WebSocket + SSR |
| **Accounts** | 0개 | ⏳ 예정 | OAuth + SSR |
| **총계** | **153개** | **75%** | 4/6 앱 완료 |

**테스트 전략**:
- pytest + DRF TestClient 활용
- fixture 기반 공통 설정 재사용 (conftest.py)
- 서비스 레이어 우선 테스트 (비즈니스 로직 검증)
- 실제 사용 중인 API만 테스트 (미사용 API 제외)

## 🚀 다음 단계

1. **테스트 커버리지 확대** - ⏳ 진행 중 (4/6 앱 완료, 153개 테스트)
   - ✅ Teams App (66개)
   - ✅ Members App (33개)
   - ✅ Schedules App (30개)
   - ✅ Shares App (24개)
   - ⏳ Mindmaps, Accounts 예정

2. **성능 최적화** - 서비스 레이어 기반 쿼리 최적화 및 캐싱

## 🛠️ 기술 스택
- Backend: Django 4.x, Python, Django REST Framework, django-allauth
- Frontend: HTML5, CSS3, JavaScript (Canvas API)
- Database: SQLite (개발), MySQL (운영)
- Architecture: Service Layer Pattern, CBV, Hybrid SSR + API
- Authentication: OAuth 2.0 (Google, GitHub)
- Testing: pytest, DRF TestClient

## 📋 개발 가이드라인

### 🏗️ API 아키텍처 전략

프로젝트는 **하이브리드 SSR + API** 방식을 채택합니다:

#### 📌 SSR 중심 (Django Templates 유지)
**정적이고 SEO가 중요한 기능**
- **accounts**: 로그인, 회원가입, 비밀번호 찾기, 이메일 인증
- **shares**: 게시판 CRUD, 파일 업로드/다운로드
- **mindmaps (부분)**: 노드 상세 페이지 (댓글 조회, 콘텐츠 표시)

**특징**:
- Django Form + Templates 활용
- 페이지 새로고침 방식
- 복잡한 파일 처리에 유리
- 정적 콘텐츠 표시에 적합

#### ⚡ API 중심 (REST API + JavaScript)
**동적이고 실시간성이 중요한 기능**
- **teams**: 팀 생성/수정/삭제, 멤버 관리, 마일스톤 CRUD
- **members**: TODO CRUD, 드래그 앤 드롭, 상태 변경
- **schedules**: 주간 스케줄 저장/조회, 팀 가용성 실시간 계산
- **mindmaps**: 노드 CRUD, 연결선 CRUD, 드래그 이동, 실시간 협업, 노드 추천

**특징**:
- DRF ViewSet + Serializers
- 서비스 레이어 재사용
- 페이지 새로고침 없는 UX
- JSON 기반 통신
- 실시간 상태 업데이트

### 🏗️ Base 템플릿 구조
- **base_team.html**: 팀 내부 페이지 (팀 네비게이션 포함 - 홈, 시간표, 마인드맵, 공유게시판)
- **base_user.html**: 사용자 페이지 (로그인된 사용자용, 팀 메뉴 불필요 - 인증, 팀 관리)
- **base_public.html**: 공개 페이지 (로고만 - 랜딩, 회원가입 완료)

### 🔧 공통 JavaScript 함수 (`ui-utils.js`)
- **위치**: `static/js/common/ui-utils.js`
- **자동 로드**: 모든 base 템플릿에서 자동 로드됨

**주요 함수들**:

#### 1️⃣ **토스트 알림**
```javascript
// 기본 토스트 (다크 그레이)
showToast('메시지 내용');

// Django 스타일 토스트 (레벨별 색상 + 아이콘)
showDjangoToast('성공 메시지', 'success');  // 초록색 + 체크 아이콘
showDjangoToast('에러 메시지', 'error');    // 빨간색 + 경고 아이콘
showDjangoToast('경고 메시지', 'warning');  // 주황색 + 알림 아이콘
showDjangoToast('정보 메시지', 'info');     // 파란색 + 정보 아이콘
```

#### 2️⃣ **확인 모달**
```javascript
showConfirmModal('정말 삭제하시겠습니까?', () => {
    // 확인 버튼 클릭 시 실행할 코드
});
```

#### 3️⃣ **Django Messages 자동 변환**
```javascript
showDjangoMessages();  // Django messages를 토스트로 자동 표시 (DOMContentLoaded에서 자동 실행)
```

### 🎯 사용자 피드백 처리 방침
1. **백엔드 응답**: Django messages 사용 → 자동으로 토스트 변환
2. **API 응답 (성공)**: `showDjangoToast(message, 'success')` 사용
3. **API 응답 (실패)**: `showDjangoToast(message, 'error')` 사용
4. **확인/삭제 등 중요 액션**: `showConfirmModal()` 사용

### 📝 커밋 메시지 스타일 가이드

**템플릿**:
```
<type>(<scope>): <description>

<body (optional)>

"""마지막에 Claude Code 생성 표시와 Co-Authored-By 는 제외할 것"""
```

**Type 종류**:
- `feat`: 새 기능 추가
- `style`: 코드 스타일링, UI/UX 개선
- `fix`: 버그 수정
- `refactor`: 리팩토링
- `docs`: 문서 변경
- `test`: 테스트 추가/수정
- `chore`: 빌드/설정 변경

**Scope 예시**:
- `mindmap`: 마인드맵 관련
- `accounts`: 계정 관련
- `teams`: 팀 관리 관련
- `shares`: 공유 게시판 관련
- `schedules`: 스케줄 관련
- `members`: 멤버 관리 관련
- `ui`: 전체 UI 관련

### 🔧 환경 설정 관리
- **환경변수**: `.env.example` 파일을 참고하여 개발환경마다 `.env` 파일 생성
- **데이터베이스**: MySQL (teammoa_db, teammoa_user)
- **이메일**: SMTP 설정 필요 (Gmail 앱 비밀번호 사용)
- **OAuth 설정**: Google Cloud Console + GitHub OAuth Apps에서 Client ID/Secret 발급
  - 가이드: `docs/oauth_setup_guide.md` 참고
- **비밀번호 정책**: 최소 8자, 일반적이지 않은 비밀번호, 숫자만 불가 (AUTH_PASSWORD_VALIDATORS)

## 🔍 새 세션에서 현황 파악 방법

### 1. 전체 프로젝트 현황 확인
```bash
Read docs/README.md  # 📊 프로젝트 대시보드 (진행률, 성과 지표)
```

### 2. 최근 작업 히스토리 확인
```bash
git log --oneline -10  # 최근 커밋 확인
git status            # 현재 작업 중인 파일
```

### 3. API vs SSR 사용 현황 확인
```bash
Read docs/architecture/detailed_api_ssr_mapping.md
```

### 4. 서비스 레이어 가이드라인 참고
```bash
Read docs/architecture/service_layer/service_layer_guidelines.md
```

## 📁 주요 문서 경로 색인

### 아키텍처 문서
- **API/SSR 아키텍처 매핑**: `docs/architecture/detailed_api_ssr_mapping.md`
  - 기능별 URL 패턴, 뷰 이름, HTTP 메서드
  - JavaScript 함수와 API 엔드포인트 정확한 매핑
  - WebSocket 이벤트 타입 및 데이터 구조
  - 총 24개 REST API, 3개 AJAX 엔드포인트, 34개 SSR 뷰, 1개 WebSocket

- **서비스 레이어**: `docs/architecture/service_layer/service_layer_guidelines.md`

### 설정 가이드
- **OAuth 설정**: `docs/oauth_setup_guide.md`
- **환경 변수**: `.env.example`

### 프로젝트 대시보드
- **전체 진행상황**: `docs/README.md`

---

**참고**: docs/README.md에서:
  1. 프로젝트 진행상황 실시간 업데이트
  2. 각 단계별 완료 현황 기록
  3. 성과 지표 및 통계 갱신
  4. 다음 목표 및 계획 명시


---
*최종 업데이트: 2025.10.20*
