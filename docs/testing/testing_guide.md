# 🧪 TeamMoa 테스트 가이드

## 📊 테스트 개요

**총 테스트 수**: 207개
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

### 1️⃣ Accounts App (24개 테스트)

#### `test_auth_service.py` (14개) - 인증 비즈니스 로직
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestRegistrationAndEmail` | 회원가입 및 이메일 인증 | 사용자 생성, 이메일 발송, 인증 처리 |
| `TestResendActivationAndRateLimiting` | 재전송 제한 및 Rate Limiting | 재전송 제한 시간, 중복 요청 방지 |
| `TestAuthenticationAndLogin` | 로그인 인증 로직 | 비밀번호 검증, 활성 계정 확인 |
| `TestSessionManagement` | 세션 관리 | 로그아웃, 세션 만료 처리 |

#### `test_auth_views.py` (10개) - 인증 SSR 뷰
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestSignupFlow` | 회원가입 페이지 및 플로우 | 폼 렌더링, 회원가입 처리, 리다이렉트 |
| `TestLoginLogoutFlow` | 로그인/로그아웃 플로우 | 로그인 처리, 로그아웃 처리, 세션 상태 |
| `TestProfileAndPasswordManagement` | 프로필 및 비밀번호 관리 | 프로필 수정, 비밀번호 변경 |

---

### 2️⃣ Teams App (66개 테스트)

#### `test_team_service.py` (23개) - 팀 비즈니스 로직
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestTeamServiceCreateTeam` | 팀 생성 | 팀 데이터 생성, 호스트 설정, 초대 코드 생성 |
| `TestTeamServiceVerifyTeamCode` | 팀 코드 검증 | 초대 코드 유효성, 중복 가입 방지 |
| `TestTeamServiceJoinTeam` | 팀 가입 | 멤버 추가, 인원수 업데이트 |
| `TestTeamServiceGetUserTeams` | 사용자 팀 조회 | 소속 팀 목록 반환 |
| `TestTeamServiceGetTeamStatistics` | 팀 통계 계산 | 멤버 수, 마일스톤 수, 할 일 통계 |
| `TestTeamServiceDisbandTeam` | 팀 해체 | 호스트 권한 확인, 팀 삭제 |
| `TestTeamServiceRemoveMember` | 멤버 추방 | 리더 권한 확인, 멤버 제거 |

#### `test_milestone_service.py` (13개) - 마일스톤 비즈니스 로직
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestMilestoneServiceCreateMilestone` | 마일스톤 생성 | 마일스톤 데이터 생성, 팀 멤버 권한 확인 |
| `TestMilestoneServiceUpdateMilestone` | 마일스톤 수정 | 데이터 업데이트, 권한 검증 |
| `TestMilestoneServiceDeleteMilestone` | 마일스톤 삭제 | 삭제 처리, 권한 검증 |
| `TestMilestoneServiceGetTeamMilestones` | 팀 마일스톤 조회 | 목록 조회, 필터링, 정렬 |

#### `test_team_viewset.py` (17개) - 팀 API 엔드포인트
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestTeamViewSetRemoveMember` | 멤버 추방 API | API 응답, 권한 체크, 상태 코드 |

#### `test_milestone_viewset.py` (4개) - 마일스톤 API 엔드포인트
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestMilestoneViewSetList` | 마일스톤 목록 조회 API | 필터링, 정렬, JSON 응답 |
| `TestMilestoneViewSetCreate` | 마일스톤 생성 API | 데이터 검증, 생성 처리 |
| `TestMilestoneViewSetUpdate` | 마일스톤 수정 API | 부분 업데이트, 전체 업데이트 |
| `TestMilestoneViewSetDestroy` | 마일스톤 삭제 API | 삭제 처리, 204 응답 |

#### `test_team_views.py` (13개) - 팀 SSR 뷰
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestMainPageView` | 메인 페이지 | 팀 목록, 통계 표시 |
| `TestTeamCreateView` | 팀 생성 페이지 | 폼 렌더링, 팀 생성 처리 |
| `TestTeamSearchView` | 팀 검색 | 검색 결과, 페이지네이션 |
| `TestTeamVerifyCodeAjax` | 팀 코드 검증 AJAX | 비동기 코드 검증 |
| `TestTeamJoinProcessAjax` | 팀 가입 처리 AJAX | 비동기 가입 처리 |
| `TestTeamInfoChangeView` | 팀 정보 수정 | 팀 정보 업데이트 |
| `TestTeamDisbandView` | 팀 해체 | 팀 삭제 처리 |

---

### 3️⃣ Members App (33개 테스트)

#### `test_todo_service.py` (20개) - TODO 비즈니스 로직
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestTodoServiceCreateTodo` | TODO 생성 | 할 일 생성, 순서 설정 |
| `TestTodoServiceAssignTodo` | TODO 할당 | 담당자 지정, 권한 확인 |
| `TestTodoServiceCompleteTodo` | TODO 완료 처리 | 상태 변경, 완료 시간 기록 |
| `TestTodoServiceMoveToTodo` | DONE → TODO 복원 | 상태 롤백, 순서 재조정 |
| `TestTodoServiceMoveToDone` | TODO → DONE 이동 | 완료 처리, 순서 조정 |
| `TestTodoServiceDeleteTodo` | TODO 삭제 | 삭제 처리, 권한 확인 |
| `TestTodoServiceGetTeamTodosWithStats` | 팀 TODO 조회 및 통계 | 목록 조회, 통계 계산 |

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

### 4️⃣ Schedules App (30개 테스트)

#### `test_schedule_service.py` (15개) - 스케줄 비즈니스 로직
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestScheduleService` | 스케줄 CRUD 및 계산 | JSON 스케줄 저장, 팀 가용성 계산, 최적 시간대 추천 |

#### `test_schedule_viewset.py` (10개) - 스케줄 API 엔드포인트
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestScheduleViewSet` | 스케줄 API | 저장, 조회, 팀 가용성 API |

#### `test_schedule_views.py` (5개) - 스케줄 SSR 뷰
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestScheduleViews` | 스케줄 페이지 | 주간 스케줄 표시, UI 렌더링 |

---

### 5️⃣ Shares App (24개 테스트)

#### `test_share_service.py` (13개) - 게시판 비즈니스 로직
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestPostCRUD` | 게시글 CRUD | 생성, 조회, 수정, 삭제 |
| `TestSearchFunctionality` | 검색 기능 | 제목, 내용, 작성자 검색 |
| `TestFileHandling` | 파일 처리 | 업로드, 다운로드, 파일 관리 |
| `TestPermissionsAndRetrieval` | 권한 및 조회 | 팀 멤버 권한, 목록 조회 |

#### `test_share_views.py` (11개) - 게시판 SSR 뷰
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestPostListAndRetrieval` | 게시글 목록 및 상세 | 목록 페이지, 상세 페이지 |
| `TestSearchUI` | 검색 UI | 검색 결과 표시 |
| `TestPostWriteAndEdit` | 게시글 작성 및 수정 | 폼 렌더링, 작성/수정 처리 |
| `TestDeleteAndDownload` | 삭제 및 다운로드 | 삭제 처리, 파일 다운로드 |
| `TestPermissions` | 권한 검증 | 팀 멤버 전용 접근 제어 |

---

### 6️⃣ Mindmaps App (30개 테스트)

#### `test_mindmap_service.py` (16개) - 마인드맵 비즈니스 로직
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestMindmapCRUD` | 마인드맵 CRUD | 마인드맵 생성, 수정, 삭제 |
| `TestNodeCRUD` | 노드 CRUD | 노드 생성, 이동, 삭제 |
| `TestConnectionCRUD` | 연결선 CRUD | 연결선 생성, 수정, 삭제 |
| `TestCommentAndPermission` | 댓글 및 권한 | 댓글 작성, 권한 검증 |

#### `test_mindmap_viewset.py` (8개) - 마인드맵 API 엔드포인트
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestNodeViewSet` | 노드 API | 노드 CRUD, 드래그 이동 API |
| `TestConnectionViewSet` | 연결선 API | 연결선 CRUD API |

#### `test_mindmap_views.py` (6개) - 마인드맵 SSR 뷰
| 테스트 클래스 | 테스트 목적 | 주요 검증 사항 |
|-------------|-----------|-------------|
| `TestMindmapListAndCreate` | 마인드맵 목록 및 생성 | 목록 페이지, 생성 모달 |
| `TestMindmapDelete` | 마인드맵 삭제 | 삭제 처리 |
| `TestMindmapEditor` | 마인드맵 에디터 | Canvas 에디터 페이지 |
| `TestNodeDetail` | 노드 상세 페이지 | 노드 내용, 댓글 표시 |

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
| Accounts | 14 | - | 10 | 24 |
| Teams | 36 | 17 | 13 | 66 |
| Members | 20 | 10 | 3 | 33 |
| Schedules | 15 | 10 | 5 | 30 |
| Shares | 13 | - | 11 | 24 |
| Mindmaps | 16 | 8 | 6 | 30 |
| **총계** | **114** | **45** | **48** | **207** |

---

*최종 업데이트: 2025.10.23*
