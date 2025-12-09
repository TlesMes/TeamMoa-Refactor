# 🧪 TeamMoa 테스트 가이드

## 📊 테스트 개요

**총 테스트 수**: 221개
**테스트 프레임워크**: pytest + Django Test + DRF TestClient
**테스트 전략**: 서비스 레이어 우선 테스트 → API → SSR 뷰

---

## 🚀 테스트 실행 방법

### 로컬 환경
```bash
# 전체 테스트 실행
pytest

# 특정 앱 테스트
pytest teams/tests/ -v
pytest members/tests/ -v

# 특정 테스트 파일
pytest teams/tests/test_team_service.py -v

# 키워드 필터링
pytest -k "create" -v
```

### Docker 환경
```bash
# 전체 테스트 실행
docker exec teammoa_web pytest -v

# 특정 앱 테스트
docker exec teammoa_web pytest teams/tests/ -v

# 간단한 출력
docker exec teammoa_web pytest --tb=line
```

### 커버리지 확인
```bash
# 커버리지 리포트 생성
pytest --cov=. --cov-report=html

# 터미널에서 확인
pytest --cov=teams --cov-report=term-missing teams/tests/
```

---

## 📁 테스트 구조 및 분류

### 1️⃣ Accounts App (28개 테스트)

#### `test_auth_service.py` (18개) - 인증 비즈니스 로직
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestRegistrationAndEmail` | 5개 | 회원가입 및 이메일 인증 | 사용자 생성, 이메일 발송, 인증 처리, 토큰 검증 |
| `TestResendActivationAndRateLimiting` | 4개 | 재전송 제한 및 Rate Limiting | 재전송 제한 시간, 중복 요청 방지, 5분 Rate Limit |
| `TestAuthenticationAndLogin` | 3개 | 로그인 인증 로직 | 비밀번호 검증, 활성 계정 확인, 인증 실패 처리 |
| `TestSessionManagement` | 2개 | 세션 관리 | 이전 URL 저장, 외부 도메인 차단 (보안) |
| `TestUserDeactivation` | 4개 | 회원 탈퇴 (Soft Delete) | 개인정보 익명화, is_deleted 처리, 팀 멤버십 제거, 소셜 계정 처리 |

#### `test_auth_views.py` (10개) - 인증 SSR 뷰
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestSignupFlow` | 회원가입 페이지 및 플로우 | 폼 렌더링, 회원가입 처리, 리다이렉트 |
| `TestLoginLogoutFlow` | 로그인/로그아웃 플로우 | 로그인 처리, 로그아웃 처리, 세션 상태 |
| `TestProfileAndPasswordManagement` | 프로필 및 비밀번호 관리 | 프로필 수정, 비밀번호 변경 |

---

### 2️⃣ Teams App (66개 테스트)

#### `test_team_service.py` (25개) - 팀 비즈니스 로직
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestTeamServiceCreateTeam` | 5개 | 팀 생성 | 팀 데이터 생성, 호스트 설정, 초대 코드 생성, 유효성 검증 |
| `TestTeamServiceVerifyTeamCode` | 5개 | 팀 코드 검증 | 초대 코드 유효성, 중복 가입 방지, 정원 초과 체크 |
| `TestTeamServiceJoinTeam` | 5개 | 팀 가입 | 멤버 추가, 인원수 업데이트, 비밀번호 검증 |
| `TestTeamServiceGetUserTeams` | 2개 | 사용자 팀 조회 | 소속 팀 목록 반환, 빈 목록 처리 |
| `TestTeamServiceGetTeamStatistics` | 2개 | 팀 통계 계산 | 마일스톤 통계, 진행 상태 집계 |
| `TestTeamServiceDisbandTeam` | 2개 | 팀 해체 | 호스트 권한 확인, 팀 삭제 |
| `TestTeamServiceRemoveMember` | 4개 | 멤버 추방/탈퇴 | 호스트 추방 권한, 본인 탈퇴, 권한 검증 |

#### `test_milestone_service.py` (14개) - 마일스톤 비즈니스 로직
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestMilestoneServiceCreateMilestone` | 3개 | 마일스톤 생성 | 마일스톤 데이터 생성, 날짜 유효성 검증, 당일 마일스톤 허용 |
| `TestMilestoneServiceUpdateMilestone` | 7개 | 마일스톤 수정 | 시작일/종료일/진행률 수정, 진행률 100% 시 완료 처리, 날짜 범위 검증 |
| `TestMilestoneServiceDeleteMilestone` | 1개 | 마일스톤 삭제 | 마일스톤 삭제 처리 |
| `TestMilestoneServiceGetTeamMilestones` | 3개 | 팀 마일스톤 조회 | 우선순위 정렬, 종료일 정렬, 커스텀 정렬 |

#### `test_team_viewset.py` (3개) - 팀 API 엔드포인트
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestTeamViewSetRemoveMember` | 3개 | 멤버 추방/탈퇴 API | 호스트 추방, 본인 탈퇴, 권한 체크 |

#### `test_milestone_viewset.py` (9개) - 마일스톤 API 엔드포인트
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestMilestoneViewSet` | 9개 | 마일스톤 API | 목록 조회, 생성, 부분 수정, 삭제, 유효성 검증 |

#### `test_team_views.py` (15개) - 팀 SSR 뷰
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestTeamViews` | 15개 | 팀 SSR 페이지 | 메인, 생성, 검색, 코드 검증 AJAX, 가입 AJAX, 정보 수정, 해체 |

---

### 3️⃣ Members App (33개 테스트)

#### `test_todo_service.py` (20개) - TODO 비즈니스 로직
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestTodoServiceCreateTodo` | 2개 | TODO 생성 | 할 일 생성, 빈 내용 검증 |
| `TestTodoServiceAssignTodo` | 5개 | TODO 할당 | 호스트 할당, 본인 할당, 권한 체크, 순서 계산, 비팀원 할당 거부 |
| `TestTodoServiceCompleteTodo` | 3개 | TODO 완료 처리 | 완료 상태 변경, 완료 시간 기록, 권한 확인 |
| `TestTodoServiceMoveToTodo` | 3개 | DONE → TODO 복원 | 상태 롤백, 순서 재조정, 권한 확인 |
| `TestTodoServiceMoveToDone` | 3개 | TODO → DONE 이동 | 완료 처리, 순서 조정, 권한 확인 |
| `TestTodoServiceDeleteTodo` | 2개 | TODO 삭제 | 삭제 처리, 권한 확인 |
| `TestTodoServiceGetTeamTodosWithStats` | 2개 | 팀 TODO 조회 및 통계 | 목록 조회, 통계 계산 |

#### `test_todo_viewset.py` (10개) - TODO API 엔드포인트
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestTodoViewSetAssign` | TODO 할당 API | 담당자 변경 API |
| `TestTodoViewSetComplete` | TODO 완료 API | 완료 처리 API |
| `TestTodoViewSetMoveToTodo` | TODO 복원 API | 복원 처리 API |
| `TestTodoViewSetMoveToDone` | DONE 이동 API | 완료 이동 API |

#### `test_member_views.py` (3개) - 멤버 SSR 뷰
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestTeamMembersPageView` | 팀 멤버 페이지 | TODO 목록, 통계 표시 |

---

### 4️⃣ Schedules App (34개 테스트)

#### `test_schedule_service.py` (12개) - 스케줄 비즈니스 로직
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestScheduleService` | 12개 | 스케줄 CRUD 및 계산 | 개인 스케줄 저장, 덮어쓰기, 팀 가용성 계산, 날짜 범위 조회, 쿼리 최적화 |

#### `test_schedule_viewset.py` (13개) - 스케줄 API 엔드포인트
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestScheduleViewSet` | 13개 | 스케줄 API | 저장, 조회, 팀 가용성 API, 인증/권한, 날짜 유효성 검증 |

#### `test_schedule_views.py` (9개) - 스케줄 SSR 뷰
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestScheduleViews` | 9개 | 스케줄 페이지 | 조회 페이지, 업로드 페이지 GET/POST, 유효성 검증, 권한 체크 |

---

### 5️⃣ Shares App (33개 테스트)

#### `test_share_service.py` (20개) - 게시판 비즈니스 로직
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestPostCRUD` | 6개 | 게시글 CRUD | 파일 첨부/없이 생성, 대용량 파일 검증, 작성자 권한 수정, 파일 포함 삭제 |
| `TestSearchFunctionality` | 4개 | 검색 기능 | 제목/내용/작성자/전체 검색 (parametrize 활용) |
| `TestFileHandling` | 2개 | 파일 처리 | 파일 없을 때 다운로드 에러, 파일 정리 메서드 |
| `TestPermissionsAndRetrieval` | 4개 | 권한 및 조회 | 게시글 상세 조회, 작성자 확인, 팀 권한 체크 |
| `TestDeletedAuthorHandling` | 4개 | 탈퇴 작성자 처리 | 탈퇴 작성자 게시물 상세 조회, 권한 확인, 목록 포함, 팀 확인 |

#### `test_share_views.py` (13개) - 게시판 SSR 뷰
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestShareViews` | 13개 | 게시판 SSR 페이지 | 목록, 상세, 페이지네이션, 검색 필터링, 작성/수정 폼, 삭제, 파일 업로드, 권한 체크 |

---

### 6️⃣ Mindmaps App (31개 테스트)

#### `test_mindmap_service.py` (16개) - 마인드맵 비즈니스 로직
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestMindmapCRUD` | 4개 | 마인드맵 CRUD | 마인드맵 생성, 수정, 삭제, 중복 제목 검증 |
| `TestNodeCRUD` | 5개 | 노드 CRUD | 노드 생성, 이동, 삭제, 권한 검증 |
| `TestConnectionCRUD` | 4개 | 연결선 CRUD | 연결선 생성, 수정, 삭제, 권한 검증 |
| `TestCommentAndPermission` | 3개 | 댓글 및 권한 | 댓글 작성, 권한 검증 |

#### `test_mindmap_viewset.py` (8개) - 마인드맵 API 엔드포인트
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestNodeViewSet` | 5개 | 노드 API | 노드 CRUD, 드래그 이동, 권한 체크 |
| `TestConnectionViewSet` | 3개 | 연결선 API | 연결선 생성, 삭제, 권한 체크 |

#### `test_mindmap_views.py` (7개) - 마인드맵 SSR 뷰
| 테스트 클래스 | 테스트 수 | 테스트 목적 | 주요 검증 사항 |
|-------------|---------|-----------|-------------|
| `TestMindmapListAndCreate` | 2개 | 목록 및 생성 | 마인드맵 목록, 생성/중복 제목 처리 |
| `TestMindmapDelete` | 1개 | 마인드맵 삭제 | 호스트 전용 삭제 권한 |
| `TestMindmapEditor` | 2개 | 에디터 페이지 | Canvas 에디터 렌더링, 권한 체크 |
| `TestNodeDetail` | 2개 | 노드 상세 페이지 | 노드 상세 표시, 댓글 추가 |

---

## 🔧 테스트 설정

### pytest.ini
- **Django 설정 모듈**: `TeamMoa.settings.dev`
- **테스트 DB 재사용**: `--reuse-db` (빠른 실행)
- **자동 옵션**: `-v`, `--strict-markers`, `--tb=short`

### conftest.py 공통 Fixtures
**사용자 Fixtures**:
- `user` - 기본 테스트 사용자
- `another_user` - 권한 테스트용
- `third_user` - 다중 멤버 테스트용
- `team` - 기본 팀 (user가 호스트)

**클라이언트 Fixtures**:
- `authenticated_api_client` - 인증된 DRF API 클라이언트
- `authenticated_web_client` - 인증된 Django 웹 클라이언트

---

## 📈 테스트 전략

### 1. 서비스 레이어 우선 테스트
- 비즈니스 로직을 HTTP 의존성 없이 독립적으로 테스트
- DB 상태 기반 검증으로 구현 의존도 최소화

### 2. API 테스트
- DRF TestClient로 실제 HTTP 요청/응답 검증
- 권한, 상태 코드, JSON 응답 형식 확인

### 3. SSR 뷰 테스트
- Django TestClient로 템플릿 렌더링 검증
- 폼 처리, 리다이렉트, 컨텍스트 데이터 확인

### 4. Fixture 재사용
- `conftest.py`의 공통 fixture로 중복 제거
- pytest의 scope 최적화로 성능 개선

### 5. Parametrize 활용
- `pytest.mark.parametrize`로 유사한 테스트 케이스 통합
- 경계값, 예외 케이스 효율적 검증

---

## 🎯 테스트 작성 가이드라인

### DO ✅
- **독립적인 테스트**: 각 테스트는 순서에 무관하게 실행 가능해야 함
- **명확한 이름**: `test_create_team_success`, `test_join_team_with_invalid_code`
- **단일 책임**: 하나의 테스트는 하나의 기능만 검증
- **DB 상태 검증**: 서비스 메서드보다 DB 상태로 검증 (구현 의존도 감소)
- **pytest.mark.parametrize**: 여러 입력값 테스트 시 활용

### DON'T ❌
- **테스트 간 의존성**: 이전 테스트 결과에 의존하지 말 것
- **실제 외부 API 호출**: Mock 사용
- **하드코딩된 ID**: fixture로 동적 생성
- **너무 긴 테스트**: 여러 검증이 필요하면 분리

---

## 📊 테스트 현황 요약

| 앱 | 서비스 | API | SSR | 합계 |
|---|---------|-----|-----|------|
| Accounts | 18 | - | 10 | 28 |
| Teams | 39 | 12 | 15 | 66 |
| Members | 20 | 10 | 3 | 33 |
| Schedules | 12 | 13 | 9 | 34 |
| Shares | 20 | - | 13 | 33 |
| Mindmaps | 16 | 8 | 7 | 31 |
| **총계** | **125** | **43** | **57** | **225** |

---

*최종 업데이트: 2025.12.04*
