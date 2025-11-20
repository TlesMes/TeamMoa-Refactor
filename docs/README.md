# 📚 TeamMoa 프로젝트 문서

TeamMoa 팀 협업 플랫폼의 개발 과정, 아키텍처 설계, 그리고 리팩토링 기록을 체계적으로 관리합니다.

## 📂 문서 카테고리

### 🏗️ [아키텍처](architecture/)
시스템 설계 및 리팩토링 작업들을 기록합니다.

#### 📋 [CBV 마이그레이션](architecture/cbv_migration/)
함수형 뷰에서 클래스 기반 뷰로의 전환 기록
- ✅ [Accounts 앱](architecture/cbv_migration/accounts_cbv_refactor.md) - 인증 시스템 CBV 전환
- ✅ [Teams 앱](architecture/cbv_migration/teams_cbv_refactor.md) - 팀 관리 CBV 전환  
- ✅ [Members 앱](architecture/cbv_migration/members_cbv_refactor.md) - 멤버 관리 CBV 전환
- ✅ [Schedules 앱](architecture/cbv_migration/schedules_cbv_refactor.md) - 스케줄 관리 CBV 전환
- ✅ [Mindmaps 앱](architecture/cbv_migration/mindmaps_cbv_refactor.md) - 마인드맵 CBV 전환
- ✅ [Shares 앱](architecture/cbv_migration/shares_cbv_refactor.md) - 공유 게시판 CBV 전환

#### 🔧 [서비스 레이어](architecture/service_layer/)
비즈니스 로직 분리를 위한 서비스 레이어 도입
- ✅ [Accounts 서비스 레이어](architecture/service_layer/accounts_service_refactor.md) - 인증 로직 완전 분리
- ✅ [Teams 서비스 레이어](architecture/service_layer/teams_service_implementation.md) - 팀/마일스톤 관리 로직 분리
- ✅ [Members 서비스 레이어](architecture/service_layer/members_service_implementation.md) - Todo 관리 및 권한 체계 분리
- ✅ [Schedules 서비스 레이어](architecture/service_layer/schedules_service_implementation.md) - JSON 스케줄 계산 로직 분리
- ✅ [Mindmaps 서비스 레이어](architecture/service_layer/mindmaps_service_implementation.md) - 마인드맵 협업 및 추천 시스템 분리
- ✅ [Shares 서비스 레이어](architecture/service_layer/shares_service_implementation.md) - 게시판 및 파일 관리 로직 분리
- 📋 [서비스 레이어 가이드라인](architecture/service_layer/service_layer_guidelines.md) - 패턴 및 베스트 프랙티스
- 🔄 [마이그레이션 로드맵](architecture/service_layer/migration_roadmap.md) - 전체 앱 적용 계획 및 진행상황

#### 🗺️ [Mindmaps 실시간 협업 시스템](architecture/mindmaps/)
WebSocket 기반 실시간 마인드맵 협업 시스템 (2025.09.07 Phase 1 완료)
- ✅ [WebSocket 실시간 협업 리팩토링](architecture/mindmaps/websocket_realtime_refactor.md) - 전면적 UX 혁신 및 실시간 협업 구현
- 🏗️ [기술 아키텍처 가이드](architecture/mindmaps/technical_architecture_guide.md) - Django Channels + Canvas 통합 아키텍처
- 👥 [사용자 경험 개선 분석](architecture/mindmaps/ux_improvement_analysis.md) - 사용성 250% 향상 상세 분석

### ⚡ [성능 최적화](performance/)
시스템 성능 개선 작업들을 기록합니다.
- ✅ [DB 쿼리 최적화 보고서](performance/optimization_report.md) - N+1 쿼리 해결 및 성능 개선

### 🎨 [UI/UX 개선](ui_ux/)
사용자 인터페이스 및 경험 개선 작업들을 기록합니다.
- ✅ [모달 시스템 개선](ui_ux/modal_system_improvement.md) - 알림 및 확인 모달 시스템 구축
- ✅ [Members App API 기반 실시간 UI](ui_ux/members_realtime_ui.md) - API 호출 기반 실시간 TODO 관리 시스템

### 🔌 [API 레이어](api/)
Django REST Framework 기반 API 인프라 및 앱별 API 전환 작업
- ✅ [Milestone API 마이그레이션 보고서](api/milestone-api-migration-report.md) - Teams 앱 마일스톤 API 전환 완료

### 🎨 [CSS 모듈화](css_refactoring/)
테마별 CSS 파일에서 앱별 모듈화로 전환하여 성능과 유지보수성 개선
- ✅ [Teams 앱 CSS 모듈화](css_refactoring/teams_css_refactor.md) - timeline.css, main.css 분리
- ✅ [Schedules 앱 CSS 모듈화](css_refactoring/schedules_css_refactor.md) - light.css에서 분리
- ✅ [Mindmaps 앱 CSS 모듈화](css_refactoring/mindmaps_css_refactor.md) - light.css에서 분리
- ✅ [Members 앱 CSS 모듈화](css_refactoring/members_css_refactor.md) - 4개 파일에서 2개로 통합
- ✅ [Shares 앱 CSS 모듈화](css_refactoring/shares_css_refactor.md) - 4개 모듈로 분리
- ✅ [Accounts 앱 CSS 모듈화](css_refactoring/accounts_css_refactor.md) - dark.css에서 5개 모듈로 분리 + Header 컴포넌트

## 📊 프로젝트 진행상황

### 🎯 아키텍처 리팩토링 현황

| 항목 | 진행률 | 상태 | 비고 |
|------|--------|------|------|
| **CBV 전환** | 6/6 (100%) | ✅ 완료 | 모든 앱 전환 완료 |
| **서비스 레이어** | 6/6 (100%) | ✅ 완료 | 모든 앱 서비스 레이어 도입 완료 |
| **사용성 분석** | 6/6 (100%) | ✅ 완료 | 전체 앱 사용자 관점 분석 완료 |
| **실시간 협업 시스템** | 1/1 (100%) | ✅ 완료 | Mindmaps WebSocket 기반 협업 구현 |
| **성능 최적화** | 1/3 (33%) | 🔄 진행중 | DB 쿼리 최적화 완료 |
| **UI/UX 개선** | 4/4 (100%) | ✅ 완료 | 모달 시스템 + Mindmaps 현대화 + 노드 디자인 + Members API 기반 UI 완료 |
| **CSS 모듈화** | 6/6 (100%) | ✅ 완료 | 모든 앱 CSS 모듈화 + Header 컴포넌트 분리 완료 |
| **API 레이어 도입** | 4/4 (100%) | ✅ 완료 | 하이브리드 전략 완성 (동적 기능 API화, 정적 기능 SSR 유지) |
| **테스트 커버리지** | 6/6 (100%) | ✅ 완료 | 전체 6개 앱 테스트 완료 (207개 테스트) ✨ |
| **Docker 배포 환경** | 1/1 (100%) | ✅ 완료 | Docker + Docker Compose 개발/운영 환경 구축 완료 |
| **AWS EC2 프로덕션 배포** | 1/1 (100%) | ✅ 완료 | HTTPS 프로덕션 배포 완료 (2025.11.20) 🎉 |

### 📈 주요 성과 지표

#### CBV 전환 성과
- **뷰 함수 수**: 47개 → 0개 (100% 감소)
- **코드 재사용성**: 공통 Mixin 도입으로 중복 코드 70% 감소
- **유지보수성**: 표준화된 패턴으로 개발 효율성 향상

#### 서비스 레이어 도입 성과 (전체 완료)
- **총 서비스 메서드**: 59개 (Accounts: 11개, Teams: 14개, Members: 12개, Schedules: 3개, Mindmaps: 10개, Shares: 9개)
- **총 서비스 클래스**: 7개 (TeamService, MilestoneService 분리 포함)
- **뷰 복잡도 감소**: 평균 31% 감소 (전체 앱 기준)
- **비즈니스 로직 중앙화**: 권한 관리, 트랜잭션 보장, 데이터 검증, JSON 데이터 처리, 파일 관리 통합
- **테스트 용이성**: HTTP 의존성 제거로 독립적 단위 테스트 가능
- **코드 재사용성**: API, CLI, 테스트에서 동일 서비스 로직 활용

#### 테스트 커버리지 구축 성과 (2025.10.19~2025.10.22 완료) ✨
- **총 테스트 수**: 207개 (100%, 6/6 앱 완료)
- **테스트 완료 앱**:
  - Teams App: 66개 (서비스 36 + API 17 + SSR 13)
  - Members App: 33개 (서비스 20 + API 10 + SSR 3)
  - Schedules App: 30개 (서비스 15 + API 10 + SSR 5)
  - Shares App: 24개 (서비스 13 + SSR 11)
  - Accounts App: 24개 (서비스 14 + SSR 10)
  - Mindmaps App: 30개 (서비스 16 + API 8 + SSR 6)
- **테스트 품질**: pytest.mark.parametrize 활용(중복 제거), 독립적 fixture(factory 함수), scope 최적화(성능 개선), DB 상태 기반 검증
- **테스트 전략**: pytest + DRF TestClient, fixture 재사용(conftest.py), 서비스 레이어 우선 테스트, 통일된 클라이언트 fixture(`authenticated_api_client`, `authenticated_web_client`)

#### 사용성 분석 및 개선 성과 (2025.09.16 완료)
- **분석 대상**: 6개 앱 전체 사용자 경험 평가
- **기존 평가**: Members(8.0점) > Teams(7.5점) > Accounts(6.8점) > Shares(5.5점) > Schedules(4.8점) > **Mindmaps(2.0점)**
- **Mindmaps 개선**: **2.0점 → 8.5점** - WebSocket 실시간 협업 + 가상 캔버스 + 모던 UI로 전면 혁신
- **Schedules 개선**: **4.8점 → 7.5점** - 드래그 선택 + 빠른 선택 도구 6종 + API 기반 실시간 업데이트 완료

#### 마인드맵 시스템 현대화 성과 (2025.09.16 완료)
- **가상 캔버스 시스템**: 5400×3600 픽셀 제한된 작업 공간으로 사용성 개선
- **동적 그리드**: 팬/줌 시각적 피드백 시스템으로 직관적 조작
- **모던 노드 디자인**: 둥근 모서리, 그라데이션, 드롭 섀도우로 시각적 매력도 향상
- **실시간 협업**: WebSocket 기반 다중 사용자 동시 편집 지원
- **핵심 성과**: 수동 좌표 입력 → 드래그 앤 드롭, 실시간 멀티유저 협업 구현

#### 실시간 협업 시스템 성과 (2025.09.07 완료)
- **기술 스택**: Django Channels + WebSocket + Redis + Vanilla JavaScript
- **사용성 혁신**: 수동 좌표 입력 → 직관적 드래그 앤 드롭 (1000% 개선)
- **협업 효율**: 순차 작업 → 동시 편집 (5배 향상)
- **반응 속도**: 페이지 새로고침 → 50ms 실시간 동기화 (4000% 개선)
- **학습 곡선**: 40분 → 10분 (75% 단축)

#### 성능 최적화 성과
- **DB 쿼리 수**: 16개 → 3개 (81% 감소)
- **페이지 로딩 속도**: 2.1초 → 0.8초 (62% 개선)
- **메모리 사용량**: 45% 감소

#### CSS 모듈화 성과 (2025.09.25 완료)
- **모듈화된 앱**: 6개 앱 완료 (Teams, Schedules, Mindmaps, Members, Shares, Accounts)
- **총 CSS 파일**: 21개 모듈로 분리 (기존 테마 파일에서 앱별 분리)
- **CSS 코드 정리**: 1,300+ 줄 중복 제거 (light.css에서 527줄, dark.css에서 830줄 분리)
- **성능 개선**: 선택적 CSS 로딩으로 페이지별 CSS 크기 60-80% 감소
- **컴포넌트 시스템**: header.css, modal.css 공통 컴포넌트 분리로 재사용성 확보
- **유지보수성**: 앱별 독립적 CSS 관리로 개발 효율성 향상
- **테마 시스템**: light/dark 테마 기반 + 앱별 모듈 조합 아키텍처 구축

#### API 레이어 도입 성과 (2025.09.28~10.11 완료)
- **DRF 인프라**: Django REST Framework 3.15.2 + drf-spectacular 기반 Swagger 문서 자동 생성
- **API 전환 완료 앱 (4/4)**:
  - **Members API**: Todo CRUD 완전 API화, TodoDOMUtils 실시간 UI 시스템 구현
  - **Teams API**: Milestone CRUD API 전환, 타임라인 필터 및 인라인 생성 기능
  - **Schedules API**: 주간 스케줄 저장/조회, 팀 가용성 실시간 계산
  - **Mindmaps API**: 노드 CRUD, 연결선 CRUD, 드래그 이동, 실시간 협업, 노드 추천 (노드 상세는 SSR 유지)
- **SSR 유지 앱 (2개, 의도적)**: Accounts (폼 기반 인증), Shares (파일 업로드/다운로드)
- **공통 인증/권한**: IsTeamMember, IsTeamLeader 등 재사용 가능한 권한 클래스
- **표준화된 응답**: 일관된 JSON 응답 형식 및 예외 처리
- **서비스 레이어 통합**: 기존 서비스 레이어와 완벽 연동
- **하이브리드 전략 완성**: 동적 기능은 API, 정적 콘텐츠/파일 처리는 SSR 유지

#### Docker 배포 환경 구축 성과 (2025.10.23 완료)
- **컨테이너화**: MySQL 8.0 + Redis 7 + Django (Daphne) 3개 서비스 구성
- **멀티 스테이지 빌드**: 최적화된 Docker 이미지 (builder + runtime 분리)
- **개발 환경**: Volume mounting으로 코드 변경 시 실시간 반영
- **프로덕션 환경**: Nginx 리버스 프록시 + Gunicorn/Daphne ASGI 서버
- **Health Check**: 컨테이너 상태 자동 모니터링 (/health/ 엔드포인트)
- **자동화 스크립트**: entrypoint.sh로 DB 대기 + 마이그레이션 + 정적 파일 수집 자동화
- **환경 변수 통합**: 단일 .env 파일로 개발/프로덕션 환경 관리
- **WebSocket 지원**: Nginx에서 Mindmaps 실시간 협업 WebSocket 프록시 설정
- **배포 준비 완료**: docker-compose up -d 한 줄로 전체 환경 구축 가능

#### AWS EC2 프로덕션 배포 성과 (2025.11.18~11.20 완료) 🎉
- **인프라 구성**: AWS EC2 t3.micro (Ubuntu 22.04), Elastic IP `3.34.102.12`
- **Docker Hub 배포**: `tlesmes/teammoa-web:latest` 이미지 자동 배포
- **HTTPS 적용**: Let's Encrypt SSL 인증서 + DuckDNS (`teammoa.duckdns.org`)
- **SSL 자동 갱신**: crontab 기반 certbot 자동 갱신 설정
- **OAuth 인증**: Google, GitHub 소셜 로그인 HTTPS 콜백 완료
- **컨테이너 안정성**: 4개 컨테이너 모두 Healthy 상태 유지
  - `teammoa_db_prod` (MySQL 8.0) - ✅ Healthy
  - `teammoa_redis_prod` (Redis 7) - ✅ Healthy
  - `teammoa_web_prod` (Django + Daphne) - ✅ Healthy
  - `teammoa_nginx_prod` (Nginx 1.25 + SSL) - ✅ Healthy
- **Health Check 분리**:
  - `/nginx-health`: Nginx 인프라 상태 확인
  - `/health/`: Django 애플리케이션 상태 확인
- **보안 설정**: HTTPS 강제 리디렉션, Secure Cookie, CSRF 보호 활성화
- **주요 해결 이슈**:
  - HTTPS 리디렉션 루프 해결 (`SECURE_PROXY_SSL_HEADER`)
  - Docker 로그 디렉토리 권한 문제 해결
  - IPv6 localhost 이슈 해결 (`127.0.0.1` 명시)
  - Health check 엔드포인트 분리로 디버깅 용이성 향상

## 🎯 다음 목표

### ✅ 주요 완료 사항
- **서비스 레이어 도입**: 전체 6개 앱 서비스 레이어 도입 100% 완료 (2025.09.07)
- **사용성 분석**: 전체 앱 사용자 경험 평가 및 개선 우선순위 도출 완료 (2025.09.07)
- **🎉 Mindmaps 실시간 협업**: WebSocket 기반 드래그 앤 드롭 + 실시간 협업 구현 완료 (2025.09.07 Phase 1)
- **API 레이어 도입**: DRF 기반 하이브리드 전략 완성 (Members/Teams/Schedules/Mindmaps API 전환 완료, 2025.09.28~10.11)
- **모달 기반 생성 시스템**: Teams 마일스톤, Mindmaps 생성 페이지 → 모달 전환 (2025.09.30~10.03)
- **Members DONE 보드**: 완료된 할 일 아카이브 시스템 구현 (2025.09.30)

## 🔧 주요 개선 과제

### 🚨 긴급 개선 대상 (사용성 심각 문제)

#### 1. **✅ Mindmaps 앱 실시간 협업 완료** (2025.09.07)
**개선 완료 사항:**
- ✅ **WebSocket 실시간 협업** - Django Channels 기반 동시 편집 지원
- ✅ **직관적 드래그 앤 드롭** - 수동 좌표 입력 → 마우스 드래그로 노드 이동
- ✅ **무한 캔버스** - 줌/팬 기능으로 대규모 마인드맵 지원
- ✅ **멀티 커서** - 실시간 다중 사용자 위치 표시
- ✅ **자동 재연결** - WebSocket 연결 끊어짐 시 자동 복구
- ✅ **반응형 디자인** - 화면 크기별 자동 조정

**Phase 2 계획 (다음 단계):**
- [ ] **연결선 시각적 그리기** - 마우스로 노드 간 연결 생성
- [ ] **노드 인라인 편집** - 더블클릭으로 즉시 텍스트 편집
- [ ] **모바일 터치 최적화** - 터치 제스처 지원
- [ ] **실행취소/다시실행** - 편집 히스토리 관리

#### 2. **✅ Schedules 앱 UI/UX 개선 완료** (2025.09.28)
**개선 완료 사항:**
- ✅ **드래그 선택 시스템** - 마우스/터치 드래그로 연속 시간대 선택
- ✅ **빠른 선택 도구 6종** - 전체, 업무시간(9-18시), 저녁(18-22시), 평일, 주말 원클릭 선택
- ✅ **API 기반 실시간 업데이트** - REST API + scheduleApi 클라이언트 완성
- ✅ **모바일 터치 지원** - 터치 이벤트 완벽 대응

**추가 개선 여지:**
- [ ] **열 단위 선택** - 요일 헤더 클릭으로 해당 요일 전체 토글


### ⚠️ 중요 개선 대상

#### 3. **Shares 앱 현대화** (진행 중)
- [x] **검색 기능** - 제목/내용/작성자 검색 (Django Q 객체, 페이지네이션) 완료
- [x] **파일 드래그 앤 드롭** 업로드 - FileUploadHandler 클래스 구현 완료
- [ ] 댓글/대댓글 시스템 (보류)
- [ ] 리치 텍스트 에디터 (보류)

#### 4. **Accounts 앱 현대화** (진행 예정)
- [ ] **OAuth 소셜 로그인** - GitHub + Google (포트폴리오 목적)
- [ ] 비밀번호 재설정 기능 (보류)
- [ ] 프로필 이미지 업로드 (보류)
- [ ] 2단계 인증 옵션 (보류)

### 🔄 단기 목표 (1-2주)
1. ✅ **Mindmaps 연결선 화살표 개선** - 둥근 모서리 반영, 렌더링 순서 최적화 완료
2. ✅ **Shares 게시판 검색 기능** - 제목/내용/작성자 검색, Q 객체 활용 완료
3. ✅ **Shares 파일 업로드 개선** - 드래그 앤 드롭, 파일 미리보기 완료
4. ✅ **Schedules App 테스트 구축** - 서비스/API/SSR 30개 테스트 완료 (2025.10.20)
5. ✅ **Shares App 테스트 구축** - 서비스/SSR 24개 테스트 완료 (2025.10.20)
6. ✅ **Accounts App 테스트 구축** - 서비스/SSR 24개 테스트 완료 (2025.10.20)
7. ✅ **Mindmaps App 테스트 구축** - 서비스/API/SSR 30개 테스트 완료, 통일된 클라이언트 fixture 구조 적용 (2025.10.22)

### 🚀 장기 목표 (2-3개월)
1. **성능 모니터링 시스템** - 서비스별 성능 지표 추적 및 최적화
2. **CI/CD 파이프라인 구축** - 자동화된 테스트 및 배포 시스템
3. **프론트엔드 프레임워크 검토** - React/Vue 도입 가능성 평가

## 📝 기여 가이드

### 문서 작성 원칙
- **구체적 기록**: AS-IS/TO-BE 패턴으로 변경 사항 명확히 기술
- **성과 측정**: 정량적 지표(라인 수, 성능 등)로 개선 효과 입증
- **재사용 가능**: 다른 개발자가 참고할 수 있도록 일반화된 패턴 제시

### 새 문서 추가시
1. 해당 카테고리 디렉토리에 작성
2. 이 README의 목차에 링크 추가
3. 진행상황 표 업데이트

---

**💡 Tip**: 각 문서는 독립적으로 읽을 수 있도록 작성되었으나, 연관된 문서들을 함께 읽으면 전체적인 아키텍처 발전 과정을 더 잘 이해할 수 있습니다.

*최종 업데이트: 2025.11.20 - AWS EC2 HTTPS 프로덕션 배포 완료 🎉*