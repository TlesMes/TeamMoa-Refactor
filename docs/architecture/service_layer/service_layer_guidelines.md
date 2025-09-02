# 🔧 TeamMoa 서비스 레이어 가이드라인

Django에서 서비스 레이어를 도입하여 비즈니스 로직을 뷰에서 분리하는 모범 사례와 패턴을 정의합니다.

## 📋 목차
- [기본 개념](#기본-개념)
- [아키텍처 패턴](#아키텍처-패턴)
- [구현 가이드라인](#구현-가이드라인)
- [예외 처리 패턴](#예외-처리-패턴)
- [테스트 작성 가이드](#테스트-작성-가이드)
- [모범 사례와 안티 패턴](#모범-사례와-안티-패턴)

## 🎯 기본 개념

### 서비스 레이어란?
비즈니스 로직을 뷰에서 분리하여 재사용 가능하고 테스트하기 쉬운 코드를 만드는 아키텍처 패턴입니다.

### 왜 필요한가?
1. **Single Responsibility Principle**: 뷰는 HTTP 처리만, 서비스는 비즈니스 로직만
2. **재사용성**: CLI, 테스트, 다른 뷰에서 동일한 로직 사용 가능
3. **테스트 용이성**: HTTP 의존성 없이 비즈니스 로직 단위 테스트 가능
4. **유지보수성**: 비즈니스 로직 변경 시 한 곳에서만 수정

### 책임 분리
```
View Layer    ─────────────────────► HTTP 요청/응답 처리, 인증/권한, 메시지 표시
     │
     ▼
Service Layer ─────────────────────► 비즈니스 로직, 검증, 트랜잭션 관리
     │
     ▼
Model Layer   ─────────────────────► 데이터 저장, 관계 정의, 기본 검증
```

## 🏗️ 아키텍처 패턴

### 기본 구조
```python
# services/auth_service.py
class AuthService:
    """인증 관련 비즈니스 로직"""
    
    def login_user(self, username, password):
        """사용자 로그인 처리"""
        # 입력값 검증
        if not username or not password:
            raise ValueError('아이디와 비밀번호를 모두 입력해주세요.')
        
        # 비즈니스 로직
        user = auth.authenticate(username=username, password=password)
        if not user:
            raise ValueError('아이디 또는 비밀번호가 올바르지 않습니다.')
            
        return user

# views.py
class LoginView(TemplateView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthService()  # 서비스 주입
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        try:
            user = self.auth_service.login_user(username, password)  # 서비스 호출
            auth.login(request, user)  # HTTP 관련 처리는 뷰에서
            messages.success(request, f'{user.nickname}님, 환영합니다!')
            return redirect('main')
        except ValueError as e:
            messages.error(request, str(e))  # Exception → Messages 변환
            return self.render_to_response({'error': str(e)})
```

### 서비스 클래스 명명 규칙
- `{Domain}Service` 패턴 사용
- 예: `AuthService`, `TeamService`, `ScheduleService`

### 메서드 명명 규칙
- 동사 + 명사 패턴: `create_team()`, `join_team()`, `send_email()`
- 부정형: `validate_*()`, `is_*()`, `check_*()`
- 헬퍼 메서드: `_private_method()` (언더스코어로 시작)

## 📝 구현 가이드라인

### 1. 서비스 클래스 기본 템플릿

```python
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import SomeModel
from .exceptions import CustomServiceException

class SomeService:
    """비즈니스 도메인 설명"""
    
    def public_method(self, param1, param2):
        """
        공개 메서드 - 외부에서 호출 가능
        
        Args:
            param1: 매개변수 설명
            param2: 매개변수 설명
            
        Returns:
            반환값 설명
            
        Raises:
            CustomServiceException: 예외 상황 설명
        """
        # 1. 입력값 검증
        self._validate_input(param1, param2)
        
        # 2. 비즈니스 로직 실행
        with transaction.atomic():  # 트랜잭션이 필요한 경우
            result = self._process_business_logic(param1, param2)
            
        return result
    
    def _validate_input(self, param1, param2):
        """입력값 검증 (private)"""
        if not param1:
            raise ValueError('param1은 필수입니다.')
            
    def _process_business_logic(self, param1, param2):
        """핵심 비즈니스 로직 (private)"""
        # 실제 비즈니스 로직 구현
        pass
```

### 2. 트랜잭션 관리

```python
from django.db import transaction

class TeamService:
    @transaction.atomic
    def create_team_with_members(self, team_data, member_list):
        """팀과 멤버를 동시에 생성 (트랜잭션 보장)"""
        # 모든 작업이 성공하거나 모두 롤백
        team = Team.objects.create(**team_data)
        
        for member_data in member_list:
            TeamUser.objects.create(team=team, **member_data)
            
        return team
```

### 3. 복잡한 검증 로직

```python
class TeamService:
    def join_team(self, user, team_id, password):
        """팀 가입 처리"""
        team = self._get_team_or_404(team_id)
        
        # 여러 검증 단계
        self._validate_team_password(team, password)
        self._validate_not_already_member(team, user)
        self._validate_team_capacity(team)
        
        # 가입 처리
        return self._create_membership(team, user)
    
    def _validate_team_password(self, team, password):
        if team.password != password:
            raise ValueError('팀 비밀번호가 올바르지 않습니다.')
            
    def _validate_not_already_member(self, team, user):
        if TeamUser.objects.filter(team=team, user=user).exists():
            raise ValueError('이미 가입된 팀입니다.')
            
    def _validate_team_capacity(self, team):
        if team.get_current_member_count() >= team.maxuser:
            raise ValueError('팀 인원이 가득 찼습니다.')
```

## ⚠️ 예외 처리 패턴

### 1. 커스텀 예외 정의

```python
# services/exceptions.py
class TeamMoaServiceException(Exception):
    """서비스 레이어 기본 예외"""
    pass

class ValidationError(TeamMoaServiceException):
    """입력값 검증 실패"""
    pass

class PermissionDenied(TeamMoaServiceException):
    """권한 부족"""
    pass

class ResourceNotFound(TeamMoaServiceException):
    """리소스 없음"""
    pass
```

### 2. 뷰에서 예외 처리 패턴

```python
from .services import TeamService
from .exceptions import ValidationError, PermissionDenied, ResourceNotFound

class TeamJoinView(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team_service = TeamService()
    
    def post(self, request, *args, **kwargs):
        try:
            team = self.team_service.join_team(
                user=request.user,
                team_id=request.POST.get('team_id'),
                password=request.POST.get('password')
            )
            messages.success(request, f'{team.title} 팀에 가입했습니다!')
            return redirect('team_detail', pk=team.id)
            
        except ValidationError as e:
            messages.error(request, str(e))
        except PermissionDenied as e:
            messages.warning(request, str(e))
        except ResourceNotFound as e:
            messages.info(request, str(e))
        except Exception as e:
            messages.error(request, '시스템 오류가 발생했습니다.')
            logger.error(f'Unexpected error in team join: {e}')
            
        return self.render_to_response({})
```

### 3. 예외 메시지 일관성

```python
class TeamService:
    # 일관된 메시지 패턴
    ERROR_MESSAGES = {
        'INVALID_PASSWORD': '팀 비밀번호가 올바르지 않습니다.',
        'ALREADY_MEMBER': '이미 가입된 팀입니다.',
        'TEAM_FULL': '팀 인원이 가득 찼습니다.',
        'TEAM_NOT_FOUND': '존재하지 않는 팀입니다.'
    }
    
    def _validate_team_password(self, team, password):
        if team.password != password:
            raise ValidationError(self.ERROR_MESSAGES['INVALID_PASSWORD'])
```

## 🧪 테스트 작성 가이드

### 1. 서비스 단위 테스트

```python
# tests/test_services.py
from django.test import TestCase
from unittest.mock import patch, Mock
from accounts.services import AuthService
from accounts.models import User

class AuthServiceTest(TestCase):
    def setUp(self):
        self.auth_service = AuthService()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_login_user_success(self):
        """로그인 성공 케이스"""
        with patch('accounts.services.auth.authenticate') as mock_auth:
            mock_auth.return_value = self.user
            
            result = self.auth_service.login_user('testuser', 'testpass123')
            
            self.assertEqual(result, self.user)
            mock_auth.assert_called_once_with(
                username='testuser', 
                password='testpass123'
            )
    
    def test_login_user_invalid_credentials(self):
        """로그인 실패 케이스"""
        with patch('accounts.services.auth.authenticate') as mock_auth:
            mock_auth.return_value = None
            
            with self.assertRaises(ValueError) as context:
                self.auth_service.login_user('testuser', 'wrongpass')
            
            self.assertIn('올바르지 않습니다', str(context.exception))
    
    def test_login_user_empty_input(self):
        """빈 입력값 검증"""
        with self.assertRaises(ValueError) as context:
            self.auth_service.login_user('', 'password')
        
        self.assertIn('모두 입력해주세요', str(context.exception))
```

### 2. 통합 테스트 예시

```python
class AuthServiceIntegrationTest(TestCase):
    def setUp(self):
        self.auth_service = AuthService()
    
    def test_full_registration_process(self):
        """회원가입 전체 프로세스 테스트"""
        form_data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        with patch('accounts.services.EmailMessage.send') as mock_send:
            current_site = Mock()
            current_site.domain = 'testserver'
            
            user = self.auth_service.register_user(form, current_site)
            
            # 사용자가 생성되었는지 확인
            self.assertEqual(user.username, 'newuser')
            self.assertFalse(user.is_active)  # 이메일 인증 전
            
            # 이메일이 발송되었는지 확인
            mock_send.assert_called_once()
```

## ✅ 모범 사례와 안티 패턴

### ✅ 모범 사례

#### 1. 명확한 책임 분리
```python
# ✅ GOOD: 서비스는 비즈니스 로직만
class TeamService:
    def create_team(self, user, team_data):
        # 입력값 검증
        self._validate_team_data(team_data)
        
        # 비즈니스 로직
        team = Team.objects.create(host=user, **team_data)
        TeamUser.objects.create(team=team, user=user)
        
        return team

# ✅ GOOD: 뷰는 HTTP 처리만
class TeamCreateView(FormView):
    def form_valid(self, form):
        try:
            team = self.team_service.create_team(
                user=self.request.user,
                team_data=form.cleaned_data
            )
            messages.success(self.request, '팀이 생성되었습니다!')
            return redirect('team_detail', pk=team.id)
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
```

#### 2. 트랜잭션 적절한 사용
```python
# ✅ GOOD: 관련된 여러 작업을 하나의 트랜잭션으로
@transaction.atomic
def transfer_team_ownership(self, team_id, new_host_id):
    team = Team.objects.select_for_update().get(id=team_id)
    old_host = team.host
    new_host = User.objects.get(id=new_host_id)
    
    # 원자성이 보장되어야 하는 작업들
    team.host = new_host
    team.save()
    
    # 권한 업데이트
    TeamUser.objects.filter(team=team, user=old_host).update(is_admin=False)
    TeamUser.objects.filter(team=team, user=new_host).update(is_admin=True)
```

#### 3. 예외적 상황 명확한 처리
```python
# ✅ GOOD: 구체적인 예외와 명확한 메시지
def join_team(self, user, team_id, password):
    try:
        team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        raise ResourceNotFound('존재하지 않는 팀입니다.')
    
    if team.password != password:
        raise ValidationError('팀 비밀번호가 올바르지 않습니다.')
    
    if TeamUser.objects.filter(team=team, user=user).exists():
        raise ValidationError('이미 가입된 팀입니다.')
```

### ❌ 안티 패턴

#### 1. 서비스에서 HTTP 처리
```python
# ❌ BAD: 서비스에서 request 객체 사용
def login_user(self, request, username, password):
    user = auth.authenticate(request, username=username, password=password)
    if user:
        auth.login(request, user)  # ❌ HTTP 처리를 서비스에서
        messages.success(request, '로그인 성공!')  # ❌ 메시지도 서비스에서
    return user

# ✅ GOOD: 서비스는 순수 비즈니스 로직만
def login_user(self, username, password):
    user = auth.authenticate(username=username, password=password)
    if not user:
        raise ValueError('로그인 정보가 올바르지 않습니다.')
    return user
```

#### 2. 뷰에서 복잡한 비즈니스 로직
```python
# ❌ BAD: 뷰에서 복잡한 비즈니스 로직
class TeamJoinView(View):
    def post(self, request):
        team_id = request.POST.get('team_id')
        password = request.POST.get('password')
        
        # ❌ 복잡한 검증 로직이 뷰에
        team = Team.objects.get(id=team_id)
        if team.password != password:
            messages.error(request, '비밀번호 틀림')
            return redirect('team_search')
        
        if TeamUser.objects.filter(team=team, user=request.user).exists():
            messages.error(request, '이미 가입됨')
            return redirect('team_search')
        
        # ❌ 더 많은 비즈니스 로직...
```

#### 3. 일관되지 않은 예외 처리
```python
# ❌ BAD: 일관되지 않은 예외 처리
def some_method(self):
    if condition1:
        return None  # ❌ 때로는 None 반환
    if condition2:
        raise ValueError('에러1')  # ❌ 때로는 ValueError
    if condition3:
        raise CustomException('에러2')  # ❌ 때로는 커스텀 예외

# ✅ GOOD: 일관된 예외 처리
def some_method(self):
    if condition1:
        raise ValidationError('조건1이 만족되지 않습니다.')
    if condition2:
        raise ValidationError('조건2가 만족되지 않습니다.')
    if condition3:
        raise ValidationError('조건3이 만족되지 않습니다.')
```

## 🔄 기존 코드 마이그레이션 체크리스트

### Phase 1: 서비스 클래스 생성
- [ ] 도메인별 서비스 클래스 생성
- [ ] 기존 뷰의 비즈니스 로직 식별
- [ ] 커스텀 예외 클래스 정의

### Phase 2: 비즈니스 로직 이동
- [ ] 복잡한 검증 로직 서비스로 이동
- [ ] DB 쿼리와 비즈니스 로직 서비스로 이동
- [ ] 트랜잭션이 필요한 부분 `@transaction.atomic` 적용

### Phase 3: 뷰 리팩토링
- [ ] 뷰에서 서비스 인스턴스 생성 (`__init__` 메서드에서)
- [ ] 비즈니스 로직 호출을 서비스 메서드 호출로 변경
- [ ] Exception → Messages 변환 패턴 적용

### Phase 4: 테스트 작성
- [ ] 서비스 메서드별 단위 테스트 작성
- [ ] 예외 상황별 테스트 케이스 작성
- [ ] 통합 테스트 작성

### Phase 5: 리팩토링 완료
- [ ] 코드 리뷰 및 품질 검증
- [ ] 성능 테스트
- [ ] 문서화 업데이트

## 📚 추가 자료

### 참고 문서
- [Accounts 서비스 레이어 리팩토링](accounts_service_refactor.md) - 실제 적용 사례
- [마이그레이션 로드맵](migration_roadmap.md) - 다른 앱 적용 계획

### 외부 자료
- [Django Service Layer Pattern](https://django-styleguide.readthedocs.io/en/latest/guides/services.html)
- [Clean Architecture in Django](https://engineering.21buttons.com/clean-architecture-in-django-d326a4ab86a9)

---

**💡 기억하세요**: 서비스 레이어는 코드를 복잡하게 만드는 것이 아니라, 복잡성을 잘 관리하기 위한 도구입니다. 작은 것부터 시작해서 점진적으로 적용해보세요!