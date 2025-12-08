# 회원 탈퇴 기능 구현 계획서

**작성일**: 2025-11-23
**목적**: User 모델의 CASCADE 문제 해결 및 안전한 회원 탈퇴 기능 구현

---

## 📝 요약

### 핵심 변경사항
1. **ForeignKey CASCADE → SET_NULL** (3개 모델)
   - `Team.host`: 팀장 탈퇴 시 자동 승계 (가장 오래된 멤버)
   - `Comment.user`: 댓글 유지, 작성자만 NULL
   - `Todo.assignee`: 미할당 보드로 자동 이동

2. **Soft Delete 방식**
   - `User.is_active=False` + 개인정보 익명화
   - 게시글/댓글은 "탈퇴한 사용자"로 표시 유지

3. **팀장 권한 관리**
   - 자동 승계: 탈퇴 시 가장 오래된 팀원에게 자동 이전
   - 수동 양도: 팀장이 직접 권한 양도 기능 추가

4. **탈퇴 사용자 표시**
   - 계정 탈퇴 + 팀 탈퇴 + Hard Delete 모두 처리
   - `User.get_display_name_in_team()` 클래스 메서드
   - 템플릿 필터로 None-safe 처리

### 구현 범위
- **모델 변경**: 3개 (Team, Comment, Todo)
- **새 기능**: 회원 탈퇴, 팀장 양도
- **UI 수정**: 6개 페이지 (팀 메인, 댓글, 게시판, TODO, 회원 탈퇴)
- **서비스 메서드**: 4개 (탈퇴, 자동 승계, 수동 양도, 사용자 표시)

---

## 📋 목차

1. [모델 수정사항](#1-모델-수정사항)
2. [로직 변경사항](#2-로직-변경사항)
3. [UI 변경사항](#3-ui-변경사항)
4. [마이그레이션 계획](#4-마이그레이션-계획)
5. [테스트 전략](#5-테스트-전략)

---

## 1. 모델 수정사항

### 1.1 Team 모델 (`teams/models.py`)

#### **현재 코드**:
```python
class Team(models.Model):
    host = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
```

#### **변경 후**:
```python
class Team(models.Model):
    host = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_teams',
        help_text='팀 호스트 (탈퇴 시 NULL)'
    )
```

#### **변경 이유**:
- ❌ **현재 문제**: User 삭제 시 팀 전체가 CASCADE 삭제됨
- ✅ **해결**: User 삭제 시 `host=NULL`로 변경, 팀은 유지됨
- ✅ **효과**: 다른 팀원들의 데이터(마일스톤, 마인드맵, 게시판) 보존

#### **영향도**:
- 🔴 **High**: 핵심 비즈니스 로직 변경
- 📝 **필수 후속 작업**:
  - 호스트 없는 팀 처리 로직 추가
  - 팀 권한 검증 로직 수정

---

### 1.2 Comment 모델 (`mindmaps/models.py`)

#### **현재 코드**:
```python
class Comment(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
```

#### **변경 후**:
```python
class Comment(models.Model):
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mindmap_comments',
        help_text='댓글 작성자 (탈퇴 시 NULL)'
    )
```

#### **변경 이유**:
- ❌ **현재 문제**: User 삭제 시 마인드맵 댓글 전체 삭제
- ✅ **해결**: 댓글 내용은 유지, 작성자만 NULL로 변경
- ✅ **효과**: 토론 히스토리 보존, 팀 지식 자산 유지
- ✅ **None-safe**: User hard delete 시 자동으로 `user=None`으로 설정됨

#### **영향도**:
- 🟡 **Medium**: 템플릿 수정 필요
- 📝 **필수 후속 작업**: 템플릿에서 `User.get_display_name_in_team()` 사용

---

### 1.3 Todo 모델 (`members/models.py`)

#### **현재 코드**:
```python
class Todo(models.Model):
    assignee = models.ForeignKey(
        'teams.TeamUser',
        on_delete=models.CASCADE,  # ❌ 문제
        null=True,
        blank=True,
        related_name='todo_set'
    )
```

#### **변경 후**:
```python
class Todo(models.Model):
    assignee = models.ForeignKey(
        'teams.TeamUser',
        on_delete=models.SET_NULL,  # ✅ 변경
        null=True,
        blank=True,
        related_name='todo_set',
        help_text='TODO 담당자 (탈퇴 시 NULL, 미할당 상태로 변경)'
    )
```

#### **변경 이유**:
- ❌ **현재 문제**: TeamUser 삭제 시 TODO 항목 삭제
- ✅ **해결**: TODO는 유지, 담당자만 NULL(미할당)로 변경
- ✅ **효과**: 팀의 작업 히스토리 보존

#### **영향도**:
- 🟢 **Low**: 이미 `null=True`로 설정되어 있어 변경 최소화
- 📝 **필수 후속 작업**: UI에서 "미할당" 상태 표시

---

### 1.4 유지되는 모델 (변경 불필요)

#### **TeamUser** (`teams/models.py`)
```python
class TeamUser(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)  # ✅ 유지
```
**이유**: 멤버십은 User와 생명주기를 함께 하므로 CASCADE 유지 적절

#### **PersonalDaySchedule** (`schedules/models.py`)
```python
class PersonalDaySchedule(models.Model):
    owner = models.ForeignKey('teams.TeamUser', on_delete=models.CASCADE)  # ✅ 유지
```
**이유**: 개인 스케줄은 멤버십과 함께 삭제되어야 함 (다른 사용자에게 영향 없음)

#### **Post** (`shares/models.py`)
```python
class Post(models.Model):
    writer = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)  # ✅ 이미 안전
```
**이유**: 이미 `SET_NULL`로 설정되어 있어 변경 불필요

---

## 2. 로직 변경사항

> **💡 설계 결정**: 팀 호스트 처리 방식
> - **검토한 방안**: A안(host=NULL 유지) vs B안(자동 승계)
> - **채택**: **B안 + 팀장 수동 양도 기능 추가**
> - **이유**: 코드 복잡도 최소화, 명확한 책임 체계 유지, 사용자 경험 일관성
> - **결과**: `team.host`는 항상 유효한 값을 가지므로 NULL 체크 로직 불필요

### 2.1 팀 호스트 자동 승계 로직 (B안)

**새로 추가**: `accounts/services.py` - `AuthService._transfer_team_ownership()`

```python
def _transfer_team_ownership(self, user):
    """
    사용자가 소유한 팀의 호스트 권한을 다른 멤버에게 자동 이전

    전략:
    1. 가장 오래된 멤버에게 자동 승계 (TeamUser.id 오름차순)
    2. 멤버가 없으면 팀 삭제
    """
    from teams.models import Team, TeamUser

    owned_teams = Team.objects.filter(host=user)

    for team in owned_teams:
        # 다음 호스트 후보 찾기 (자신 제외, 가입일 순)
        next_host_membership = TeamUser.objects.filter(team=team)\
                                               .exclude(user=user)\
                                               .order_by('id')\
                                               .first()

        if next_host_membership:
            # 호스트 자동 승계
            team.host = next_host_membership.user
            team.save()

            # TODO: 새 호스트에게 알림 전송 (선택사항)
            # self._notify_new_host(next_host_membership.user, team)
        else:
            # 혼자인 팀은 삭제
            team.delete()
```

---

### 2.2 팀 호스트 수동 양도 기능 (추가 기능)

**새로 추가**: `teams/services.py` - `TeamService.transfer_host()`

```python
@transaction.atomic
def transfer_host(self, team_id, current_host, new_host_user_id):
    """
    팀 호스트 권한을 다른 팀원에게 양도합니다.

    Args:
        team_id: 팀 ID
        current_host: 현재 호스트 (권한 검증용)
        new_host_user_id: 새 호스트가 될 User ID

    Returns:
        Team: 업데이트된 팀 객체

    Raises:
        ValueError: 권한 없음, 대상이 팀원 아님 등
    """
    from teams.models import Team, TeamUser
    from accounts.models import User

    # 팀 조회
    team = get_object_or_404(Team, pk=team_id)

    # 권한 검증: 현재 호스트만 양도 가능
    if team.host != current_host:
        raise ValueError('팀장만 권한을 양도할 수 있습니다.')

    # 새 호스트 조회
    new_host = get_object_or_404(User, pk=new_host_user_id)

    # 새 호스트가 팀 멤버인지 확인
    if not TeamUser.objects.filter(team=team, user=new_host).exists():
        raise ValueError('팀 멤버에게만 권한을 양도할 수 있습니다.')

    # 자기 자신에게 양도 방지
    if team.host == new_host:
        raise ValueError('이미 팀장입니다.')

    # 호스트 변경
    old_host = team.host
    team.host = new_host
    team.save()

    # TODO: 알림 전송 (선택사항)
    # - 새 호스트에게: "'{팀명}'의 새 팀장이 되었습니다."
    # - 기존 호스트에게: "팀장 권한이 양도되었습니다."

    return team
```

---

### 2.3 탈퇴 사용자 표시 로직 (신규)

**새로 추가**: `accounts/models.py` - `User.get_display_name_in_team()` 클래스 메서드

```python
class User(AbstractUser):
    # ... 기존 필드들 ...

    @classmethod
    def get_display_name_in_team(cls, user_or_none, team):
        """
        팀 컨텍스트에서 사용자 이름을 안전하게 반환 (None-safe)

        Args:
            user_or_none: User 인스턴스 또는 None (hard delete된 경우)
            team: Team 인스턴스

        Returns:
            str: 표시할 이름

        처리 케이스:
        1. user=None (hard delete, SET_NULL 결과) → "탈퇴한 사용자"
        2. user.is_active=False (계정 비활성화) → "탈퇴한 사용자"
        3. TeamUser 없음 (팀 탈퇴) → "탈퇴한 사용자"
        4. 정상 → user.nickname
        """
        from teams.models import TeamUser

        # 1. None 체크 (hard delete 또는 SET_NULL)
        if user_or_none is None:
            return "탈퇴한 사용자"

        # 2. 계정 비활성화 체크
        if not user_or_none.is_active:
            return "탈퇴한 사용자"

        # 3. 팀 탈퇴 체크
        if not TeamUser.objects.filter(team=team, user=user_or_none).exists():
            return "탈퇴한 사용자"

        return user_or_none.nickname
```

**Template Filter**: `accounts/templatetags/user_filters.py`

```python
from django import template
from accounts.models import User

register = template.Library()

@register.simple_tag
def user_display_name(user, team):
    """User.get_display_name_in_team()을 템플릿에서 사용"""
    return User.get_display_name_in_team(user, team)
```

**적용 범위**:
- ✅ 공유 게시판 (Post.writer)
- ✅ 마인드맵 댓글 (Comment.user)
- ✅ 3가지 케이스 모두 처리 (hard delete, 계정 탈퇴, 팀 탈퇴)

---

### 2.4 회원 탈퇴 핵심 로직

#### **새로 추가**: `accounts/services.py` - `AuthService.deactivate_user()`

```python
@transaction.atomic
def deactivate_user(self, user, password=None):
    """
    사용자 계정을 비활성화합니다 (Soft Delete).

    처리 순서:
    1. 비밀번호 확인 (소셜 로그인 전용 계정은 생략)
    2. 팀 소유권 이전
    3. 개인정보 익명화
    4. 멤버십 해제 (TeamUser 삭제)
    5. 소셜 계정 연결 해제
    6. 계정 비활성화

    Args:
        user: 비활성화할 사용자
        password: 비밀번호 (확인용, 소셜 전용 계정은 None)

    Returns:
        User: 비활성화된 사용자 객체

    Raises:
        ValueError: 비밀번호 불일치 등
    """
    from teams.models import TeamUser
    from allauth.socialaccount.models import SocialAccount
    from allauth.account.models import EmailAddress

    # 1. 비밀번호 확인 (사용 가능한 비밀번호가 있을 경우만)
    if user.has_usable_password():
        if not password:
            raise ValueError('비밀번호를 입력해주세요.')
        if not user.check_password(password):
            raise ValueError('비밀번호가 올바르지 않습니다.')

    # 2. 팀 소유권 이전 (CASCADE 방지)
    self._transfer_team_ownership(user)

    # 3. 개인정보 익명화
    user.username = f"deleted_user_{user.id}"
    user.email = None  # unique 제약 고려
    user.nickname = "탈퇴한 사용자"
    user.profile = ""
    user.set_unusable_password()
    user.is_active = False
    user.save()

    # 4. 멤버십 해제 (TODO의 assignee는 SET_NULL로 자동 처리됨)
    TeamUser.objects.filter(user=user).delete()

    # 5. 소셜 계정 연결 해제
    SocialAccount.objects.filter(user=user).delete()
    EmailAddress.objects.filter(user=user).delete()

    return user
```

---

## 3. UI 변경사항

### 3.1 팀 메인 페이지 - 팀장 권한 양도 기능 추가 (`teams/templates/teams/team_main_page.html`)

#### **멤버 리스트에 "팀장 양도" 버튼 추가** (154번 줄 근처):

**현재 코드**:
```html
<div class="member-actions">
  {% if request.user == team.host %}
  <button class="remove-member-btn" data-user-id="{{ member.user.id }}"
          data-user-name="{{ member.user.nickname }}" title="추방">
    <i class="ri-user-unfollow-line"></i>
  </button>
  {% elif request.user == member.user %}
  <button class="leave-team-btn" data-user-id="{{ member.user.id }}" title="탈퇴">
    <i class="ri-logout-box-line"></i>
  </button>
  {% endif %}
  <span class="member-login">{{member.user.last_login|date:'Y-m-d, H:i:s'}}</span>
</div>
```

**변경 후**:
```html
<div class="member-actions">
  {% if request.user == team.host %}
  <!-- 팀장만 보이는 버튼들 -->
  <button class="transfer-host-btn" data-user-id="{{ member.user.id }}"
          data-user-name="{{ member.user.nickname }}" title="팀장 양도">
    <i class="ri-shield-user-line"></i>
  </button>
  <button class="remove-member-btn" data-user-id="{{ member.user.id }}"
          data-user-name="{{ member.user.nickname }}" title="추방">
    <i class="ri-user-unfollow-line"></i>
  </button>
  {% elif request.user == member.user %}
  <button class="leave-team-btn" data-user-id="{{ member.user.id }}" title="탈퇴">
    <i class="ri-logout-box-line"></i>
  </button>
  {% endif %}
  <span class="member-login">{{member.user.last_login|date:'Y-m-d, H:i:s'}}</span>
</div>
```

#### **CSS 추가** (`static/css/pages/teams/main.css`):
```css
/* 팀장 양도 버튼 */
.transfer-host-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  margin-right: 0.5rem;
}

.transfer-host-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.transfer-host-btn i {
  margin-right: 4px;
}
```

#### **JavaScript 이벤트 핸들러 추가** (`static/js/pages/team_main.js`):
```javascript
// 팀장 양도 버튼 이벤트
document.addEventListener('DOMContentLoaded', function() {
  const transferButtons = document.querySelectorAll('.transfer-host-btn');

  transferButtons.forEach(button => {
    button.addEventListener('click', async function() {
      const userId = this.dataset.userId;
      const userName = this.dataset.userName;
      const teamId = window.teamData.teamId;

      // 확인 모달
      const confirmed = await showConfirmModal(
        `정말 ${userName}님에게 팀장 권한을 양도하시겠습니까?\n\n` +
        `양도 후에는 되돌릴 수 없으며, ${userName}님이 새로운 팀장이 됩니다.`,
        '팀장 양도'
      );

      if (!confirmed) return;

      try {
        // API 호출
        const response = await apiClient.post(
          `/api/teams/${teamId}/transfer-host/`,
          { new_host_user_id: userId }
        );

        if (response.success) {
          showDjangoToast(`${userName}님에게 팀장 권한을 양도했습니다.`, 'success');

          // 페이지 새로고침 (권한 변경 반영)
          setTimeout(() => {
            window.location.reload();
          }, 1500);
        } else {
          showDjangoToast(response.message || '권한 양도에 실패했습니다.', 'error');
        }
      } catch (error) {
        console.error('팀장 양도 오류:', error);
        showDjangoToast('권한 양도 중 오류가 발생했습니다.', 'error');
      }
    });
  });
});
```

#### **API 엔드포인트 추가** (`teams/viewsets.py`):
```python
@action(detail=True, methods=['post'], url_path='transfer-host')
def transfer_host(self, request, pk=None):
    """
    팀 호스트 권한 양도 API

    POST /api/teams/{team_id}/transfer-host/
    Body: { "new_host_user_id": 123 }
    """
    team = self.get_object()
    new_host_user_id = request.data.get('new_host_user_id')

    if not new_host_user_id:
        return api_error_response(request, '새 팀장의 ID를 입력해주세요.')

    try:
        updated_team = self.team_service.transfer_host(
            team_id=team.id,
            current_host=request.user,
            new_host_user_id=new_host_user_id
        )

        # 새 팀장 정보
        new_host = updated_team.host

        return api_success_response(
            request,
            f'{new_host.nickname}님에게 팀장 권한을 양도했습니다.',
            data={
                'team_id': updated_team.id,
                'new_host': {
                    'id': new_host.id,
                    'nickname': new_host.nickname,
                    'username': new_host.username
                }
            }
        )

    except ValueError as e:
        return api_error_response(request, str(e), status_code=status.HTTP_403_FORBIDDEN)
```

---

### 3.2 노드 댓글 페이지 (`mindmaps/templates/mindmaps/node_detail_page.html`)

> **💡 참고**: 마인드맵 댓글도 shares와 동일하게 `User.get_display_name_in_team()` 메서드 사용
> - 3가지 케이스 모두 처리 (hard delete, 계정 탈퇴, 팀 탈퇴)

#### **현재 코드** (54-60번 줄):
```html
<div class="node-detail-comment-item">
  <div class="node-detail-comment-header">
    <span class="node-detail-comment-author">{{ comment.user.nickname }}</span>
    <span class="node-detail-comment-date">{{ comment.commented_at|date:'Y-m-d H:i' }}</span>
  </div>
  <p class="node-detail-comment-content">{{ comment.comment }}</p>
</div>
```

#### **변경 후**:
```html
{% load user_filters %}

<div class="node-detail-comment-item">
  <div class="node-detail-comment-header">
    <span class="node-detail-comment-author">
      {% user_display_name comment.user team %}
    </span>
    <span class="node-detail-comment-date">{{ comment.commented_at|date:'Y-m-d H:i' }}</span>
  </div>
  <p class="node-detail-comment-content">{{ comment.comment }}</p>
</div>
```

#### **CSS 추가** (선택사항):
```css
/* static/css/pages/mindmaps/node_detail.css */

/* 탈퇴한 사용자 스타일링 (선택사항) */
.node-detail-comment-author {
  color: #333;
}
```

---

### 3.3 공유 게시판 - 탈퇴 사용자 표시 (`shares/templates/shares/*.html`)

> **💡 참고**: shares 게시판의 Post 모델은 이미 `writer = ForeignKey(User, on_delete=SET_NULL)`로 안전합니다.
> - User hard delete 시 자동으로 `writer=None`으로 설정됨
> - 모델 메서드에서 None 체크로 3가지 케이스 모두 처리 (hard delete, 계정 탈퇴, 팀 탈퇴)

#### **User 모델에 클래스 메서드 추가** (`accounts/models.py`):

```python
class User(AbstractUser):
    # ... 기존 필드들 ...

    @classmethod
    def get_display_name_in_team(cls, user_or_none, team):
        """
        팀 컨텍스트에서 사용자 이름을 안전하게 반환 (None-safe)

        Args:
            user_or_none: User 인스턴스 또는 None (hard delete된 경우)
            team: Team 인스턴스

        Returns:
            str: 표시할 이름

        처리 케이스:
        1. user=None (hard delete, SET_NULL 결과) → "탈퇴한 사용자"
        2. user.is_active=False (계정 비활성화) → "탈퇴한 사용자"
        3. TeamUser 없음 (팀 탈퇴) → "탈퇴한 사용자"
        4. 정상 → user.nickname
        """
        from teams.models import TeamUser

        # 1. None 체크 (hard delete 또는 SET_NULL)
        if user_or_none is None:
            return "탈퇴한 사용자"

        # 2. 계정 비활성화 체크
        if not user_or_none.is_active:
            return "탈퇴한 사용자"

        # 3. 팀 탈퇴 체크
        if not TeamUser.objects.filter(team=team, user=user_or_none).exists():
            return "탈퇴한 사용자"

        return user_or_none.nickname
```

#### **Template Filter 생성** (`accounts/templatetags/user_filters.py`):

```python
from django import template
from accounts.models import User

register = template.Library()

@register.simple_tag
def user_display_name(user, team):
    """User.get_display_name_in_team()을 템플릿에서 사용"""
    return User.get_display_name_in_team(user, team)
```

#### **게시글 목록 페이지** (`post_list.html` 64, 78번 줄):

**현재 코드**:
```html
<!-- 고정 게시글 -->
<span class="post-author">{{ post.writer }}</span>

<!-- 일반 게시글 -->
<span class="post-author">{{ post.writer.nickname }}</span>
```

**변경 후**:
```html
{% load user_filters %}

<!-- 고정 게시글 -->
<span class="post-author">
  {% user_display_name post.writer team %}
</span>

<!-- 일반 게시글 -->
<span class="post-author">
  {% user_display_name post.writer team %}
</span>
```

#### **게시글 상세 페이지** (`post_detail.html` 20번 줄):

**현재 코드**:
```html
<span><i class="fas fa-user-edit"></i>&nbsp;작성자: {{ post.writer.nickname }}</span>
```

**변경 후**:
```html
{% load user_filters %}

<span>
  <i class="fas fa-user-edit"></i>&nbsp;작성자:
  {% user_display_name post.writer team %}
</span>
```

#### **CSS 추가** (`static/css/pages/shares/common.css`):

```css
/* 탈퇴한 사용자 스타일 (선택사항 - 텍스트만 표시되므로 추가 스타일링 불필요) */
.post-author {
  color: #333;
}
```

---

### 3.4 TODO 보드 - 이미 구현됨 ✅

> **💡 현재 상태**: TODO 미할당 보드는 이미 구현되어 있습니다.
> - 템플릿: `members/templates/members/team_members_page.html`
> - 로직: `assignee=NULL`인 TODO는 자동으로 "할 일 목록" 보드에 표시됨
> - **회원/팀 탈퇴 시**: `Todo.assignee` CASCADE → SET_NULL 변경으로 자동으로 미할당 보드로 이동

**추가 작업 불필요** - 모델 변경만으로 자동 처리됨

---

### 3.5 회원 탈퇴 페이지 (신규)

#### **템플릿**: `accounts/templates/accounts/deactivate_confirm.html`

```html
{% extends 'base_user.html' %}
{% load static %}

{% block title %}회원 탈퇴{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/pages/accounts/deactivate.css' %}" />
{% endblock %}

{% block contents %}
<section class="deactivate-page">
  <div class="deactivate-container">
    <div class="deactivate-header">
      <i class="ri-error-warning-line"></i>
      <h2>회원 탈퇴</h2>
    </div>

    <div class="deactivate-warnings">
      <h3>탈퇴 전 확인사항</h3>
      <ul>
        <li>
          <i class="ri-team-line"></i>
          <strong>소유한 팀</strong>: {{ owned_teams_count }}개
          {% if owned_teams_count > 0 %}
            <br>→ 다른 멤버에게 호스트 권한이 자동 이전됩니다.
          {% endif %}
        </li>
        <li>
          <i class="ri-chat-3-line"></i>
          <strong>작성한 댓글/게시글</strong>은 "탈퇴한 사용자"로 표시되어 유지됩니다.
        </li>
        <li>
          <i class="ri-account-circle-line"></i>
          <strong>개인정보</strong>는 즉시 삭제되며 복구할 수 없습니다.
        </li>
      </ul>
    </div>

    <form method="POST" action="{% url 'accounts:deactivate' %}" id="deactivate-form">
      {% csrf_token %}

      {% if user.has_usable_password %}
      <div class="form-group">
        <label for="password">비밀번호 확인</label>
        <input type="password" name="password" id="password" required
               placeholder="비밀번호를 입력하세요">
      </div>
      {% endif %}

      <div class="form-group checkbox-group">
        <label>
          <input type="checkbox" name="confirm" required>
          위 내용을 모두 확인했으며, 회원 탈퇴에 동의합니다.
        </label>
      </div>

      <div class="form-actions">
        <a href="{% url 'accounts:update' %}" class="btn btn-secondary">
          <i class="ri-arrow-left-line"></i>
          취소
        </a>
        <button type="submit" class="btn btn-danger">
          <i class="ri-logout-box-line"></i>
          탈퇴하기
        </button>
      </div>
    </form>
  </div>
</section>

<script>
document.getElementById('deactivate-form').addEventListener('submit', function(e) {
  if (!confirm('정말로 탈퇴하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
    e.preventDefault();
  }
});
</script>
{% endblock %}
```

#### **CSS**: `static/css/pages/accounts/deactivate.css`

```css
.deactivate-page {
  min-height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.deactivate-container {
  max-width: 600px;
  width: 100%;
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.deactivate-header {
  text-align: center;
  margin-bottom: 2rem;
}

.deactivate-header .ri-error-warning-line {
  font-size: 4rem;
  color: #dc3545;
  margin-bottom: 1rem;
}

.deactivate-warnings {
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.deactivate-warnings h3 {
  color: #856404;
  margin-bottom: 1rem;
}

.deactivate-warnings ul {
  list-style: none;
  padding: 0;
}

.deactivate-warnings li {
  margin-bottom: 1rem;
  padding-left: 2rem;
  position: relative;
}

.deactivate-warnings li i {
  position: absolute;
  left: 0;
  top: 2px;
  color: #856404;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}
```

---

### 3.6 프로필 수정 페이지에 탈퇴 버튼 추가

#### **템플릿**: `accounts/templates/accounts/update.html`

```html
<!-- 기존 폼 아래에 추가 -->
<div class="danger-zone">
  <h3>위험 영역</h3>
  <p>이 작업은 되돌릴 수 없습니다.</p>
  <a href="{% url 'accounts:deactivate' %}" class="btn btn-danger-outline">
    <i class="ri-user-unfollow-line"></i>
    회원 탈퇴
  </a>
</div>
```

---

## 4. 마이그레이션 계획

### 4.1 마이그레이션 파일 생성

```bash
# 로컬 환경에서 실행
python manage.py makemigrations teams mindmaps members

# 예상 생성 파일:
# - teams/migrations/0005_alter_team_host.py
# - mindmaps/migrations/0004_alter_comment_user.py
# - members/migrations/0003_alter_todo_assignee.py
```

### 4.2 마이그레이션 SQL 확인

```bash
# 실제 실행될 SQL 미리보기
python manage.py sqlmigrate teams 0005
python manage.py sqlmigrate mindmaps 0004
python manage.py sqlmigrate members 0003
```

**예상 SQL**:
```sql
-- teams
ALTER TABLE `teams_team`
MODIFY COLUMN `host_id` INT NULL;

-- mindmaps
ALTER TABLE `mindmaps_comment`
MODIFY COLUMN `user_id` INT NULL;

-- members
ALTER TABLE `members_todo`
MODIFY COLUMN `assignee_id` INT NULL;
```


---

## 5. 테스트 전략

### 5.1 단위 테스트 (Unit Tests)

#### **A. 모델 테스트**: `teams/tests/test_models.py`

```python
def test_team_host_can_be_null(self):
    """Team.host가 NULL이 될 수 있는지 확인"""
    team = Team.objects.create(
        title="호스트 없는 팀",
        maxuser=10,
        currentuser=0,
        invitecode="TEST123",
        teampasswd="test",
        introduction="테스트",
        host=None  # NULL 허용
    )
    team.refresh_from_db()
    assert team.host is None
```

#### **B. 서비스 레이어 테스트**: `accounts/tests/test_auth_service.py`

```python
@pytest.mark.django_db
class TestUserDeactivation:
    def test_deactivate_user_anonymizes_data(self, user):
        """사용자 비활성화 시 개인정보가 익명화되는지 확인"""
        service = AuthService()
        service.deactivate_user(user, password='testpass123')

        user.refresh_from_db()
        assert user.is_active == False
        assert user.username == f"deleted_user_{user.id}"
        assert user.email is None
        assert user.nickname == "탈퇴한 사용자"
        assert not user.has_usable_password()

    def test_team_ownership_transfer_on_deactivation(self, user, team, other_user):
        """팀 소유자 탈퇴 시 호스트가 이전되는지 확인"""
        # 팀 호스트 설정
        team.host = user
        team.save()

        # 다른 멤버 추가
        TeamUser.objects.create(team=team, user=other_user)

        # 호스트 탈퇴
        service = AuthService()
        service.deactivate_user(user, password='testpass123')

        # 호스트 이전 확인
        team.refresh_from_db()
        assert team.host == other_user

    def test_solo_team_deleted_on_owner_deactivation(self, user, team):
        """혼자인 팀의 호스트 탈퇴 시 팀이 삭제되는지 확인"""
        team.host = user
        team.save()
        team_id = team.id

        service = AuthService()
        service.deactivate_user(user, password='testpass123')

        # 팀 삭제 확인
        assert not Team.objects.filter(id=team_id).exists()
```

#### **C. 댓글 테스트**: `mindmaps/tests/test_comment_handling.py`

```python
@pytest.mark.django_db
def test_comment_preserved_after_user_deactivation(user, node):
    """사용자 탈퇴 후에도 댓글이 유지되는지 확인"""
    # 댓글 작성
    comment = Comment.objects.create(
        comment="테스트 댓글",
        node=node,
        user=user
    )

    # 사용자 탈퇴
    service = AuthService()
    service.deactivate_user(user, password='testpass123')

    # 댓글 유지 확인
    comment.refresh_from_db()
    assert comment.comment == "테스트 댓글"
    assert comment.user.is_active == False
    assert comment.author_display == "탈퇴한 사용자"
```

#### **D. 팀장 권한 양도 테스트**: `teams/tests/test_team_service.py`

```python
@pytest.mark.django_db
class TestHostTransfer:
    def test_transfer_host_to_team_member(self, user, other_user, team):
        """팀장이 팀원에게 권한을 양도할 수 있는지 확인"""
        # 초기 설정
        team.host = user
        team.save()
        TeamUser.objects.create(team=team, user=user)
        TeamUser.objects.create(team=team, user=other_user)

        # 권한 양도
        service = TeamService()
        updated_team = service.transfer_host(
            team_id=team.id,
            current_host=user,
            new_host_user_id=other_user.id
        )

        # 검증
        assert updated_team.host == other_user

    def test_transfer_host_requires_current_host(self, user, other_user, third_user, team):
        """팀장이 아닌 사람은 권한 양도를 할 수 없는지 확인"""
        team.host = user
        team.save()
        TeamUser.objects.create(team=team, user=user)
        TeamUser.objects.create(team=team, user=other_user)
        TeamUser.objects.create(team=team, user=third_user)

        # 팀장이 아닌 사람이 양도 시도
        service = TeamService()
        with pytest.raises(ValueError, match='팀장만 권한을 양도할 수 있습니다'):
            service.transfer_host(
                team_id=team.id,
                current_host=other_user,  # 팀장이 아님
                new_host_user_id=third_user.id
            )

    def test_transfer_host_requires_team_member(self, user, other_user, non_member, team):
        """팀 멤버가 아닌 사람에게는 권한 양도 불가"""
        team.host = user
        team.save()
        TeamUser.objects.create(team=team, user=user)

        service = TeamService()
        with pytest.raises(ValueError, match='팀 멤버에게만 권한을 양도할 수 있습니다'):
            service.transfer_host(
                team_id=team.id,
                current_host=user,
                new_host_user_id=non_member.id  # 팀 멤버 아님
            )

    def test_cannot_transfer_to_self(self, user, team):
        """자기 자신에게는 권한 양도 불가"""
        team.host = user
        team.save()
        TeamUser.objects.create(team=team, user=user)

        service = TeamService()
        with pytest.raises(ValueError, match='이미 팀장입니다'):
            service.transfer_host(
                team_id=team.id,
                current_host=user,
                new_host_user_id=user.id  # 자기 자신
            )
```

---

### 5.2 통합 테스트 (Integration Tests)

#### **시나리오 1: 팀 호스트 탈퇴 전체 플로우**

```python
@pytest.mark.django_db
class TestTeamHostDeactivationFlow:
    def test_full_deactivation_flow(self, authenticated_client, team, user, other_user):
        """팀 호스트 탈퇴 전체 플로우 테스트"""
        # 1. 마일스톤 생성
        milestone = Milestone.objects.create(
            team=team,
            title="테스트 마일스톤",
            startdate=date.today(),
            enddate=date.today() + timedelta(days=7)
        )

        # 2. 다른 멤버 추가
        TeamUser.objects.create(team=team, user=other_user)

        # 3. 호스트 탈퇴 요청
        response = authenticated_client.post(reverse('accounts:deactivate'), {
            'password': 'testpass123',
            'confirm': 'on'
        })

        # 4. 검증
        assert response.status_code == 302  # 리다이렉트

        # 팀 유지 확인
        team.refresh_from_db()
        assert team.host == other_user  # 호스트 이전

        # 마일스톤 유지 확인
        assert Milestone.objects.filter(id=milestone.id).exists()

        # 사용자 비활성화 확인
        user.refresh_from_db()
        assert user.is_active == False
```

---

### 5.3 UI 테스트 체크리스트

#### **수동 테스트 시나리오**:

- [ ] **팀 메인 페이지 - 팀장 양도 기능** (신규)
  - [ ] 팀장에게만 "팀장 양도" 버튼이 보이는지 확인
  - [ ] 팀원에게는 버튼이 안 보이는지 확인
  - [ ] 버튼 클릭 시 확인 모달 표시 확인
  - [ ] 양도 성공 후 페이지 새로고침 확인
  - [ ] 양도 후 새 팀장에게 "팀장" 배지 표시 확인
  - [ ] 양도 후 이전 팀장은 일반 팀원으로 표시 확인

- [ ] **팀 호스트 자동 승계**
  - [ ] 팀장 탈퇴 시 가장 오래된 멤버가 자동 팀장 확인
  - [ ] 혼자인 팀의 팀장 탈퇴 시 팀 삭제 확인

- [ ] **노드 댓글 페이지**
  - [ ] 탈퇴한 사용자의 댓글에 "탈퇴한 사용자" 표시 확인
  - [ ] 댓글 스타일(회색, 이탤릭) 적용 확인

- [ ] **TODO 보드**
  - [ ] "미할당" 보드가 표시되는지 확인
  - [ ] 담당자 탈퇴 시 TODO가 미할당 보드로 이동하는지 확인

- [ ] **회원 탈퇴 페이지**
  - [ ] 소유 팀 개수 표시 확인
  - [ ] 비밀번호 확인 동작 확인
  - [ ] 확인 체크박스 필수 입력 확인
  - [ ] 탈퇴 후 로그아웃 및 리다이렉트 확인

---