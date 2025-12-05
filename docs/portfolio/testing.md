# 테스트 전략

> **221개 테스트로 6개 앱 전체 검증**
>
> 서비스 레이어 우선 전략, fixture 기반 재사용성, DB 상태 검증으로 안정성 확보

---

## 목차
- [1. 테스트 개요](#1-테스트-개요)
- [2. 테스트 범위 / 커버리지](#2-테스트-범위--커버리지)
- [3. 테스트 전략](#3-테스트-전략)
- [4. 테스트 구조](#4-테스트-구조)
- [5. 테스트 구현 방식](#5-테스트-구현-방식)
- [6. Fixture 패턴](#6-fixture-패턴)
- [7. 학습 내용](#7-학습-내용)

---

## 1. 테스트 개요

### 왜 테스트를 도입했는가?

**배경**:
- Django 프로젝트에서 **비즈니스 로직 신뢰성 확보** 필요
- API + SSR 하이브리드 구조에서 **일관된 검증 전략** 요구
- 리팩토링 및 기능 추가 시 **회귀 버그 방지**

**목표**:
- ✅ 6개 앱의 **핵심 비즈니스 로직** 검증
- ✅ 28개 페이지, 24개 REST API **동작 보장**
- ✅ 리팩토링 시 **안전망** 제공

### 테스트 규모

```
총 221개 테스트
├─ 서비스 레이어: 121개 (55%)
├─ SSR: 57개 (26%)
└─ API: 43개 (19%)
```


---

## 2. 테스트 범위 / 커버리지

### 앱별 테스트 분포

| 앱 | 테스트 수 | 서비스 | API | SSR | 주요 검증 항목 |
|---|---------|--------|-----|-----|-------------|
| **Teams** | 66개 | 39개 | 12개 | 15개 | 팀 생성/가입/해체, 마일스톤 CRUD |
| **Schedules** | 34개 | 12개 | 13개 | 9개 | 주간 스케줄, 팀 가용성 계산 |
| **Members** | 33개 | 20개 | 10개 | 3개 | TODO 드래그앤드롭, 상태 변경 |
| **Mindmaps** | 31개 | 16개 | 8개 | 7개 | 노드/연결선 CRUD, 실시간 협업 |
| **Shares** | 29개 | 16개 | - | 13개 | 게시판 CRUD, 검색, 파일 처리 |
| **Accounts** | 28개 | 18개 | - | 10개 | 회원가입, 이메일 인증, 회원 탈퇴 |
| **총계** | **221개** | **121개** | **43개** | **57개** | - |

### 왜 221개인가?

**테스트 필요성 판단 기준**:

1. **서비스 레이어 (121개)** - 각 기능당 2-4개 테스트
   - 성공 케이스 (1개)
   - 실패/예외 케이스 (1-2개)
   - 권한/경계값 검증 (1개)
   - 예시: 팀 생성 → 성공, 중복명 실패, 호스트 권한, 최대 인원 초과

2. **API (43개)** - 실제 사용 중인 엔드포인트만
   - 프론트엔드에서 호출하는 API만 선별
   - HTTP 상태 코드, 권한, JSON 형식 검증
   - 미사용 CRUD API 제외로 테스트 최소화

3. **SSR (57개)** - 28개 페이지의 핵심 흐름
   - GET: 템플릿 렌더링, 컨텍스트 검증
   - POST: Form 제출, 리다이렉트, DB 변경
   - 각 페이지당 평균 2개 테스트 (GET + POST)

**결과**: 비즈니스 로직 신뢰성 확보 + 유지보수 가능한 범위

### 테스트 우선순위

1. **서비스 레이어 (55%)** - 비즈니스 로직 중심 검증
   - API/SSR 모두 서비스를 사용하므로 우선 검증
   - HTTP 의존성 없이 독립적으로 테스트

2. **SSR 뷰 (26%)** - 템플릿 렌더링, Form 처리
   - Django TestClient로 실제 페이지 동작 확인

3. **API (19%)** - REST API 엔드포인트
   - DRF TestClient로 JSON 응답 검증
   - **실제 사용 중인 API만** 테스트 (미사용 API 제외)

---

## 3. 테스트 전략

### 핵심 원칙

#### 1. 서비스 레이어 우선 테스트

**이유**: API/SSR 모두 서비스를 사용하므로, 한 번의 테스트로 양쪽 검증

```
[ API ViewSet ] ─┐
                 ├-→ [ Service Layer ] ← 테스트 집중
[ SSR View ]    ─┘
```

**장점**:
- 비즈니스 로직을 HTTP와 독립적으로 검증
- API/SSR 리팩토링 시에도 테스트 유지
- 테스트 중복 최소화

#### 2. Given-When-Then 패턴

**이유**: 테스트 가독성 및 의도 명확화

```python
def test_create_team(user):
    # Given: 초기 상태 설정
    team_data = {'title': '테스트팀', 'maxuser': 10}

    # When: 동작 실행
    team = TeamService.create_team(user, team_data)

    # Then: 결과 검증
    assert team.host == user
```

#### 3. DB 상태 기반 검증

**이유**: 구현 의존도 최소화 (리팩토링에 강함)

**지양**:
```python
# Bad: 서비스 내부 동작 검증
assert TeamService.create_team.called_once()
```

**지향**:
```python
# Good: DB 상태 확인
assert Team.objects.filter(title='테스트팀').exists()
assert team.host == user
assert TeamUser.objects.filter(team=team, user=user).exists()
```

#### 4. 실제 사용 중인 API만 테스트

**이유**: 테스트 유지보수 비용 최소화

**원칙**: 프론트엔드에서 실제 호출하는 API만 테스트, 미사용 API는 제외

#### 5. Mock 사용 최소화

**원칙**: Django 테스트 환경의 트랜잭션 격리를 신뢰, 실제 DB 사용

**Mock을 사용하지 않는 이유**:
- 실제 DB 사용으로 **통합 테스트** 효과
- pytest-django의 `@pytest.mark.django_db`로 **자동 트랜잭션 롤백**
- 외부 의존성 최소 (이메일은 Django의 `mail.outbox` 사용)

**Mock을 사용하는 경우** (현재 0건):
- 외부 API 호출 (현재 없음)
- 결제 시스템 등 실제 비용 발생하는 서비스 (현재 없음)

---

## 4. 테스트 구조

### 테스트 파일 구조

```
teams/tests/
├── conftest.py                  # fixture 정의 (user, team, client 등)
├── test_team_service.py         # 팀 서비스 (23개)
├── test_milestone_service.py    # 마일스톤 서비스 (13개)
├── test_team_viewset.py         # 팀 API (17개)
└── test_team_views.py           # SSR 뷰 (13개)
```

### 구조를 이렇게 나눈 이유

**서비스 레이어 분리**:
- `test_team_service.py`: 팀 생성/가입/해체 로직
- `test_milestone_service.py`: 마일스톤 CRUD 로직
- **이유**: 서비스 책임별로 분리하여 유지보수성 향상

**API/SSR 분리**:
- `test_team_viewset.py`: DRF API 엔드포인트 테스트
- `test_team_views.py`: Django SSR 뷰 테스트
- **이유**: 클라이언트 타입(APIClient vs TestClient)이 다름

**conftest.py 역할**:
- 공통 fixture 정의 (user, team, authenticated_client 등)
- **이유**: 테스트 코드 중복 제거, 유지보수 집중화

### 테스트 계층 간 책임 분리

```
┌─────────────────────────────────────┐
│  SSR 테스트 (test_team_views.py)     │  → 템플릿, 리다이렉트, Form 검증
├─────────────────────────────────────┤
│  API 테스트 (test_team_viewset.py)   │  → JSON 응답, 상태 코드, 권한 검증
├─────────────────────────────────────┤
│  서비스 테스트 (test_*_service.py)    │  → 비즈니스 로직, DB 상태 검증
└─────────────────────────────────────┘
```

**검증 책임**:
- **서비스**: 비즈니스 로직, 예외 처리, DB 상태
- **API**: HTTP 상태 코드, JSON 형식, 권한
- **SSR**: 템플릿 렌더링, 컨텍스트, 리다이렉트

---

## 5. 테스트 구현 방식

### 5.1 서비스 레이어 테스트

**목적**: HTTP와 무관한 순수 비즈니스 로직 검증

**검증 방식**: DB 상태 직접 확인 (구현 의존도 최소화)

#### 예시: Given-When-Then 패턴

```python
@pytest.mark.django_db
def test_create_team_success(self, user):
    # Given: 초기 데이터 준비
    team_data = {'title': '테스트팀', 'maxuser': 10, ...}

    # When: 서비스 메서드 호출
    team = TeamService.create_team(user, team_data)

    # Then: DB 상태 검증
    assert team.host == user
    assert TeamUser.objects.filter(team=team, user=user).exists()
```

**핵심**: DB 상태 기반 검증으로 구현 변경에 강한 테스트

---

### 5.2 API 테스트

**목적**: REST API 엔드포인트의 HTTP 응답 검증

**검증 요소**: 상태 코드, JSON 구조, 권한, DB 변경

#### 예시: DRF APIClient 활용

```python
@pytest.mark.django_db
def test_create_milestone(self, authenticated_api_client, team):
    # Given
    url = f'/api/v1/teams/{team.pk}/milestones/'
    data = {'title': '1차 마일스톤', 'start_date': '2025-01-01', ...}

    # When
    response = authenticated_api_client.post(url, data, format='json')

    # Then: HTTP 응답 + DB 이중 검증
    assert response.status_code == status.HTTP_201_CREATED
    assert Milestone.objects.filter(title='1차 마일스톤').exists()
```

**핵심**: `authenticated_api_client` fixture로 인증 처리 자동화

---

### 5.3 SSR 뷰 테스트

**목적**: Django 템플릿 렌더링 및 Form 처리 검증

**검증 요소**: 템플릿 사용, 컨텍스트 데이터, 리다이렉트

#### 예시: Django TestClient 활용

```python
@pytest.mark.django_db
def test_team_create_post(self, authenticated_web_client, user):
    # Given
    data = {'title': '새 팀', 'maxuser': 10, ...}

    # When
    response = authenticated_web_client.post(reverse('teams:team_create'), data)

    # Then: 리다이렉트 + 템플릿 + DB 검증
    assert response.status_code == 302
    assert Team.objects.filter(title='새 팀', host=user).exists()
```

**핵심**: `authenticated_web_client` fixture로 세션 인증 자동화

---

## 6. Fixture 패턴

### Fixture 재사용으로 중복 코드 제거

**Before (fixture 없음)**:
```python
def test_something():
    user = User.objects.create_user(...)  # 매번 반복
    client = APIClient()
    client.force_authenticate(user=user)
    team = Team.objects.create(...)
    TeamUser.objects.create(...)

    response = client.get(...)  # 실제 테스트
    assert response.status_code == 200
```

**After (fixture 사용)**:
```python
def test_something(authenticated_api_client, team):
    response = authenticated_api_client.get(...)
    assert response.status_code == 200
```

**효과**: 설정 코드 제거, 테스트 의도 명확화

### Fixture 구조

**루트 conftest.py** - 공통 fixture
| Fixture | 역할 |
|---------|------|
| `user`, `another_user`, `third_user` | 테스트 사용자 |
| `team` | 기본 팀 (user가 호스트) |
| `authenticated_api_client` | 인증된 DRF 클라이언트 |
| `authenticated_web_client` | 인증된 Django 클라이언트 |

**각 앱별 conftest.py** - 앱 전용 fixture
- `teams/tests/conftest.py`: `milestone`, `team_with_members`, `full_team`
- `mindmaps/tests/conftest.py`: `create_mindmap()`, `create_node()` 헬퍼 함수
- `members/tests/conftest.py`: `todo`, `todo_with_assignee`
- 기타 앱들...

**관리**: 공통 fixture는 [루트](../../conftest.py), 앱 전용 fixture는 각 앱의 `tests/conftest.py`

### DB 자동 롤백 (pytest-django)

```python
@pytest.mark.django_db  # 각 테스트마다 자동 롤백
def test_create_team(user):
    TeamService.create_team(user, {...})
    # 테스트 종료 후 자동 롤백 → DB 초기 상태 복원
```

**효과**: 테스트 간 완전한 격리, DB 충돌 없음

---

## 7. 학습 내용

### 테스트 구축을 통해 얻은 점

#### 1. pytest 활용 능력

**학습한 내용**:
- **fixture** - 테스트 데이터 재사용 및 의존성 관리
- **mark** - 테스트 분류 (`@pytest.mark.django_db`, `@pytest.mark.slow`)
- **parametrize** - 여러 입력값으로 동일 테스트

**실무 적용**:
- fixture로 221개 테스트의 중복 코드 감소
- 테스트 실행 시간 최적화

#### 2. Django 테스트 도구 이해

**학습한 내용**:
- **TestClient vs APIClient** - SSR은 TestClient, API는 APIClient
- **인증 우회 메서드**
  - `force_login(user)`: TestClient 세션 로그인 스킵
  - `force_authenticate(user)`: APIClient 인증 스킵 (토큰/JWT 설정 불필요)
  - 효과: 매 테스트마다 로그인 API 호출 불필요 → 속도 향상
- **`refresh_from_db()`** - 다른 코드에서 수정한 객체의 최신 상태 조회
- **`mail.outbox`** - 이메일 전송 테스트 (실제 SMTP 서버 불필요)

**실무 적용**:
- API/SSR 하이브리드 구조에 적합한 테스트 전략 수립
- 이메일 인증 플로우를 Mock 없이 검증

#### 3. 서비스 레이어 구조 이해 향상

**학습한 내용**:
- 비즈니스 로직을 HTTP와 분리하는 이유
- 서비스 레이어를 먼저 테스트하면 API/SSR 동시 검증 가능
- DB 상태 기반 검증으로 구현 변경에 강한 테스트 작성

**실무 적용**:
- API/SSR 리팩토링 시 서비스 테스트만으로 안정성 보장
- 새 기능 추가 시 서비스 → API → SSR 순서로 개발

#### 4. 리팩토링 안정성 증가

**효과**:
- 서비스 레이어 리팩토링 시 **테스트 통과 여부로 즉시 검증**
- 코드 변경 후 **회귀 버그 조기 발견**
- 자신감 있는 코드 개선 가능

**사례**:
```bash
# 리팩토링 전
pytest -v  # 221 passed

# 서비스 로직 수정
# ...

# 리팩토링 후
pytest -v  # 219 passed, 2 failed ← 즉시 발견!
```

#### 5. 테스트 유지보수 경험

**학습한 내용**:
- **실제 사용 API만 테스트**: 미사용 API 테스트 제외로 유지보수 부담 감소
- **DB 상태 검증**: 서비스 구현 변경 시 테스트 수정 불필요
- **fixture 중앙 관리**: 공통 설정 변경 시 한 곳만 수정

**실무 적용**:
- 테스트 코드 유지보수 비용 최소화
- 새 팀원 온보딩 시 테스트로 빠른 이해 가능

#### 6. 테스트가 개발 방식에 준 영향

**변화**:
- **TDD 접근**: 복잡한 로직은 테스트 먼저 작성
- **코드 품질 향상**: 테스트 가능한 구조로 자연스럽게 설계
- **문서화 효과**: 테스트 코드가 사용 예시 역할

---

## 테스트 실행

```bash
# 전체 테스트 실행
pytest -v

# 특정 앱만
pytest teams/tests/ -v

# 특정 테스트만
pytest -k "test_create" -v

# 커버리지 확인
pytest --cov=. --cov-report=html
```

**실행 결과**:
```bash
============================== test session starts ===============================
collected 221 items

accounts/tests/test_auth_service.py::TestAuthService::test_register_user ✓
accounts/tests/test_auth_service.py::TestAuthService::test_activate_account ✓
... (221개 테스트)

============================== 221 passed in 134.2s ================================
```

---

**작성일**: 2025년 12월 4일
**버전**: 2.0
**테스트 실행**: `pytest -v`
**코드 위치**: 각 앱의 `tests/` 디렉토리
