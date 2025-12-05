# TeamMoa 포트폴리오 문서

> **Django 기반 팀 협업 플랫폼**
> 실시간 마인드맵, 스케줄 조율, TODO 관리를 통합한 올인원 프로젝트 관리 시스템

---

## 📸 프로젝트 스냅샷

### 서비스 레이어 아키텍처 흐름도

```
┌──────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌──────────────────┐              ┌──────────────────┐          │
│  │  Web Browser     │              │  API Client      │          │
│  │  (SSR + JS)      │              │  (REST/JSON)     │          │
│  └────────┬─────────┘              └────────┬─────────┘          │
└───────────┼─────────────────────────────────┼────────────────────┘
            │                                 │
            │ HTTP Request                    │ HTTP Request
            ▼                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                            │
│  ┌──────────────────┐              ┌──────────────────┐          │
│  │  Django Views    │              │  DRF ViewSets    │          │
│  │  (SSR)           │              │  (API)           │          │
│  │  - Form 처리      │              │  - JSON 응답     │          │
│  │  - 템플릿 렌더링   │              │  - Serializer    │          │
│  └────────┬─────────┘              └────────┬─────────┘          │
└───────────┼──────────────────────────────────┼───────────────────┘
            │                                  │
            └──────────────┬───────────────────┘
                           │ Both use
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Business Logic (services.py)                            │   │
│  │  - TeamService.create_team()                             │   │
│  │  - TodoService.assign_todo()                             │   │
│  │  - ScheduleService.get_team_availability()               │   │
│  │  - MindmapService.create_node()                          │   │
│  └────────────────────────┬─────────────────────────────────┘   │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │  Django ORM      │────────────▶│  MySQL 8.0       │         │
│  │  (models.py)     │              │  Database        │         │
│  └──────────────────┘              └──────────────────┘         │
└─────────────────────────────────────────────────────────────────┘

💡 핵심: View/ViewSet은 HTTP만 처리, Service는 비즈니스 로직만 담당
```

### Backend
- **Django 5.2.4** + DRF (REST API)
- **서비스 레이어 패턴** (View/Service/Model 분리)
- **하이브리드 SSR+API** (34개 SSR + 24개 API)
- **Django Channels** (WebSocket 실시간 협업)

### Database
- **MySQL 8.0** (관계형 데이터베이스)
- **6개 Django App** (accounts, teams, members, schedules, mindmaps, shares)
- **28개 핵심 페이지** (인증, 팀 관리, TODO, 스케줄, 마인드맵, 게시판)
- **Soft Delete 패턴** (회원 탈퇴, 계정 복구)

### Infrastructure
- **Docker Compose** (MySQL, Redis, Django, Nginx)
- **GitHub Actions CI/CD** (Test → Build → Deploy)
- **AWS EC2 프로덕션 배포** (t3.micro 프리티어)
- **HTTPS** (Let's Encrypt 자동 갱신)

### Testing
- **221개 테스트** (6개 앱 100% 커버리지)
- **pytest + fixture** (서비스 121개, API 43개, SSR 57개)
- **Given-When-Then** 패턴

### Key Features
- **실시간 마인드맵** (WebSocket + Canvas API, 5400×3600px)
- **스마트 스케줄** (JSON 168슬롯, 팀 가용성 자동 계산)
- **TODO 관리** (드래그 앤 드롭, Optimistic UI)
- **OAuth 2.0** (Google, GitHub 소셜 로그인)

### Achievements
- ✅ **CI/CD 완전 자동화** (git push → 5분 내 배포 완료)
- ✅ **Dynamic Security Group** (배포 시에만 SSH 포트 개방)
- ✅ **221개 테스트** (회귀 버그 방지, 리팩토링 안정성)
- ✅ **N+1 쿼리 해결** (select_related, prefetch_related)

---

## 📚 포트폴리오 문서 구성

| 문서 | 페이지 | 핵심 내용 | 추천 대상 |
|------|--------|----------|----------|
| [프로젝트 개요](./overview.md) | 8p | 프로젝트 배경, 4대 핵심 기능, 기술 스택 선택 이유 | **필독** (전체 흐름 파악) |
| [아키텍처 설계](./architecture.md) | 10p | 서비스 레이어 패턴, API vs SSR 전략, DB 설계 | 백엔드 아키텍처 관심자 |
| [인프라 및 배포](./infrastructure.md) | 12p | Docker, CI/CD, AWS EC2, Nginx + SSL | DevOps/인프라 관심자 |
| [테스트 전략](./testing.md) | 12p | 221개 테스트 구축 과정, pytest fixture 패턴 | 테스트 전략 관심자 |
| [트러블슈팅](./troubleshooting.md) | 12p | 15건 이상 문제 해결 사례 (HTTPS, N+1, WebSocket) | 실전 경험 확인 |
| [실시간 마인드맵](./features/realtime-mindmap.md) | 13p | Canvas API, WebSocket, 커서 공유 (50ms 스로틀링) | 실시간 협업 기능 상세 |

**총 분량**: 67페이지 (A4 기준) | **코드 예시**: 100개 이상 | **코드 검증**: 100% 완료

---

## 🎯 문서 읽는 추천 순서

### 1. 빠른 이해
1. **[프로젝트 개요](./overview.md)** (8페이지)
   - 프로젝트 배경 및 핵심 기능
   - 기술 스택 선택 이유
   - 주요 성과

### 2. 기술 깊이 확인
2. **[아키텍처 설계](./architecture.md)** (10페이지)
   - 서비스 레이어 패턴 도입 배경 (Before/After 코드)
   - API vs SSR 선택 기준
   - 쿼리 최적화 (N+1 해결)

3. **[인프라 및 배포](./infrastructure.md)** (12페이지)
   - Docker 멀티 스테이지 빌드
   - GitHub Actions CI/CD 파이프라인
   - Dynamic Security Group

### 3. 실전 경험 확인
4. **[테스트 전략](./testing.md)** (12페이지)
   - 221개 테스트 구축 과정
   - fixture 패턴 및 재사용

5. **[트러블슈팅](./troubleshooting.md)** (12페이지)
   - HTTPS 리디렉션 루프
   - username/email 영구 점유 문제
   - N+1 쿼리 최적화

### 4. 심화 기능
6. **[실시간 마인드맵](./features/realtime-mindmap.md)** (13페이지)
   - WebSocket 실시간 통신
   - Canvas API 좌표계 변환
   - 50ms 스로틀링 최적화

---

## 🔗 프로젝트 링크

### Live Demo
- **URL**: [https://teammoa.duckdns.org](https://teammoa.duckdns.org)
- **테스트 계정**: 회원가입 후 이메일 인증 필요 (Google/GitHub OAuth 가능)

### GitHub Repository
- **URL**: [https://github.com/TlesMes/TeamMoa-Refactor](https://github.com/TlesMes/TeamMoa-Refactor)
- **CI/CD**: GitHub Actions (자동 배포)
- **Docker Hub**: [tlesmes/teammoa-web](https://hub.docker.com/r/tlesmes/teammoa-web)


---

## 🎓 핵심 학습 포인트

### 아키텍처
- **서비스 레이어 패턴** - Fat View 문제 해결, 비즈니스 로직 분리
- **하이브리드 SSR+API** - 기능별 최적 렌더링 방식 선택

### Backend
- **Django Channels** - WebSocket 실시간 통신
- **ORM 최적화** - N+1 쿼리 해결 (select_related, prefetch_related)
- **트랜잭션 관리** - `@transaction.atomic` (원자성 보장)

### DevOps
- **Docker** - 멀티 스테이지 빌드, Health Check
- **CI/CD** - GitHub Actions 3-stage 파이프라인 (Test → Build → Deploy)
- **보안** - Dynamic Security Group, HTTPS 강제

### Testing
- **pytest** - fixture 패턴, 데이터 격리
- **DB 상태 기반 검증** - 구현 의존도 최소화
- **221개 테스트** - 회귀 버그 방지

---

## 📊 프로젝트 통계

### 코드 규모
- **6개 Django App** (accounts, teams, members, schedules, mindmaps, shares)
- **28개 핵심 페이지** (인증 10 + 팀 7 + 멤버 1 + 스케줄 2 + 마인드맵 8)
- **24개 REST API** + 3개 AJAX 엔드포인트
- **1개 WebSocket** (실시간 마인드맵)

### 테스트 커버리지
- **총 테스트**: 221개 (6개 앱 100% 커버리지)
- **서비스 레이어**: 121개 (55%)
- **API 테스트**: 43개 (19%)
- **SSR 테스트**: 57개 (26%)

### 인프라
- **AWS EC2**: t3.micro (프리티어, Ubuntu 22.04)
- **컨테이너**: 4개 (MySQL 8.0, Redis 7, Django, Nginx)
- **배포 시간**: 30분 → 5분 (CI/CD 자동화)
- **SSL**: Let's Encrypt (자동 갱신, crontab)

---

## 🚀 향후 계획

### 문서 개선
- [ ] ERD 다이어그램 추가 (dbdiagram.io)
- [ ] UI 스크린샷 추가 (주요 기능)
- [ ] 추가 기능 문서 작성 (OAuth 2.0, 성능 최적화)

### 기능 확장
- [ ] 마인드맵 버전 관리 (Git 스타일)
- [ ] TODO 우선순위 및 마감일 추가
- [ ] 팀 채팅 기능 (WebSocket)

### 성능 최적화
- [ ] N+1 쿼리 완전 제거 (django-debug-toolbar)
- [ ] Redis 캐싱 전략 구현
- [ ] 데이터베이스 인덱스 추가

---

**최종 업데이트**: 2025년 12월 5일
**버전**: 2.0
