# Shares 앱 CBV 전환 리팩토링 보고서

## 📋 개요
Shares 앱의 함수형 뷰(FBV)를 클래스 기반 뷰(CBV)로 전환하여 게시판 시스템의 안전성, 코드 일관성, 권한 관리를 크게 향상시켰습니다. 특히 페이지네이션 구조를 67% 간소화하고 새로운 PostAuthorRequiredMixin을 도입했습니다.

## 🔄 전환된 뷰 목록 (3개)

### 1. `post_write_view` → `PostWriteView`
**전환 유형**: TeamMemberRequiredMixin + TemplateView

```python
# AS-IS: 수동 권한 검사와 중복 코드
def post_write_view(request, pk):
    user = request.user
    if not user.is_authenticated:
        return redirect('/accounts/login')
    
    if request.method == "POST":
        user_id = User.objects.get(username=user.username)
        post = form.save(commit=False)
        post.writer = user_id
        post.isTeams_id = team_number

# TO-BE: 자동 권한 검사와 구조화된 처리
class PostWriteView(TeamMemberRequiredMixin, TemplateView):
    template_name = 'shares/post_write_renew.html'
    
    def post(self, request, pk):
        if form.is_valid():
            post = form.save(commit=False)
            post.writer = request.user  # 직접 사용
            post.isTeams_id = pk
```

**전환 이유**:
- **TeamMemberRequiredMixin**: 팀 멤버 권한 자동 검사
- **불필요한 User 조회 제거**: `request.user` 직접 사용
- **파일 업로드 로직 개선**: 안전한 파일 처리
- **GET/POST 분리**: 명확한 책임 분리

### 2. `post_edit_view` → `PostEditView`
**전환 유형**: PostAuthorRequiredMixin + TeamMemberRequiredMixin + TemplateView

```python
# AS-IS: 중복된 권한 검사와 객체 조회
def post_edit_view(request, pk, post_id):
    post = Post.objects.get(id=post_id)
    if request.method == "POST":
        # 권한 검사 없음
        form = PostWriteForm(request.POST, instance=post)
    else:
        post = Post.objects.get(id=post_id)  # 중복 조회!
        if post.writer == request.user or request.user.level == '0':
            # 권한 검사
        else:
            messages.error(request, "본인 게시글이 아닙니다.")

# TO-BE: Mixin을 통한 자동 권한 관리
class PostEditView(PostAuthorRequiredMixin, TeamMemberRequiredMixin, TemplateView):
    def get_objects(self):
        if not hasattr(self, '_objects'):
            self._objects = {
                'post': get_object_or_404(Post, id=self.kwargs['post_id']),
                'team': get_object_or_404(Team, pk=self.kwargs['pk'])
            }
        return self._objects
```

**전환 이유**:
- **PostAuthorRequiredMixin**: 게시글 작성자 권한 자동 검사
- **객체 조회 최적화**: 중복 조회 제거 및 캐싱
- **안전한 객체 조회**: `get_object_or_404()` 적용
- **권한 검사 자동화**: 중복 권한 검사 코드 완전 제거

### 3. `post_delete_view` → `PostDeleteView`
**전환 유형**: PostAuthorRequiredMixin + TeamMemberRequiredMixin + View

```python
# AS-IS: 수동 권한 검사와 중복 로직
def post_delete_view(request, pk, post_id):
    post = Post.objects.get(id=post_id)
    if post.writer == request.user or request.user.level == '0':
        post.delete()
        messages.success(request, "삭제되었습니다.")
    else:
        messages.error(request, "본인 게시글이 아닙니다.")

# TO-BE: 자동 권한 관리와 간소화된 로직
class PostDeleteView(PostAuthorRequiredMixin, TeamMemberRequiredMixin, View):
    def get(self, request, pk, post_id):
        post = get_object_or_404(Post, id=post_id)
        post.delete()
        messages.success(request, "삭제되었습니다.")
        return redirect(POST_LIST_PAGE, post.isTeams_id)
```

**전환 이유**:
- **권한 검사 완전 자동화**: Mixin에서 모든 권한 검사 처리
- **안전한 삭제**: `get_object_or_404()`로 존재하지 않는 게시글 처리
- **코드 간소화**: 권한 검사 로직 제거로 핵심 로직만 유지

## 🔧 PostListView 최적화

### **페이지네이션 구조 대폭 간소화**

```python
# AS-IS: 과도하게 복잡한 커스텀 페이지네이션 (20줄)
def get_context_data(self, **kwargs):
    paginator = context['paginator']
    page_numbers_range = 5
    max_index = len(paginator.page_range)
    page = self.request.GET.get('page')
    current_page = int(page) if page else 1
    start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
    end_index = start_index + page_numbers_range
    if end_index >= max_index:
        end_index = max_index
    page_range = paginator.page_range[start_index:end_index]
    # ... 복잡한 로직 계속

# TO-BE: Django ListView 기본 기능 활용 (6줄)
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    team = self.get_team()
    context.update({
        'team': team,
        'team_id': team.id
    })
    return context
```

**최적화 효과**:
- **코드 라인 67% 감소** (20줄 → 6줄)
- **Django 표준 페이지네이션 활용**: `paginate_by = 10`으로 자동 처리
- **템플릿에서 직접 사용 가능**: `{{ paginator }}`, `{{ page_obj }}`, `{{ is_paginated }}`
- **중복된 Team 조회 제거**: `get_team()` 메서드로 캐싱

## 🏗️ 새로 도입된 Mixin 클래스

### `PostAuthorRequiredMixin`
```python
class PostAuthorRequiredMixin:
    """게시글 작성자 또는 관리자만 접근 가능한 Mixin"""
    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs.get('post_id'))
        if post.writer != request.user and request.user.level != '0':
            messages.error(request, "본인 게시글이 아닙니다.")
            return redirect(POST_LIST_PAGE, kwargs.get('pk'))
        return super().dispatch(request, *args, **kwargs)
```

**특징**:
- **게시글별 권한 검사**: 작성자 또는 관리자(level='0')만 접근
- **자동 리다이렉트**: 권한 없을 시 게시글 목록으로 안전한 이동
- **적용 뷰**: PostEditView, PostDeleteView (2개 뷰)

## ✨ 주요 개선 사항

### 1. **URL 하드코딩 완전 제거**
```python
# URL 패턴 상수 도입
LOGIN_PAGE = 'accounts:login'
POST_LIST_PAGE = 'shares:post_list'
POST_DETAIL_PAGE = 'shares:post_detail_view'
MAIN_PAGE = 'teams:main_page'

# 적용 예시
return redirect(POST_LIST_PAGE, pk)  # 기존: redirect(f'/shares/{pk}/')
```

**적용된 곳**: 8곳의 하드코딩된 URL을 상수로 변경

### 2. **안전한 객체 조회 전면 도입**
- **PostListView**: `Team.objects.get()` → `get_object_or_404()`
- **PostEditView**: `Post.objects.get()` → `get_object_or_404()`  
- **PostDeleteView**: `Post.objects.get()` → `get_object_or_404()`

**효과**: 존재하지 않는 객체 접근 시 500 에러 → 404 에러로 안전한 처리

### 3. **코드 품질 대폭 개선**
- **불필요한 print문 제거**: 3개의 디버그 print문 삭제
- **주석 처리된 코드 제거**: 6곳의 주석 코드 정리
- **import 중복 제거**: `django.shortcuts` 중복 import 정리
- **인덴테이션 통일**: 코드 스타일 일관성 확보

### 4. **권한 관리 시스템 완전 자동화**
- **수동 `is_authenticated` 검사 제거**: TeamMemberRequiredMixin으로 대체
- **게시글 작성자 권한 자동화**: PostAuthorRequiredMixin 도입
- **중복 권한 검사 코드 완전 제거**: DRY 원칙 준수

## 🔗 하위 호환성
모든 뷰는 기존 URL 패턴과 완전 호환:
```python
post_write_view = PostWriteView.as_view()
post_edit_view = PostEditView.as_view()
post_delete_view = PostDeleteView.as_view()
```

## 📊 전환 결과
- **전환된 뷰**: 3개 (100%)
- **새로 도입된 Mixin**: 1개 (PostAuthorRequiredMixin)
- **기존 활용 Mixin**: 1개 (TeamMemberRequiredMixin)
- **하드코딩된 URL 제거**: 8곳 → 0곳
- **페이지네이션 코드 간소화**: 67% 라인 감소
- **안전한 객체 조회**: `get_object_or_404()` 6곳 적용
- **코드 품질 개선**: print문, 주석, 중복 import 완전 정리

## 💡 비즈니스 가치

### 1. **게시판 시스템의 완성도**
- 팀 기반 게시글 작성, 수정, 삭제의 완전한 권한 관리
- 파일 업로드/다운로드를 포함한 풍부한 게시판 기능
- 안전하고 직관적인 페이지네이션 시스템

### 2. **보안과 안전성**
- 게시글 작성자 권한의 엄격한 관리
- 존재하지 않는 객체에 대한 안전한 404 처리
- 팀 멤버 권한 기반의 접근 제어

### 3. **확장성과 유지보수성**
- PostAuthorRequiredMixin을 통한 재사용 가능한 권한 관리
- Django 표준 페이지네이션 활용으로 향후 커스터마이징 용이
- CBV 구조로 기능 확장과 오버라이드 편의성 확보

### 4. **개발자 경험**
- URL 상수화로 변경사항에 대한 안전한 관리
- 복잡한 페이지네이션 로직 제거로 코드 이해도 향상
- Django 모범 사례를 따른 일관된 코드 구조

Shares 앱은 이제 팀 기반 게시판 시스템으로서 보안, 사용성, 확장성을 모두 갖춘 완전한 도구가 되었습니다. 특히 권한 관리 자동화와 페이지네이션 간소화를 통해 개발자와 사용자 모두에게 우수한 경험을 제공합니다.