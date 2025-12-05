# TeamMoa - 프로젝트 개요

> **Django 기반 팀 협업 플랫폼**
> 실시간 마인드맵, 스케줄 조율, TODO 관리를 통합한 올인원 프로젝트 관리 시스템

---

## 목차
- [프로젝트 배경](#프로젝트-배경)
- [핵심 기능](#핵심-기능)
- [기술 스택 및 선택 이유](#기술-스택-및-선택-이유)
- [프로젝트 구조](#프로젝트-구조)
- [주요 성과](#주요-성과)
- [데모 및 링크](#데모-및-링크)

---

## 프로젝트 배경

### 문제 인식
팀 프로젝트를 진행하면서 여러 도구를 병행 사용하는 불편함을 경험했습니다:
- **Notion**: 문서 작성 및 정리
- **Google Meet**: 화상 회의
- **카카오톡**: 실시간 소통
- **Figma**: 디자인 협업
- **구글 캘린더**: 일정 조율

이러한 도구 간 전환은 협업 효율을 떨어뜨렸고, 특히 **팀원 가용 시간 조율**과 **아이디어 시각화**에 어려움이 있었습니다.

### 해결 방향
팀 프로젝트에 필요한 핵심 기능을 하나의 플랫폼에 통합:
1. **실시간 마인드맵** - 아이디어를 시각적으로 정리하고 협업
2. **스마트 스케줄** - 팀원 가용 시간 자동 계산
3. **TODO 관리** - 드래그 앤 드롭 기반 업무 분배
4. **공유 게시판** - 파일 공유 및 공지사항 관리

---

## 핵심 기능

### 1. 실시간 마인드맵 협업
**구현 목표**: 여러 명이 동시에 마인드맵을 편집하고 커서를 공유하는 시스템

**기술 구현**:
- **Canvas API** - 5400×3600px 가상 캔버스에서 노드 드래그 앤 드롭
- **Django Channels + WebSocket** - 실시간 양방향 통신
- **Redis** - WebSocket 메시지 브로커 및 채널 레이어

**주요 기능**:
- 노드 생성/이동/삭제 실시간 동기화 (WebSocket 브로드캐스팅)
- 다중 사용자 커서 공유 (50ms 스로틀링)
- 줌/팬 기능 (마우스 휠, 버튼)
- 노드 추천 시스템 (좋아요 토글)


---

### 2. 스마트 스케줄 조율
**구현 목표**: 팀원들의 주간 가용 시간을 입력받아 공통 가능 시간을 자동으로 계산

**기술 구현**:
- **JSON 데이터 구조** - 날짜별 가능한 시간대를 리스트로 저장
  ```json
  {
    "date": "2025-01-06",
    "available_hours": [9, 10, 14, 15, 16, 18]
  }
  ```
  각 숫자는 해당 시간대를 의미 (0-23시)
- **REST API** - 주차 변경 시 실시간 팀 가용성 조회
- **드래그 앤 드롭 UI** - JavaScript로 시간대 선택

**주요 기능**:
- 개인 스케줄 저장 (주차별)
- 팀 가용성 자동 계산 (0~N명)
- 빠른 선택 도구 (업무시간, 저녁시간, 평일/주말)
- ISO week 형식 지원 (YYYY-Www)

**코드 위치**:
- 서비스 로직: [`schedules/services.py`](../../schedules/services.py)
- 프론트엔드: [`static/js/pages/scheduler_upload.js`](../../static/js/pages/scheduler_upload.js)

---

### 3. TODO 관리 시스템
**구현 목표**: 팀원에게 업무를 드래그 앤 드롭으로 할당하고 진행 상태를 시각적으로 관리

**기술 구현**:
- **REST API** - DRF ViewSet 커스텀 액션 (`assign`, `complete`, `move-to-done`)
- **Optimistic UI** - API 호출 전에 DOM을 먼저 업데이트하여 UX 개선
- **권한 기반 제어** - 팀장은 모든 TODO, 일반 멤버는 자신의 TODO만 조작 가능

**주요 기능**:
- 미할당 TODO 보드 → 멤버 보드 (드래그 앤 드롭)
- 완료/미완료 상태 토글 (체크박스)
- TODO 카운터 실시간 업데이트
- 권한별 UI 분기 (팀장/일반 멤버)

**API 엔드포인트**:
```
POST /api/v1/teams/{team_pk}/todos/{pk}/assign/        # TODO 할당
POST /api/v1/teams/{team_pk}/todos/{pk}/complete/      # 완료 토글
POST /api/v1/teams/{team_pk}/todos/{pk}/move-to-done/  # DONE 보드로 이동
DELETE /api/v1/teams/{team_pk}/todos/{pk}/             # TODO 삭제
```

**참고 문서**: [아키텍처 설계 - API vs SSR](./architecture.md#api-vs-ssr-전략)

---

### 4. 공유 게시판
**구현 목표**: 팀 내 파일 공유 및 공지사항 관리

**기술 구현**:
- **Django Form + Templates** - 전통적인 SSR 방식
- **Summernote 에디터** - WYSIWYG 에디터 (이미지 임베드)
- **파일 업로드/다운로드** - 드래그 앤 드롭 UI

**주요 기능**:
- 게시물 CRUD (작성, 수정, 삭제)
- 파일 첨부 (최대 10MB)
- 검색 기능 (제목, 내용, 작성자)
- 페이지네이션 (10개/페이지)

**SSR 선택 이유**:
- 정적 콘텐츠 (게시물 상세 페이지)
- 복잡한 파일 업로드 (Django Form 활용)
- SEO 고려 (검색 엔진 크롤링)

---

## 기술 스택 및 선택 이유

### Backend
- **Django 5.2.4** - 빠른 개발 속도, ORM, Admin 패널
- **Django REST Framework** - REST API 구축 (Serializer, ViewSet)
- **Django Channels** - WebSocket 실시간 통신
- **MySQL 8.0** - 관계형 데이터베이스 (FK 제약조건, 트랜잭션)
- **Redis 7.0** - WebSocket 채널 레이어, 캐싱

**Django 선택 이유**:
1. **ORM** - 복잡한 쿼리를 Python 코드로 작성 (`select_related`, `prefetch_related`)
2. **Admin 패널** - 데이터 관리 및 디버깅 편의성
3. **Ecosystem** - django-allauth (OAuth 2.0), DRF (REST API)
4. **보안** - CSRF, XSS, SQL Injection 기본 방어

### Frontend
- **HTML5 + CSS3 + JavaScript (Vanilla)** - 프레임워크 없이 기본기 강화
- **Canvas API** - 2D 그래픽 렌더링 (마인드맵)
- **Fetch API** - REST API 호출
- **WebSocket API** - 실시간 통신

**Vanilla JS 선택 이유**:
- 프레임워크 학습 전 JavaScript 기본기 다지기
- 번들링 없이 빠른 개발 가능
- Canvas API 제어에 프레임워크 불필요

### DevOps
- **Docker + Docker Compose** - 컨테이너 기반 배포 (MySQL, Redis, Django, Nginx)
- **GitHub Actions** - CI/CD 자동화 (테스트 → 빌드 → 배포)
- **AWS EC2** - 프로덕션 서버 (Ubuntu 22.04, t3.micro)
- **Nginx** - 리버스 프록시, SSL 종료

**Docker 선택 이유**:
1. **환경 일관성** - 로컬, 테스트, 프로덕션 동일 환경
2. **의존성 격리** - MySQL, Redis 독립 컨테이너
3. **배포 간소화** - 이미지 빌드 후 Docker Hub 푸시

### Architecture
- **Service Layer Pattern** - 비즈니스 로직과 뷰 분리
- **Class-Based Views (CBV)** - Django Generic Views 활용
- **하이브리드 SSR + API** - 기능별 최적 렌더링 방식 선택

**서비스 레이어 도입 이유**:
- View에서 비즈니스 로직 제거 → 재사용성 향상
- 테스트 용이성 (서비스 로직 단위 테스트)
- API/SSR 간 로직 공유

**참고 문서**: [아키텍처 설계](./architecture.md)

---

## 프로젝트 구조

```
TeamMoa/
├── accounts/           # 인증 시스템
│   ├── services.py     # 회원가입, 이메일 인증, OAuth 로직
│   ├── adapters.py     # django-allauth 커스텀 어댑터
│   └── management/commands/
│       └── delete_unverified_users.py  # 미인증 계정 정리
│
├── teams/              # 팀 관리
│   ├── services.py     # 팀 CRUD, 멤버 관리, 마일스톤 로직
│   └── viewsets.py     # MilestoneViewSet (REST API)
│
├── members/            # TODO 관리
│   ├── services.py     # TODO 할당, 완료, 이동 로직
│   └── viewsets.py     # TodoViewSet (REST API)
│
├── schedules/          # 스케줄 관리
│   ├── services.py     # 개인 스케줄 저장, 팀 가용성 계산
│   └── viewsets.py     # ScheduleViewSet (REST API)
│
├── mindmaps/           # 마인드맵
│   ├── services.py     # 노드/연결선 CRUD, 추천 로직
│   ├── viewsets.py     # NodeViewSet, NodeConnectionViewSet
│   └── consumers.py    # WebSocket Consumer (실시간 협업)
│
├── shares/             # 게시판
│   ├── services.py     # 게시물 CRUD, 검색 로직
│   └── views.py        # SSR 뷰 (Django Form)
│
├── static/
│   ├── css/            # 모듈별 CSS
│   └── js/
│       ├── api/        # API 클라이언트
│       ├── common/     # 공통 유틸리티 (ui-utils.js)
│       └── pages/      # 페이지별 JavaScript
│
├── templates/
│   ├── base_team.html  # 팀 내부 페이지 (네비게이션 포함)
│   ├── base_user.html  # 사용자 페이지 (로그인 필요)
│   └── base_public.html # 공개 페이지 (로고만)
│
├── .github/workflows/
│   └── ci-cd.yml       # GitHub Actions CI/CD 파이프라인
│
├── docker-compose.yml      # 개발 환경
├── docker-compose.prod.yml # 프로덕션 환경
└── pytest.ini              # 테스트 설정
```

**디렉토리 설계 원칙**:
1. **앱 단위 분리** - 기능별 Django App (accounts, teams, members, ...)
2. **서비스 레이어 통일** - 모든 앱에 `services.py` 존재
3. **템플릿 계층화** - 3개 base 템플릿 (team, user, public)
4. **JavaScript 모듈화** - API 클라이언트, 공통 유틸, 페이지별 스크립트 분리

---

## 주요 성과

### 1. 테스트 커버리지 구축
- **221개 테스트** 작성 (pytest)
- **6개 앱** 모두 테스트 완료
- **서비스 레이어 우선 테스트** - 비즈니스 로직 검증

**테스트 분포**:
| 앱 | 테스트 수 | 커버리지 |
|---|---------|---------|
| Teams | 66개 | 서비스(36) + API(17) + SSR(13) |
| Members | 33개 | 서비스(20) + API(10) + SSR(3) |
| Schedules | 30개 | 서비스(15) + API(10) + SSR(5) |
| Mindmaps | 40개 | 서비스(16) + API(8) + SSR(6) + 기타(10) |
| Shares | 24개 | 서비스(13) + SSR(11) |
| Accounts | 28개 | 서비스(18) + SSR(10) |

**참고 문서**: [테스트 전략](./testing.md)

---

### 2. CI/CD 파이프라인 자동화
**구축 전**: 수동 배포 (30분 소요)
1. 로컬에서 테스트 실행
2. Docker 이미지 빌드
3. Docker Hub 푸시
4. EC2 SSH 접속
5. 이미지 풀 및 재시작

**구축 후**: 완전 자동화 (5분 소요)
```
git push origin main → 자동 테스트 → 자동 빌드 → 자동 배포 → 완료
```

**GitHub Actions 파이프라인**:
- **Stage 1: Test** - 221개 테스트 자동 실행 (실패 시 배포 중단)
- **Stage 2: Build** - Docker 이미지 빌드 및 Docker Hub 푸시
- **Stage 3: Deploy** - EC2 SSH 접속 후 자동 배포 (무중단)

**보안 강화**:
- **Dynamic Security Group** - 배포 시에만 SSH 포트 개방 (GitHub Actions IP만 허용)
- **Health Check** - 3회 재시도 (10초 간격), 실패 시 자동 롤백

**참고 문서**: [CI/CD 파이프라인](./infrastructure.md#cicd-파이프라인)

---

### 3. 프로덕션 배포
- **HTTPS 적용** - Let's Encrypt SSL 인증서 (자동 갱신)
- **도메인** - DuckDNS 무료 도메인 (`teammoa.duckdns.org`)
- **컨테이너 구성** - MySQL, Redis, Django, Nginx (모두 Healthy 상태)
- **OAuth 2.0** - Google, GitHub 소셜 로그인 정상 작동

**인프라 구성**:
```
도메인: https://teammoa.duckdns.org
서버: AWS EC2 t3.micro (Ubuntu 22.04)
IP: 3.34.102.12

컨테이너:
- teammoa_db_prod (MySQL 8.0)
- teammoa_redis_prod (Redis 7)
- teammoa_web_prod (Django + Daphne)
- teammoa_nginx_prod (Nginx 1.25 + SSL)
```

**참고 문서**: [인프라 구성](./infrastructure.md)

---

### 4. 아키텍처 개선
**문제**: View에 비즈니스 로직이 혼재되어 재사용 불가, 테스트 어려움

**해결**: 서비스 레이어 패턴 도입
- 6개 앱 모두 `services.py` 생성
- View는 HTTP 처리만, 서비스는 비즈니스 로직만
- API/SSR 간 로직 공유 (예: `TeamService.create_team()`)

**효과**:
- 코드 재사용성 증가 (API/SSR 공통 서비스)
- 테스트 용이성 향상 (서비스 단위 테스트)
- 유지보수성 개선 (로직 분리)

**참고 문서**: [아키텍처 설계 - 서비스 레이어](./architecture.md#서비스-레이어-패턴)

---

## 데모 및 링크

### 🌐 Live Demo
**URL**: [https://teammoa.duckdns.org](https://teammoa.duckdns.org)

**테스트 계정**:
- 회원가입 후 이메일 인증 필요
- Google/GitHub OAuth 로그인 가능

### 📦 GitHub Repository
**URL**: [https://github.com/TlesMes/TeamMoa-Refactor](https://github.com/TlesMes/TeamMoa-Refactor)

### 📚 상세 문서
- [아키텍처 설계](./architecture.md) - 서비스 레이어, 하이브리드 SSR+API
- [실시간 협업](./features/realtime-mindmap.md) - WebSocket, Django Channels
- [인프라 구성](./infrastructure.md) - Docker, CI/CD, AWS
- [테스트 전략](./testing.md) - pytest, 221개 테스트
- [트러블슈팅](./troubleshooting.md) - 15건 해결 사례

---

## 학습 내용

### 1. Django 심화
- **서비스 레이어 패턴** - Fat Model 문제 해결
- **django-allauth** - OAuth 2.0 커스텀 어댑터
- **Django Channels** - WebSocket 실시간 통신
- **DRF ViewSet** - 커스텀 액션

### 2. 데이터베이스 최적화
- **N+1 쿼리 해결** - `select_related`, `prefetch_related`
- **트랜잭션 관리** - `@transaction.atomic` (회원가입 + 이메일 발송)
- **Soft Delete** - `is_deleted` 필드로 계정 복구 가능

### 3. 인프라 및 DevOps
- **Docker** - 멀티 스테이지 빌드, Health Check
- **GitHub Actions** - CI/CD 파이프라인, Dynamic Security Group
- **Nginx** - 리버스 프록시, WebSocket 프록시 설정
- **Let's Encrypt** - SSL 인증서 자동 갱신 (crontab)

### 4. 프론트엔드
- **Canvas API** - 2D 렌더링, 드래그 앤 드롭 구현
- **WebSocket** - 양방향 통신, 스로틀링 (50ms)
- **Optimistic UI** - DOM 조작 후 API 호출 (UX 개선)

---

## 개선 계획

### 1. 성능 최적화 (다음 단계)
- [ ] N+1 쿼리 완전 제거 (django-debug-toolbar 활용)
- [ ] Redis 캐싱 전략 구현 (팀 목록, 스케줄 조회)
- [ ] 데이터베이스 인덱스 추가 (쿼리 성능 개선)

### 2. 모니터링 시스템
- [ ] Sentry 연동 (에러 추적)
- [ ] 로깅 시스템 강화 (DEBUG → INFO → ERROR 레벨 분리)
- [ ] 성능 메트릭 수집 (응답 시간, DB 쿼리 수)

### 3. 기능 확장
- [ ] 마인드맵 버전 관리 (Git 스타일)
- [ ] TODO 우선순위 및 마감일 추가
- [ ] 팀 채팅 기능 (WebSocket)

---

**작성일**: 2025년 12월 2일
**버전**: 1.0
