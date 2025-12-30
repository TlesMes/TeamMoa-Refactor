# TeamMoa 프로젝트 메모

## 📋 프로젝트 요약
Django 기반 팀 프로젝트 관리 시스템
- 팀 관리, 스케줄링, 마인드맵, 공유 게시판, TODO 관리
- 총 28개 핵심 페이지 보유

## 🎯 현재 진행 중인 작업

### 🚀 마일스톤-TODO 연동 기능 개선 (2025.12.26)

**📋 백엔드 구현 완료 (Phase 1-3)**:
- ✅ **Phase 1 완료 (2025.12.26)**: 모델 및 마이그레이션
  - Milestone.progress_mode 필드, Todo.milestone FK 추가
  - 4개 모델 메서드 구현, 마이그레이션 실행
- ✅ **Phase 2 완료 (2025.12.28)**: 서비스 레이어 확장
  - MilestoneService 4개 메서드, TodoService 3개 메서드 구현
  - 24개 테스트 추가 (총 249개 테스트 통과)
- ✅ **Phase 3 완료 (2025.12.29)**: API 레이어 구현
  - MilestoneViewSet/TodoViewSet 확장, Serializer 추가
  - toggle_progress_mode, assign_milestone API 구현

**🎯 핵심 기능**:
1. **진행률 관리 방식 선택**
   - 수동 모드: 팀장이 슬라이더로 직접 조정 (주관적 추정)
   - AUTO 모드: TODO 완료율로 자동 계산 (객관적 지표)

2. **TODO-마일스톤 연결**
   - TODO를 마일스톤에 할당
   - TODO 완료 시 마일스톤 진행률 자동 갱신 (AUTO 모드)
   - 100% 도달 시 마일스톤 자동 완료

3. **모드 전환 정책**
   - 수동 → AUTO: 즉시 TODO 기반 재계산
   - AUTO → 수동: 기존 진행률 유지

**📦 남은 작업 (Phase 4-5)**:
- ⏳ **Phase 4 (진행 예정)**: 프론트엔드 구현 (2-3일)
  - Day 1: API Client 확장, 진행률 슬라이더 컴포넌트, 타임라인 업데이트
  - Day 2: 마일스톤 수정 모달 (HTML/JS/CSS)
  - Day 3: TODO 페이지 연동 (배지, 할당 드롭다운, 토스트)
- ⏳ **Phase 5**: 최종 테스트 및 배포 (1일)
  - 통합 테스트, 엣지 케이스, 성능 테스트, 프로덕션 배포

**📚 참고 문서**:
- [마일스톤 개선 계획](./docs/architecture/design/milestone_improvement_plan.md)
- [시나리오 및 DB 변경](./docs/architecture/design/milestone_scenario_and_db_changes.md)
- [API 마이그레이션 가이드](./docs/architecture/refactoring/api_migrations/milestone_api_migration.md)

**다음 작업**: Phase 4 구현 시작 - 프론트엔드 UI 구축

---

### 📚 포트폴리오 문서화 완료! (2025.12.08)

**✅ 포트폴리오 문서 완료** (9개 문서, 96페이지, 150+ 코드):
- ✅ **핵심 문서 5개**: overview, architecture, infrastructure, testing, troubleshooting
- ✅ **기능 상세 3개**: 실시간 마인드맵, OAuth 2.0 인증, 성능 최적화
- ✅ **README**: 문서 가이드

**✅ 문서 구조 대폭 개선** (2025.12.08):
- ✅ **6단계 카테고리 체계**: portfolio | architecture (design|refactoring|migration) | guides | development | troubleshooting
- ✅ **docs/README.md 간소화**: 314줄 → 113줄 (64% 감소)
- ✅ **44개 문서 재분류**: 정적 구조 vs 시간의 흐름 분리
- ✅ **가독성 대폭 개선**: 수평선 구분, 인용구 설명, 들여쓰기 단순화
- ✅ **구버전 정리**: archive/ 삭제, oauth_account_design.md 삭제

**✅ Mermaid 다이어그램 4개 추가** (2025.12.08):
- ✅ **ERD 다이어그램** (architecture.md) - 10개 핵심 엔터티, 관계 시각화
- ✅ **CI/CD 파이프라인** (infrastructure.md) - 3-stage 배포 흐름, 색상 코딩
- ✅ **WebSocket 아키텍처** (realtime-mindmap.md) - Sequence Diagram, 실시간 협업 프로세스
- ✅ **서비스 레이어 흐름도** (README.md) - 4계층 구조, SSR/API 병행

**🎯 핵심 성과**:
- **문서 체계화**: 복잡한 디렉토리 구조 → 명확한 6단계 카테고리
- **네비게이션 개선**: 프로젝트 대시보드 → 독자 중심 문서 가이드
- **유지보수성 향상**: 정적 구조(design) vs 시간의 흐름(refactoring) 분리
- **시각화 완성**: 텍스트 다이어그램 → Mermaid (GitHub 자동 렌더링)
- **코드 검증률**: 100% (모든 코드 스니펫 실제 프로젝트 코드 일치)

---

### 🎉 AWS ALB + Multi-AZ 고가용성 인프라 구축 완료! (2025.12.16)

**✅ 프로덕션 인프라 완전 구축**:
- ✅ **AWS Application Load Balancer 구축**: 2대 EC2 로드밸런싱
- ✅ **Multi-AZ 고가용성 아키텍처**: ap-northeast-2a, 2b (가용 영역 분산)
- ✅ **Rolling Update 무중단 배포**: Target Group Deregister/Register 자동화
- ✅ **HTTPS 적용**: ACM SSL 인증서 (*.teammoa.shop)
- ✅ **WebSocket 안정화**: ALB Sticky Session 설정 (app_cookie)
- ✅ **Security Group 최적화**: Web/DB 분리, 최소 권한 원칙

**✅ 부하 테스트 및 성능 검증 완료**:
- ✅ **Locust 부하 테스트 4회 실시** (총 57,232건 요청)
  - 점진적 부하 증가: 20명 → 50명 → 100명 → 150명
  - 95%ile 응답 시간: **70ms** (목표 500ms 대비 86% 향상)
  - 평균 응답 시간: **52ms** (매우 안정적)
  - 에러율: **0.16%** (목표 1% 대비 84% 향상)
  - 최대 RPS: **40.34** (목표 10 대비 303% 초과 달성)
- ✅ **실제 트래픽 검증**: 로드밸런싱 균등 분산 확인
- ✅ **무중단 배포 검증**: 배포 중 200 응답 유지 (다운타임 0초)

**📊 핵심 성과**:
- **고가용성**: Multi-AZ 구성으로 99.9% 가용성 달성
- **무중단 배포**: CI/CD Rolling Update 자동화 (배포 중 서비스 중단 없음)
- **성능**: SLA 목표 초과 달성 (응답 속도 86% 향상, 에러율 84% 감소)
- **확장성**: ALB Auto Scaling 준비 완료 (트래픽 증가 시 EC2 추가 가능)

**🏗️ 인프라 구조**:
```
Internet → ALB (HTTPS:443)
           ├─ EC2-Web1 (ap-northeast-2a) → MySQL + Redis
           └─ EC2-Web2 (ap-northeast-2b) → MySQL + Redis
```

**💰 비용**:
- 현재: 월 약 $22 (ALB만, EC2는 프리티어)
- 프리티어 종료 후: 월 $40~$50 (ALB + EC2 2대)

**📚 참고 문서**:
- [부하 테스트 리포트](./docs/guides/load-testing/load-test-report.md)
- [ALB 구축 가이드](./docs/guides/alb_deployment_guide.md)
- [infrastructure.md - ALB 섹션](./docs/portfolio/infrastructure.md#aws-application-load-balancer-alb)

---

### 🔐 회원 탈퇴 및 미인증 계정 관리 개선 완료! (2025.11.24)

**✅ 문제 해결: username/email 영구 점유 방지**:
- ✅ User 모델에 `is_deleted`, `deleted_at` 필드 추가
- ✅ 미인증 계정(`is_active=False`, `is_deleted=False`)과 탈퇴 계정 구분
- ✅ 3일 이상 미인증 계정 자동 삭제 Management Command 구현
- ✅ Admin 페이지에서 계정 상태 확인 및 필터링 기능 추가
- ✅ 회원 탈퇴 서비스 로직 개선 (Soft Delete 적용)

**구현 내용**:
```python
# Management Command 사용법
python manage.py delete_unverified_users              # 3일 기준 삭제
python manage.py delete_unverified_users --days 7     # 7일 기준 삭제
python manage.py delete_unverified_users --dry-run    # 삭제 대상 확인만
python manage.py delete_unverified_users --verbose    # 상세 정보 출력
```

**개선 효과**:
- 이메일 잘못 입력 시 username/email 영구 점유 문제 해결
- 미인증 계정 자동 정리로 DB 용량 최적화
- 탈퇴/미인증 계정 상태 명확히 구분 가능

**테스트 커버리지**:
- 회원 탈퇴 서비스 테스트에 `is_deleted`, `deleted_at` 검증 추가
- Shares 앱에 탈퇴한 작성자 처리 테스트 4개 추가
<!-- AUTO:TEST_COUNT -->
- 모든 테스트 통과 (249개)

---

### 🚀 CI/CD 파이프라인 구축 완료! (2025.11.21)

**✅ 완전 자동화된 배포 시스템 구축**:
- ✅ GitHub Actions 기반 3-stage 파이프라인 (Test → Build → Deploy)
<!-- AUTO:TEST_COUNT -->
- ✅ 264개 테스트 자동 실행
- ✅ Docker 이미지 자동 빌드 및 Docker Hub 푸시
- ✅ EC2 자동 배포 (무중단 배포)
- ✅ Dynamic Security Group (배포 시에만 SSH 포트 개방)

**성과**: 수동 배포 → 완전 자동화 (git push로 EC2배포까지 한번에 완료)

**파이프라인 구조**:
```
git push origin main → 자동으로 Test → Build → Deploy → 완료!
```

**보안 & 안정성**:
- ✅ 테스트 실패 시 배포 중단
- ✅ AWS IAM 최소 권한 + Dynamic Security Group
- ✅ Health check 재시도 (3회, 10초 간격)
- ✅ 실패 시 자동 롤백 (IP 제거 보장)

---

### 🎉 프로덕션 배포 완료! (2025.11.20)

**✅ 모든 핵심 인프라 구축 완료**:
- ✅ AWS EC2 인스턴스 구축 (t3.micro, Ubuntu 22.04)
- ✅ Elastic IP 할당: `3.34.102.12`
- ✅ Docker Hub 이미지: `tlesmes/teammoa-web:latest`
- ✅ 4개 컨테이너 모두 **Healthy 상태** (MySQL, Redis, Django, Nginx)
- ✅ HTTPS 적용 완료: `https://teammoa.duckdns.org`
- ✅ OAuth 2.0 인증 (Google, GitHub) 정상 작동
- ✅ Let's Encrypt SSL 인증서 자동 갱신 설정 (crontab)

**배포 상세**:
```
도메인: https://teammoa.duckdns.org
IP: 3.34.102.12

컨테이너 상태 (모두 Healthy):
- teammoa_db_prod (MySQL 8.0) ✅
- teammoa_redis_prod (Redis 7) ✅
- teammoa_web_prod (Django + Daphne) ✅
- teammoa_nginx_prod (Nginx 1.25 + SSL) ✅

SSL 인증서: Let's Encrypt (자동 갱신)
```

**주요 해결 이슈**:
- ✅ HTTPS 리디렉션 루프 해결 (`SECURE_PROXY_SSL_HEADER` 설정)
- ✅ Docker 로그 디렉토리 권한 문제 해결
- ✅ Health check 엔드포인트 분리 (`/nginx-health`, `/health/`)
- ✅ IPv6 localhost 해결 (`127.0.0.1` 명시)
- ✅ `ALLOWED_HOSTS`에 `127.0.0.1` 추가 (health check용)
- ✅ Docker 이미지 네이밍 통일 (`tlesmes/teammoa-web`)

**환경 설정** (`.env`):
```bash
DEBUG=False
ALLOWED_HOSTS=3.34.102.12,localhost,127.0.0.1,teammoa.duckdns.org,web
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
CORS_ALLOWED_ORIGINS=https://teammoa.duckdns.org
```

---

### 🐳 Docker 배포 환경 구축 (2025.10.23 완료)

**구축 완료**:
- ✅ Docker + Docker Compose 개발/운영 환경
- ✅ MySQL 8.0 + Redis 7 + Django (Daphne) 컨테이너화
- ✅ 멀티 스테이지 빌드 최적화
- ✅ Health check 자동 모니터링
- ✅ entrypoint.sh 자동화 스크립트
- ✅ Nginx 리버스 프록시 설정 (WebSocket 포함)
- ✅ 단일 .env 파일로 환경 관리

**Docker 테스트 결과**:
- 3개 컨테이너 모두 healthy 상태
- 웹 접속 정상 (localhost:8000)
- Volume mounting으로 코드 실시간 반영 확인

---

### 🧪 테스트 커버리지 구축 (2025.10.19~2025.10.22 완료)

<!-- AUTO-GENERATED-TEST-STATS:START -->
| 앱 | 서비스 | API | SSR | 합계 |
|---|---------|-----|-----|------|
| Accounts | 18 | - | 10 | 28 |
| Teams | 53 | 19 | 15 | 87 |
| Members | 32 | 16 | 3 | 51 |
| Schedules | 12 | 13 | 9 | 34 |
| Shares | 20 | - | 13 | 33 |
| Mindmaps | 16 | 8 | 7 | 31 |
| **총계** | **151** | **56** | **57** | **264** |
<!-- AUTO-GENERATED-TEST-STATS:END -->

**테스트 전략**:
- pytest + DRF TestClient 활용
- fixture 기반 공통 설정 재사용 (conftest.py)
- 서비스 레이어 우선 테스트 (비즈니스 로직 검증)
- 실제 사용 중인 API만 테스트 (미사용 API 제외)
- DB 상태 기반 검증으로 서비스 구현 의존도 최소화
- 통일된 클라이언트 fixture 구조 (`authenticated_api_client`, `authenticated_web_client`)

## 🚀 완료된 단계

<!-- AUTO:TEST_COUNT -->
1. **테스트 커버리지 구축** - ✅ 완료 (6/6 앱, 264개 테스트, 2025.10.22)
2. **Docker 배포 환경 구축** - ✅ 완료 (개발/운영 환경, 2025.10.23)
3. **AWS EC2 프로덕션 배포** - ✅ 완료 (HTTP 배포, 2025.11.18)
4. **HTTPS 설정** - ✅ 완료 (Let's Encrypt + DuckDNS, 2025.11.20)
5. **CI/CD 파이프라인 구축** - ✅ 완료 (GitHub Actions 자동 배포, 2025.11.21)
6. **회원 탈퇴 및 미인증 계정 관리 개선** - ✅ 완료 (Soft Delete + 자동 정리, 2025.11.24)
7. **포트폴리오 문서 작성** - ✅ 완료 (9개 문서, 96페이지, 150+ 코드, 2025.12.08)
8. **문서 구조 재구성** - ✅ 완료 (6단계 카테고리, 64% 간소화, 2025.12.08)
9. **AWS ALB + Multi-AZ 고가용성 인프라 구축** - ✅ 완료 (2025.12.16)
   - ALB 로드밸런싱, Rolling Update, 부하 테스트 완료
10. **마일스톤-TODO 연동 기능 개선 계획 수립** - ✅ 완료 (2025.12.26)
   - 비즈니스 설계, 구현 계획 문서화, 5단계 7일 계획 수립

### 📋 다음 목표 (우선순위 순)

1. **마일스톤-TODO 연동 기능 구현** (7일) - ⏳ 다음 작업
   - Phase 1: 모델 및 마이그레이션
   - Phase 2: 서비스 레이어 확장
   - Phase 3: API 레이어
   - Phase 4: 프론트엔드 구현
   - Phase 5: 테스트 및 배포

2. **성능 최적화** (3-4시간)
   - 서비스 레이어 기반 쿼리 최적화
   - N+1 쿼리 해결
   - 캐싱 전략 구현 (Redis 활용)
   - 데이터베이스 인덱스 추가

3. **모니터링 시스템 구축** (2-3시간)
   - Health check 개선 (Django health 엔드포인트 추가)
   - 로깅 시스템 강화
   - 에러 추적 (Sentry 연동)
   - 성능 메트릭 수집

## 🛠️ 기술 스택
- Backend: Django 4.x, Python, Django REST Framework, django-allauth
- Frontend: HTML5, CSS3, JavaScript (Canvas API)
- Database: MySQL 8.0
- Infrastructure: Docker, Docker Compose, Nginx, AWS EC2, **AWS ALB (Application Load Balancer)**
- Cache & WebSocket: Redis 7
- Architecture: Service Layer Pattern, CBV, Hybrid SSR + API
- Authentication: OAuth 2.0 (Google, GitHub)
<!-- AUTO:TEST_COUNT -->
- Testing: pytest, DRF TestClient (264 tests), Locust (부하 테스트)
- Deployment: Docker Hub, AWS ALB + EC2 Multi-AZ (고가용성 구성)
- CI/CD: GitHub Actions (Rolling Update 무중단 배포)

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
- **Docker 배포**: `docs/deployment/deployment_guide.md`

### 프로젝트 대시보드
- **전체 진행상황**: `docs/README.md`

---

## 🔧 배포 파일 위치

### 로컬
- **환경변수**: `d:\github\TeamMoa\.env.ec2`
- **Docker Compose**: `d:\github\TeamMoa\docker-compose.prod.yml`

### EC2 서버 (SSH: `ssh teammoa`)
- **환경변수**: `~/TeamMoa/.env`
- **Docker Compose**: `~/TeamMoa/docker-compose.prod.yml`
- **Nginx 설정**: `~/TeamMoa/deploy/nginx-site.conf`

### 명령어
```bash
# EC2 접속
ssh teammoa

# 작업 디렉토리
cd ~/TeamMoa

# 컨테이너 상태
docker compose -f docker-compose.prod.yml ps
```

---

**참고**: docs/README.md에서:
  1. 프로젝트 진행상황 실시간 업데이트
  2. 각 단계별 완료 현황 기록
  3. 성과 지표 및 통계 갱신
  4. 다음 목표 및 계획 명시


---
*최종 업데이트: 2025.12.16 - AWS ALB + Multi-AZ 고가용성 인프라 구축 및 부하 테스트 완료*
