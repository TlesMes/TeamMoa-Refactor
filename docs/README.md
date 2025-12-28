# 📚 TeamMoa 프로젝트 문서

TeamMoa 팀 협업 플랫폼의 개발 과정, 아키텍처 설계, 그리고 리팩토링 기록을 체계적으로 관리합니다.

## 📂 문서 카테고리

### 📸 포트폴리오 - 외부 공개용

> **96페이지, 150+ 코드 예시** | 채용 담당자, 동료 개발자 대상

**핵심 문서**
- [프로젝트 개요](portfolio/overview.md) - 배경, 핵심 기능, 기술 스택 선택 이유 (8p)
- [아키텍처 설계](portfolio/architecture.md) - 서비스 레이어, API vs SSR 전략, DB 설계 (10p)
- [인프라 및 배포](portfolio/infrastructure.md) - Docker, CI/CD, AWS EC2, Nginx + SSL (12p)
- [테스트 전략](portfolio/testing.md) - 221개 테스트 구축 과정, pytest fixture 패턴 (12p)
- [트러블슈팅](portfolio/troubleshooting.md) - 8건 문제 해결 사례 (HTTPS, N+1, WebSocket) (12p)

**기능 상세**
- [실시간 마인드맵](portfolio/features/realtime-mindmap.md) - Canvas API, WebSocket, 커서 공유 (13p)
- [OAuth 2.0 인증](portfolio/features/oauth-authentication.md) - django-allauth, 계정 병합 (15p)
- [성능 최적화](portfolio/features/performance-optimization.md) - N+1 쿼리 해결, 81% 감소 (14p)

---

### 🏗️ 아키텍처 - 설계 & 리팩토링

> 시스템 구조 정의 + 개선 히스토리

**📐 설계 문서** (정적 구조)
- [API/SSR 매핑](architecture/design/api_ssr_mapping.md) - 24개 REST API, 34개 SSR 뷰, 1개 WebSocket
- [서비스 레이어 가이드라인](architecture/design/service_layer_guidelines.md) - 패턴 및 베스트 프랙티스
- [API 레이어 소개](architecture/design/api_layer_introduction.md) - DRF 하이브리드 전략
- [Mindmaps 아키텍처](architecture/design/mindmaps_architecture.md) - Django Channels + Canvas

**🔄 리팩토링 히스토리** 
- **CBV 마이그레이션**: [6개 앱 전환 기록](architecture/refactoring/cbv/) | [요약 보고서](architecture/refactoring/cbv/cbv_migration_summary.md)
- **서비스 레이어 도입**: [6개 앱 구현 기록](architecture/refactoring/service_layer/)
- **API 마이그레이션**: [Milestone](architecture/refactoring/api_migrations/milestone_api_migration.md) | [Scheduler](architecture/refactoring/api_migrations/scheduler_api_migration.md)
- **Mindmaps 리팩토링**: [WebSocket 협업](architecture/refactoring/mindmaps/websocket_realtime_refactor.md) | [노드 재설계](architecture/refactoring/mindmaps/redesign_plan.md) | [추천 시스템](architecture/refactoring/mindmaps/recommendation_refactor.md)

**🚀 로드맵**
- [마이그레이션 로드맵](architecture/migration/migration_roadmap.md) - 전체 앱 적용 계획 및 진행상황

---

### 📚 가이드 - 설정 & 사용법

> 실무 작업용 단계별 가이드

- [OAuth 설정](guides/oauth_setup_guide.md) - Google, GitHub OAuth 설정 방법
- [배포 가이드](guides/deployment_guide.md) - Docker 환경 구축, AWS EC2 배포
- [테스트 가이드](guides/testing_guide.md) - pytest 환경 설정, 테스트 작성

---

### 🔧 개발 문서 - 성능 & UI/UX & 기능

> 개선 작업 기록

**성능 최적화**
- [DB 쿼리 최적화](development/performance/optimization_report.md) - N+1 쿼리 해결

**UI/UX 개선**
- [모달 시스템](development/ui_ux/modal_system_improvement.md) - 알림 및 확인 모달
- [Members 실시간 UI](development/ui_ux/members_realtime_ui.md) - API 기반 TODO 관리
- [Mindmaps UX 분석](development/ui_ux/mindmaps_ux_improvement.md) - 사용성 분석
- [UI 현대화 보고서](development/ui_ux/ui_modernization_report.md) - 전체 UI 개선 종합

**기능 개발**
- [회원 탈퇴 계획](development/features/user_deactivation_plan.md) - Soft Delete, 자동 정리

---

### 🐛 트러블슈팅 - 문제 해결

> 프로덕션 배포 중 발생한 문제 해결 사례

- [Cron 환경 변수 문제](troubleshooting/cron_environment.md) - Django cron job 환경 변수 로드 실패

---

## 📊 프로젝트 진행 현황

| 항목 | 상태 | 완료일 |
|------|------|--------|
| **CBV 전환** | ✅ 완료 (6/6) | 2025.09.05 |
| **서비스 레이어** | ✅ 완료 (6/6) | 2025.09.07 |
| **실시간 협업** | ✅ 완료 (Mindmaps WebSocket) | 2025.09.07 |
| **CSS 모듈화** | ✅ 완료 (6/6) | 2025.09.25 |
| **API 레이어** | ✅ 완료 (4/4 하이브리드) | 2025.10.11 |
<!-- AUTO:TEST_COUNT -->
| **테스트 커버리지** | ✅ 완료 (262개 테스트) | 2025.10.22 |
| **Docker 배포** | ✅ 완료 | 2025.10.23 |
| **AWS EC2 배포** | ✅ 완료 (HTTPS) | 2025.11.20 |
| **CI/CD 파이프라인** | ✅ 완료 (GitHub Actions) | 2025.11.21 |
| **회원 탈퇴 개선** | ✅ 완료 (Soft Delete) | 2025.11.24 |
| **포트폴리오 문서** | ✅ 완료 (96p, 150+ 코드) | 2025.12.08 |
| **AWS ALB + Multi-AZ** | ✅ 완료 (고가용성, 부하 테스트) | 2025.12.16 |
| **UI 스크린샷** | ✅ 완료 (10개 이미지, GIF 포함) | 2025.12.23 |

---


## 📝 문서 작성 원칙

새 문서 추가 시:
1. 해당 카테고리 디렉토리에 작성
2. 이 README의 목차에 링크 추가
3. AS-IS/TO-BE 패턴으로 변경 사항 명확히 기술
4. 정량적 지표로 개선 효과 입증

---

**💡 Tip**: 각 문서는 독립적으로 읽을 수 있도록 작성되었으나, 연관된 문서들을 함께 읽으면 전체적인 아키텍처 발전 과정을 더 잘 이해할 수 있습니다.

*최종 업데이트: 2025.12.23 - UI 스크린샷 추가 완료 (10개 이미지, GIF 포함)*
