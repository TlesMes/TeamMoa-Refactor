# Teams 앱 CBV 전환 리팩토링 보고서

## 📋 개요
Teams 앱의 모든 함수형 뷰(FBV)를 클래스 기반 뷰(CBV)로 전환하여 코드 재사용성과 유지보수성을 향상시켰습니다.

## 🔄 전환된 뷰 목록 (9개)

### 1. `main_page` → `MainPageView`
**전환 유형**: TemplateView
```python
# AS-IS: 조건부 템플릿 렌더링과 컨텍스트 처리
def main_page(request):
    if user.is_authenticated:
        # 로그인 상태 처리
    else:
        # 미로그인 상태 처리

# TO-BE: 동적 템플릿 선택과 깔끔한 컨텍스트 분리
class MainPageView(TemplateView):
    def get_template_names(self):
        # 로그인 상태에 따른 템플릿 동적 선택
```
**전환 이유**: 
- 로그인/미로그인에 따른 다른 템플릿 렌더링 로직을 명확히 분리
- `get_template_names()`, `get_context_data()` 메서드로 책임 분리

### 2. `team_create` → `TeamCreateView`
**전환 유형**: LoginRequiredMixin + FormView
```python
# AS-IS: 수동 POST/GET 처리와 폼 검증
def team_create(request):
    if request.method == 'POST':
        # 폼 처리 로직

# TO-BE: 자동 폼 처리와 로그인 검증
class TeamCreateView(LoginRequiredMixin, FormView):
    def form_valid(self, form):
        # 팀 생성 로직만 집중
```
**전환 이유**:
- LoginRequiredMixin으로 인증 검사 자동화
- form_valid() 메서드로 성공 시 로직만 집중
- Django messages 통합으로 사용자 피드백 개선

### 3. `team_search` → `TeamSearchView` 
**전환 유형**: LoginRequiredMixin + FormView
**전환 이유**:
- 초대코드 검증 실패 시 적절한 에러 메시지 제공
- try-catch로 예외 처리 개선

### 4. `team_join` → `TeamJoinView`
**전환 유형**: LoginRequiredMixin + FormView
```python
# AS-IS: JavaScript alert를 통한 에러 처리
return HttpResponse('<script>alert("팀 최대인원 초과.")</script>')

# TO-BE: Django messages를 통한 우아한 에러 처리  
messages.error(self.request, '팀 최대인원을 초과했습니다.')
```
**전환 이유**:
- 복잡한 비즈니스 로직 (중복 가입 검사, 인원 제한, 패스워드 검증)을 체계적으로 구조화
- JavaScript alert 제거하고 Django messages로 UX 개선

### 5. `team_main_page` → `TeamMainPageView`
**전환 유형**: TeamMemberRequiredMixin + DetailView
```python
# AS-IS: 수동 권한 검사 함수 호출
if not is_member(request, pk):
    return HttpResponse('<script>alert("팀원이 아닙니다.")</script>')

# TO-BE: Mixin을 통한 자동 권한 검사
class TeamMainPageView(TeamMemberRequiredMixin, DetailView):
    # 권한 검사는 Mixin에서 자동 처리
```
**전환 이유**:
- 커스텀 Mixin으로 권한 검사 재사용성 극대화
- DetailView로 객체 조회 로직 단순화
- 복잡한 오늘 일정 계산 로직을 get_context_data()로 분리

### 6. `team_info_change` → `TeamInfoChangeView`
**전환 유형**: TeamHostRequiredMixin + UpdateView
**전환 이유**:
- 팀장 권한 검사를 Mixin으로 재사용
- UpdateView로 수정 폼 로직 자동화
- 수정 성공 메시지 자동 표시

### 7. `team_add_devPhase` → `TeamAddDevPhaseView` 
**전환 유형**: TeamHostRequiredMixin + FormView
```python
# AS-IS: 복잡한 중첩 if문과 JavaScript alert
for p in devphases:
    if (p.startdate < start) & (p.enddate > start):
        return HttpResponse('<script>alert("개발 기간 중복.")</script>')

# TO-BE: 깔끔한 검증 로직과 Django messages
if (phase.startdate < start < phase.enddate or ...):
    messages.error(self.request, '개발 기간이 중복됩니다.')
```
**전환 이유**:
- 기간 중복 검증 로직 가독성 향상
- DevPhase.objects.create()로 객체 생성 단순화

### 8. `team_delete_devPhase` → `TeamDeleteDevPhaseView`
**전환 유형**: TeamHostRequiredMixin + DeleteView
**전환 이유**:
- DeleteView로 삭제 로직 표준화
- 삭제 성공 메시지 자동 처리

### 9. `team_disband` → `TeamDisbandView`
**전환 유형**: TeamHostRequiredMixin + DeleteView  
**전환 이유**:
- 팀 해체라는 중요한 액션에 대한 명확한 피드백

## 🏗️ 새로 도입된 Mixin 클래스

### `TeamMemberRequiredMixin`
- **목적**: 팀 멤버만 접근 가능한 뷰에서 재사용
- **적용 뷰**: team_main_page
- **장점**: 권한 검사 로직의 중복 제거

### `TeamHostRequiredMixin`  
- **목적**: 팀장만 접근 가능한 뷰에서 재사용
- **적용 뷰**: team_info_change, team_add_devPhase, team_delete_devPhase, team_disband
- **장점**: 팀장 권한 검사를 4개 뷰에서 재사용

## ✨ 주요 개선 사항

### 1. **에러 처리 혁신**
- JavaScript alert → Django messages 
- 사용자 친화적 에러 메시지
- 일관된 피드백 시스템

### 2. **코드 재사용성 극대화**
- 2개의 커스텀 Mixin으로 권한 검사 중복 제거
- LoginRequiredMixin으로 인증 검사 자동화

### 3. **책임 분리 명확화**
- dispatch(): 권한 검사
- get_context_data(): 템플릿 컨텍스트 준비  
- form_valid(): 성공 로직 처리
- get_success_url(): 리다이렉트 URL 결정

### 4. **유지보수성 향상**
- 각 뷰의 역할이 클래스명으로 명확히 표현
- 메서드별 책임이 명확히 구분
- 향후 기능 확장 시 메서드 오버라이드만으로 커스터마이징 가능

## 🔗 하위 호환성
모든 뷰는 기존 URL 패턴과 호환되도록 `as_view()` 함수 형태로도 제공:
```python
main_page = MainPageView.as_view()
team_create = TeamCreateView.as_view()
# ... 모든 뷰 동일 적용
```

## 📊 전환 결과
- **전환된 뷰**: 9개 (100%)
- **새로 도입된 Mixin**: 2개
- **제거된 JavaScript alert**: 8개
- **도입된 Django messages**: 8개
- **코드 가독성**: 크게 향상
- **재사용성**: 권한 검사 로직 완전 재사용화

이번 CBV 전환으로 Teams 앱은 Django의 모범사례를 따르는 현대적이고 유지보수하기 쉬운 코드베이스로 발전했습니다.