# TeamMoa 프로젝트 메모

## 📋 프로젝트 요약
Django 기반 팀 프로젝트 관리 시스템
- 팀 관리, 스케줄링, 마인드맵, 공유 게시판, TODO 관리
- 총 28개 핵심 페이지 보유

## 🎯 현재 상태 (2025.10.11)

### ✅ 완료된 작업
1. **UI 현대화 완료** (28개 페이지 100%)
   - 일관된 디자인 시스템 구축
   - 반응형 디자인 적용
   - **CSS 모듈화 100% 완료** - 6개 앱, 21개 모듈 파일로 분리
   - **🎉 Members App API 기반 실시간 UI** - REST API 호출 기반 실시간 TODO 관리 시스템

2. **백엔드 리팩토링 완료**
   - 네이밍 컨벤션 통일 (`Team_User` → `TeamUser` 등)
   - 모델 구조 정리 (중복 필드 제거)
   - **CBV 전환 100% 완료** - 6개 앱, 47개 뷰 모두 전환
   - **스케줄 모델 재설계 완료** - JSON 기반 구조로 전환

3. **🎉 서비스 레이어 도입 100% 완료**
   - **전체 6개 앱 완료** - Accounts, Teams, Members, Schedules, Mindmaps, Shares
   - **총 59개 서비스 메서드** 구현 (7개 서비스 클래스)
   - **평균 뷰 복잡도 31% 감소** 달성
   - 모든 비즈니스 로직의 서비스 레이어 중앙화 완료
   - 권한 관리, 트랜잭션 보장, 데이터 검증 체계 통합

4. **마인드맵 시스템 현대화**
   - **가상 캔버스 시스템** 구현 (5400×3600 픽셀)
   - **동적 그리드 및 시각적 피드백** 시스템
   - **모던 노드 디자인** - 둥근 모서리, 그라데이션, 드롭 섀도우
   - 실시간 협업 기능 완성

5. **문서화 체계 구축**
   - docs 디렉토리 카테고리별 구조화 (15개 문서)
   - 서비스 레이어 가이드라인 및 마이그레이션 로드맵 완성
   - CBV 전환 종합 보고서 작성
   - **모든 문서 최신화 완료** (2025.09.16)

## 🚀 다음 단계 (우선순위순)
1. ✅ **마인드맵 연결선 개선** - 화살표 렌더링, 둥근 모서리 반영 완료
2. ✅ **Shares 검색 기능** - 제목/내용/작성자 검색, 페이지네이션 완료
3. ✅ **Shares 드래그 앤 드롭 업로드** - 파일 업로드 UX 개선 완료
4. **Shares 태그 시스템** - 게시물 태그 분류 (선택사항)
5. **OAuth 소셜 로그인** - GitHub + Google OAuth 2.0 구현 (포트폴리오)
6. **테스트 커버리지 확대** - API 엔드포인트 및 서비스 레이어 단위 테스트
7. **성능 최적화** - 서비스 레이어 기반 쿼리 최적화 및 캐싱

## 🛠️ 기술 스택
- Backend: Django 4.x, Python, Django REST Framework
- Frontend: HTML5, CSS3, JavaScript (Canvas API)
- Database: SQLite (개발), MySQL (운영)
- Architecture: Service Layer Pattern, CBV, Hybrid SSR + API

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

**장점**:
- 각 기능의 특성에 맞는 최적의 방식 선택
- 점진적 마이그레이션 가능
- 기존 코드 재사용 (서비스 레이어)

### 🏗️ Base 템플릿 구조
- **base_team.html**: 팀 내부 페이지 (팀 네비게이션 포함 - 홈, 시간표, 마인드맵, 공유게시판)
- **base_user.html**: 사용자 페이지 (로그인된 사용자용, 팀 메뉴 불필요 - 인증, 팀 관리)
- **base_public.html**: 공개 페이지 (로고만 - 랜딩, 회원가입 완료)

### 🔧 공통 JavaScript 함수 (`ui-utils.js`)
- **위치**: `static/js/common/ui-utils.js`
- **자동 로드**: 모든 base 템플릿에서 자동 로드됨 (`base_team.html`, `base_user.html`, `base_public.html`)

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
- `ui`: 전체 UI 관련

### 🔧 환경 설정 관리
- **환경변수**: `.env.example` 파일을 참고하여 개발환경마다 `.env` 파일 생성
- **데이터베이스**: MySQL (teammoa_db, teammoa_user)
- **이메일**: SMTP 설정 필요 (Gmail 앱 비밀번호 사용)
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

### 3. 서비스 레이어 진행상황 체크
```bash
find . -name "services.py" -not -path "./venv/*"  # 구현된 서비스 확인
```

### 4. 다음 작업 가이드라인 참고
```bash
Read docs/architecture/service_layer/service_layer_guidelines.md  # 패턴 가이드
Read docs/architecture/service_layer/migration_roadmap.md         # 진행 계획
```

- 앞으로 docs/README.md에서:
  1. 프로젝트 진행상황 실시간 업데이트
  2. 각 단계별 완료 현황 기록
  3. 성과 지표 및 통계 갱신
  4. 다음 목표 및 계획 명시

  
---
*최종 업데이트: 2025.10.11*
