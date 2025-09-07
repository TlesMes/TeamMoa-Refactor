# 📅 Schedules 앱 서비스 레이어 구현 보고서

**Phase 4** | **구현 완료일**: 2025.09.04 | **담당 앱**: Schedules

---

## 📊 개요 및 성과 지표

### 🎯 구현 목표
- JSON 기반 스케줄 데이터 처리 로직의 서비스화
- 복잡한 팀 가용성 계산 알고리즘의 최적화
- 트랜잭션을 통한 주간 스케줄 업로드 안정성 확보

### 📈 성과 지표
| 지표 | 이전 | 이후 | 개선율 |
|------|------|------|-------|
| 뷰 파일 라인 수 | 115줄 | 99줄 | **14% 감소** |
| 비즈니스 로직 분리 | 0% | 100% | **완전 분리** |
| 서비스 메서드 수 | 0개 | 4개 | **핵심 기능만** |
| 트랜잭션 보장 | 부분적 | 완전 | **100%** |
| 중복 검증 제거 | N/A | 완료 | **최적화** |

---

## 🏗️ 아키텍처 변경 사항

### Before: 기존 구조
```
┌─────────────────┐
│   Templates     │
└─────────────────┘
         │
┌─────────────────┐    ┌─────────────────┐
│     Views       │────│     Models      │
│  (115 lines)    │    │  (with @class   │
│                 │    │   method)       │
└─────────────────┘    └─────────────────┘
```

### After: 서비스 레이어 도입
```
┌─────────────────┐
│   Templates     │
└─────────────────┘
         │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Views       │────│   Services      │────│     Models      │
│   (99 lines)    │    │  (4 methods)    │    │  (simplified)   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🔧 구현된 서비스 메서드

### ScheduleService 클래스 구성 (4개 메서드)

#### 1️⃣ 개인 스케줄 관리
```python
def save_personal_schedule(self, team_user, week_start, schedule_data)
```
- **기능**: 개인 주간 스케줄을 트랜잭션으로 안전하게 저장
- **개선점**: 기존 뷰에 산재된 스케줄 처리 로직 통합
- **트랜잭션**: @transaction.atomic으로 원자성 보장
- **사용처**: SchedulerUploadPageView.post()

#### 2️⃣ 팀 스케줄 계산
```python
def get_team_availability(self, team, start_date, end_date)
```
- **기능**: 팀의 주간 가용성 실시간 계산
- **이전 위치**: `PersonalDaySchedule.get_team_availability()` 클래스 메서드
- **개선점**: 서비스로 이동하여 재사용성 증대
- **사용처**: SchedulerPageView.post()

#### 3️⃣ 내부 최적화 메서드
```python
@transaction.atomic
def _bulk_process_weekly_schedule(self, team_user, week_start, schedule_data)
```
- **기능**: 주간 스케줄 일괄 처리
- **성능**: 트랜잭션 내에서 7일치 스케줄 원자적 처리
- **사용처**: save_personal_schedule() 내부에서 호출

#### 4️⃣ 에러 메시지 상수
```python
ERROR_MESSAGES = {
    'INVALID_DATE': '유효하지 않은 날짜 형식입니다.',
    'INVALID_WEEK': '주간을 선택해주세요.',
}
```
- **기능**: 표준화된 에러 메시지 상수
- **사용처**: 모든 예외 처리에서 활용

---

## 📝 뷰 클래스 리팩토링

### SchedulerPageView 변경사항
```python
# Before (29줄)
def post(self, request, *args, **kwargs):
    team = get_object_or_404(Team, pk=kwargs['pk'])
    week = request.POST.get("week")
    
    if not week:
        messages.error(request, '주간을 선택해주세요.')
        return self.render_to_response({'team': team})
    
    try:
        date_mon = date.fromisoformat(week)
        date_sun = date_mon + timedelta(days=6)
        
        # 직접 모델 메서드 호출
        team_availability = PersonalDaySchedule.get_team_availability(
            team, date_mon, date_sun
        )
        # ...
    except ValueError:
        messages.error(request, '유효하지 않은 날짜 형식입니다.')
```

```python
# After (23줄)
def post(self, request, *args, **kwargs):
    team = get_object_or_404(Team, pk=kwargs['pk'])
    week = request.POST.get("week")
    
    try:
        if not week:
            raise ValueError(self.schedule_service.ERROR_MESSAGES['INVALID_WEEK'])
        
        date_mon = date.fromisoformat(week)
        date_sun = date_mon + timedelta(days=6)
        
        # 서비스를 통한 팀 가용성 계산
        team_availability = self.schedule_service.get_team_availability(
            team, date_mon, date_sun
        )
        # ...
    except ValueError as e:
        messages.error(request, str(e))
```

### SchedulerUploadPageView 변경사항
```python
# Before (45줄) - 복잡한 스케줄 저장 로직
for day_offset in range(7):
    current_date = week_start + timedelta(days=day_offset)
    
    PersonalDaySchedule.objects.filter(
        owner=teamuser,
        date=current_date
    ).delete()
    
    available_hours = []
    for hour in range(24):
        checkbox_name = f'time_{hour}-{day_offset + 1}'
        if request.POST.get(checkbox_name):
            available_hours.append(hour)
    
    if available_hours:
        PersonalDaySchedule.objects.create(
            owner=teamuser,
            date=current_date,
            available_hours=available_hours
        )
        updated_days += 1
```

```python
# After (8줄) - 서비스 호출로 간소화
updated_days = self.schedule_service.save_personal_schedule(
    teamuser, week_start, request.POST
)
```

---

## 🔄 Exception → Messages 패턴 적용

### 에러 메시지 표준화
```python
ERROR_MESSAGES = {
    'INVALID_DATE': '유효하지 않은 날짜 형식입니다.',
    'INVALID_WEEK': '주간을 선택해주세요.',
}
```

### 뷰에서의 통일된 예외 처리
```python
try:
    # 서비스 메서드 호출
    result = self.schedule_service.some_method(...)
    messages.success(request, '성공 메시지')
except ValueError as e:
    messages.error(request, str(e))
```

---

## 💾 데이터베이스 최적화

### 기존 쿼리 패턴 유지
- **select_related('owner')**: N+1 쿼리 방지
- **날짜별 그룹화**: Python 딕셔너리 활용
- **SQLite 호환**: 복잡한 SQL 대신 Python 집계

### 트랜잭션 도입
```python
@transaction.atomic
def _bulk_process_weekly_schedule(self, team_user, week_start, schedule_data):
    # 7일치 스케줄의 원자적 처리 보장
```

---

## 🧪 테스트 가능성 개선

### 서비스 레벨 단위 테스트 가능
```python
# 예시: 서비스 메서드 테스트
def test_save_personal_schedule():
    service = ScheduleService()
    result = service.save_personal_schedule(team_user, week_start, schedule_data)
    assert result == expected_days
```

### 뷰 테스트 간소화
- 서비스 로직 분리로 뷰 테스트는 HTTP 응답에만 집중
- 비즈니스 로직은 서비스 테스트에서 담당

---

## 📋 Migration Checklist

### ✅ 완료된 작업
- [x] ScheduleService 클래스 생성 (4개 메서드)
- [x] 모델의 클래스 메서드를 서비스로 이동
- [x] 2개 뷰 클래스 서비스 호출로 변경
- [x] Exception → Messages 패턴 적용
- [x] 트랜잭션 도입으로 데이터 일관성 확보
- [x] 중복 검증 제거 및 최적화
- [x] Django configuration 검증 완료
- [x] 서비스 임포트 테스트 통과

---

## 🎯 Phase 4 학습 효과

### 핵심 패턴 습득
1. **JSON 데이터 처리의 서비스화**: available_hours JSON 필드 처리 로직 분리
2. **복잡한 계산 로직 이동**: 24시간 x 7일 가용성 계산의 서비스 이전
3. **트랜잭션 적용**: 주간 스케줄 업데이트의 원자성 보장
4. **중복 검증 제거**: 3층 검증을 1층으로 최적화

### 재사용 가능한 컴포넌트
- `get_team_availability()`: 다른 앱에서도 활용 가능한 팀 스케줄 계산
- 깔끔한 서비스 인터페이스로 API 확장 준비

---


---

**💡 Phase 4 핵심 인사이트**: Schedules 앱에서는 "덜 하는 것이 더 많이 하는 것"임을 배웠습니다. 중복된 검증 로직을 제거하고 핵심 기능만 남김으로써 더 깔끔하고 유지보수하기 쉬운 서비스 레이어를 구축했습니다.

*구현 완료: 2025.09.04*