# TeamMoa 프로젝트 메모

## 📋 프로젝트 요약
Django 기반 팀 프로젝트 관리 시스템
- 팀 관리, 스케줄링, 마인드맵, 공유 게시판, TODO 관리
- 총 28개 핵심 페이지 보유

## 🎯 현재 상태 (2025.09.25)

### ✅ 완료된 작업
1. **UI 현대화 완료** (28개 페이지 100%)
   - 일관된 디자인 시스템 구축
   - 반응형 디자인 적용
   - **CSS 모듈화 100% 완료** - 6개 앱, 21개 모듈 파일로 분리

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
1. **API 레이어 도입** - Django REST Framework와 서비스 레이어 통합
2. **테스트 커버리지 확대** - 각 서비스 메서드별 단위 테스트
3. **성능 최적화** - 서비스 레이어 기반 쿼리 최적화 및 캐싱
4. **마인드맵 고도화** - 연결선 관리, 키보드 단축키, 미니맵
5. **CI/CD 파이프라인** - 자동화된 테스트 및 배포 시스템

## 🛠️ 기술 스택
- Backend: Django 4.x, Python
- Frontend: HTML5, CSS3, JavaScript (Canvas API)
- Database: SQLite (개발), MySQL (운영)
- Architecture: Service Layer Pattern, CBV

## 📋 개발 가이드라인

### 🔧 공통 JavaScript 함수
- **위치**: `static/js/common/scripts.js`
- **주요 함수들**:
  - `showConfirmModal(message, onConfirm)`: 확인 모달 표시
  - `showToast(message)`: 토스트 알림 표시
  - `showDjangoMessages()`: Django messages를 토스트로 자동 변환

### 🎯 사용자 피드백 처리 방침
1. **사용자 알림**: 모든 경우에 Django messages 사용 (base 템플릿에서 자동으로 토스트 변환)
2. **AJAX 응답**: Django messages 활용
3. **확인/삭제 등 중요 액션**: `showConfirmModal()` 사용

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
*최종 업데이트: 2025.09.25*
