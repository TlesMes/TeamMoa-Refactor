# API 레이어 도입 필요성 및 변화 분석

## 📋 개요

TeamMoa 프로젝트에 Django REST Framework(DRF) 기반 API 레이어를 도입하여 기존 서버사이드 렌더링 방식을 API 기반 아키텍처로 전환하는 방안을 분석합니다.

---

## 🎯 API 레이어 도입 필요성

### 1. 현재 아키텍처의 한계

**기존 방식**: Django Templates + AJAX 혼재
- 일부 기능은 페이지 새로고침 (폼 제출)
- 일부 기능은 AJAX 요청 (실시간 기능)
- 일관성 없는 데이터 교환 방식
- 프론트엔드와 백엔드 강한 결합

### 2. 확장성 및 유지보수성
- **모바일 앱 개발 준비**: 동일한 API로 웹/모바일 대응
- **마이크로서비스 전환 가능**: 독립적인 API 서비스
- **프론트엔드 프레임워크 도입**: React/Vue.js 등 SPA 전환 준비
- **API 문서화**: 자동 문서 생성 및 팀 협업 개선

### 3. 성능 및 사용자 경험
- **부분 페이지 업데이트**: 전체 페이지 새로고침 제거
- **캐싱 최적화**: API 레벨 캐싱 전략
- **로딩 성능**: 필요한 데이터만 요청
- **오프라인 지원**: PWA 구현 가능

---

## 🔄 작동 흐름 변화 분석

### 현재 방식 (Django Templates + AJAX 혼재)

#### 1. 팀 생성 플로우
```
[사용자]
  ↓ POST /teams/create (폼 데이터)
[Django View]
  ↓ team_service.create_team()
[Service Layer]
  ↓ DB 조작
[Database]
  ↓ 성공/실패
[Django View]
  ↓ 전체 페이지 렌더링 (redirect)
[브라우저] 새 페이지 로드
```

#### 2. 마인드맵 실시간 협업 (현재 WebSocket)
```
[사용자] 노드 이동
  ↓ WebSocket 메시지
[Django Channels Consumer]
  ↓ mindmap_service.update_node()
[Service Layer]
  ↓ DB 업데이트 + 브로드캐스트
[모든 클라이언트] 실시간 업데이트
```

### 변경 후 방식 (DRF API + SPA)

#### 1. 팀 생성 플로우
```
[사용자]
  ↓ POST /api/v1/teams/ (JSON)
[DRF ViewSet]
  ↓ team_service.create_team()
[Service Layer]
  ↓ DB 조작 (변경 없음)
[Database]
  ↓ 성공/실패
[DRF Serializer]
  ↓ JSON 응답
[JavaScript Frontend]
  ↓ DOM 부분 업데이트
[브라우저] 페이지 새로고침 없음
```

#### 2. 마인드맵 실시간 협업 (WebSocket + REST API 혼합)
```
[사용자] 노드 이동
  ↓ WebSocket 메시지 (실시간)
[Django Channels Consumer]
  ↓ mindmap_service.update_node()
[Service Layer] (변경 없음)
  ↓ DB 업데이트 + 브로드캐스트
[모든 클라이언트] 실시간 업데이트

+ 추가로
[사용자] 마인드맵 목록 조회
  ↓ GET /api/v1/mindmaps/
[DRF ViewSet] JSON 응답
```

---

## 📊 구체적 변화 비교

### A. 데이터 흐름

| 현재 방식 | 변경 후 |
|-----------|---------|
| HTML 폼 → Django View → DB → HTML 페이지 | JSON → DRF API → DB → JSON 응답 |
| 전체 페이지 새로고침 | 부분 DOM 업데이트 |
| 서버사이드 렌더링 | 클라이언트사이드 렌더링 |

### B. 파일 업로드 (Shares 앱)

**현재**:
```python
# views.py
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = shares_service.create_post(...)
            return redirect('shares:post_detail', post.id)
    # HTML 폼 렌더링
```

**변경 후**:
```python
# api/views.py
class PostViewSet(viewsets.ModelViewSet):
    def create(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            post = shares_service.create_post(...)
            return Response(PostSerializer(post).data, status=201)
```

### C. 권한 관리

**현재**:
```python
# views.py - 데코레이터 방식
@login_required
@team_member_required
def team_detail(request, team_id):
    team = teams_service.get_team_details(team_id, request.user)
    return render(request, 'team_detail.html', {'team': team})
```

**변경 후**:
```python
# api/views.py - DRF 권한 클래스
class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsTeamMember]

    def retrieve(self, request, pk):
        team = teams_service.get_team_details(pk, request.user)
        return Response(TeamSerializer(team).data)
```

---

## 🛠 필요한 변경 사항

### 1. 백엔드 (Django)

#### 신규 구성 요소
- **DRF 설정 및 라우팅**
- **API ViewSets** (6개 앱 × 평균 3-4개 ViewSet)
- **Serializers** (모델별 직렬화)
- **API 권한 클래스** (기존 데코레이터 → DRF 권한)
- **API 문서화** (drf-spectacular)

#### 기존 유지
- **Service Layer** ✅ (변경 없음)
- **Models** ✅ (변경 없음)
- **WebSocket 협업** ✅ (변경 없음)
- **데이터베이스** ✅ (변경 없음)

### 2. 프론트엔드 (JavaScript)

#### 신규 구성 요소
- **API 클라이언트** (fetch/axios 기반)
- **상태 관리** (간단한 상태 매니저)
- **컴포넌트화** (재사용 가능한 JS 컴포넌트)
- **폼 처리** (JSON 전송)
- **에러 핸들링** (API 오류 처리)

#### 기존 유지
- **CSS 모듈** ✅ (변경 없음)
- **WebSocket 클라이언트** ✅ (변경 없음)
- **기본 HTML 구조** ✅ (점진적 개선)

---

## 📈 예상 효과

### 1. 개발 측면
- **API First 설계**: 명확한 데이터 계약
- **팀 협업 개선**: 백엔드/프론트엔드 독립 개발
- **코드 재사용**: 웹/모바일 동일 API 사용
- **테스트 용이성**: API 단위 테스트

### 2. 성능 측면
- **로딩 속도**: 부분 업데이트로 50-70% 개선 예상
- **네트워크 트래픽**: JSON으로 HTML 대비 60% 감소
- **캐싱**: API 레벨 캐싱으로 응답 속도 향상

### 3. 사용자 경험
- **즉시 피드백**: 페이지 새로고침 제거
- **오프라인 지원**: 로컬 캐시 활용
- **모바일 최적화**: 반응형 API 응답

---

## 🎯 마이그레이션 전략

### Phase 1: 기반 구축 (1주)
1. DRF 설정 및 기본 구조
2. 인증 API (accounts 앱)
3. 기본 CRUD API 1-2개 구현

### Phase 2: 핵심 기능 (2주)
1. Teams, Members API 구현
2. 기존 AJAX → API 전환
3. 프론트엔드 컴포넌트화

### Phase 3: 고급 기능 (1주)
1. 파일 업로드 API
2. 실시간 협업 API 통합
3. 성능 최적화 및 테스트

---

## ❓ 고려 사항

### 1. 장점
- ✅ **서비스 레이어 완성**으로 비즈니스 로직 재작성 불필요
- ✅ **점진적 마이그레이션** 가능 (페이지별 전환)
- ✅ **미래 확장성** 확보 (모바일, SPA)

### 2. 단점
- ⚠️ **JavaScript 복잡도 증가**
- ⚠️ **초기 개발 시간** 필요
- ⚠️ **SEO 고려** (일부 페이지)

### 3. 위험 요소
- **브라우저 호환성** (구형 브라우저)
- **디버깅 복잡성** 증가
- **보안 고려사항** (CORS, CSRF)

---

## 🤔 결론

**추천 여부**: ✅ **강력 추천**

**이유**:
1. **기반 작업 완료**: 서비스 레이어로 비즈니스 로직 분리 완료
2. **점진적 전환**: 기존 시스템 유지하며 단계별 적용 가능
3. **미래 지향성**: 모바일 앱, SPA 전환 등 확장성 확보
4. **성능 개선**: 사용자 경험 크게 향상

**현재 TeamMoa는 API 레이어 도입에 최적화된 상태**입니다.