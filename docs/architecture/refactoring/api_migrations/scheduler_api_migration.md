# scheduler_page API 전환 작업 현황

**작업일**: 2025-10-09
**상태**: ✅ 구현 및 테스트 완료

---

## 📋 작업 개요

scheduler_page를 POST 폼 방식에서 API 기반 실시간 업데이트 방식으로 전환

### ✅ 완료된 작업

1. **scheduler_page.js 파일 생성** (`static/js/pages/scheduler_page.js`)
   - ISO week 형식 → start_date/end_date 변환 함수
   - API 호출 및 응답 처리
   - DOM 동적 업데이트
   - 에러 처리 및 로딩 상태 표시

2. **scheduler_page.html 템플릿 수정**
   - JavaScript 파일 연결 (`{% block extra_js %}`)

---

## 🔧 구현 세부사항

### 1. **새 파일: scheduler_page.js**

**위치**: `static/js/pages/scheduler_page.js`

**주요 함수**:

#### `weekToDateRange(weekString)`
- ISO week 형식(YYYY-Www)을 시작일/종료일로 변환
- ISO 8601 표준 준수 (Week 1 = 1월 4일 포함 주)
- 입력: `"2025-W40"`
- 출력: `{startDate: "2025-09-29", endDate: "2025-10-05"}`

#### `loadTeamAvailability(weekString)`
- API 엔드포인트 호출: `GET /api/v1/teams/{teamId}/schedules/team-availability/`
- 쿼리 파라미터: `start_date`, `end_date`
- 로딩 상태 표시 (opacity 0.5, pointer-events none)
- 성공 시 `updateScheduleTable()` 호출
- 실패 시 토스트 에러 메시지

#### `updateScheduleTable(availabilityData)`
- 7일치 가용성 데이터로 테이블 업데이트
- 날짜 헤더 업데이트 (월/일, 요일)
- 각 시간대 셀의 `availability-N` 클래스 교체
- 가용 인원 수 텍스트 업데이트

#### `showLoadingState(isLoading)`
- 로딩 중: 그리드 반투명 처리 + 클릭 방지
- 로딩 완료: 원상복구

**이벤트 핸들러**:
- 폼 제출 방지 (`e.preventDefault()`)
- 주차 입력 변경 시 자동 API 호출
- 제출 버튼 클릭 시 API 호출

---

### 2. **수정된 파일: scheduler_page.html**

**변경 내용**:
```django
{% block extra_js %}
<script src="{% static 'js/pages/scheduler_page.js' %}"></script>
{% endblock %}
```

**템플릿 구조 (유지됨)**:
- SSR로 초기 렌더링 (현재 주차 또는 기본값)
- 폼은 그대로 유지 (JavaScript에서 제출 방지)
- `id="schedulediv1"` ~ `id="schedulediv7"` 유지

---

## 🔗 API 연동 구조 (기존 인프라 재사용)

**이번 작업**: 프론트엔드 JavaScript만 추가
**백엔드**: API 인프라 이미 구현되어 있었음

### 1. URL 라우팅 (api/urls.py - 77-79줄)

```python
# 스케줄 엔드포인트
path('v1/teams/<int:team_pk>/schedules/team-availability/', ScheduleViewSet.as_view({
    'get': 'get_team_availability'
}), name='team-schedules-availability'),
```

- **URL**: `/api/v1/teams/{team_pk}/schedules/team-availability/`
- **HTTP Method**: `GET`
- **ViewSet 액션**: `get_team_availability`

---

### 2. ViewSet 액션 (schedules/viewsets.py - 83-112줄)

```python
@action(detail=False, methods=['get'], url_path='team-availability')
def get_team_availability(self, request, team_pk=None):
    team = self.get_team()

    # 쿼리 파라미터 검증
    query_serializer = TeamScheduleQuerySerializer(data=request.query_params)
    query_serializer.is_valid(raise_exception=True)

    start_date = query_serializer.validated_data['start_date']
    end_date = query_serializer.validated_data['end_date']

    # 서비스 레이어 호출
    availability_data = self.schedule_service.get_team_availability(
        team=team,
        start_date=start_date,
        end_date=end_date
    )

    # 응답 직렬화
    response_serializer = TeamAvailabilitySerializer(availability_data, many=True)

    return Response({
        'success': True,
        'data': response_serializer.data
    }, status=status.HTTP_200_OK)
```

**처리 흐름**:
1. 쿼리 파라미터 검증 (TeamScheduleQuerySerializer)
2. 서비스 레이어 호출
3. 응답 직렬화 (TeamAvailabilitySerializer)

---

### 3. 시리얼라이저 (schedules/serializers.py)

#### TeamScheduleQuerySerializer (42-51줄)
```python
class TeamScheduleQuerySerializer(serializers.Serializer):
    """팀 스케줄 조회 파라미터 직렬화"""
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError('시작일은 종료일보다 이전이어야 합니다.')
        return data
```

**역할**: 요청 파라미터 검증
- `start_date`, `end_date` 날짜 형식 검증
- 시작일 ≤ 종료일 검증

#### TeamAvailabilitySerializer (33-39줄)
```python
class TeamAvailabilitySerializer(serializers.Serializer):
    """팀 가용성 조회 결과 직렬화"""
    date = serializers.DateField()
    availability = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="시간대별 가능한 인원 수 {0: 3, 9: 5, ...}"
    )
```

**역할**: 응답 데이터 구조화
- `date`: 날짜
- `availability`: {시간대: 가용 인원 수} 딕셔너리

---

### 4. API 요청/응답 예시

**요청**:
```http
GET /api/v1/teams/5/schedules/team-availability/?start_date=2025-09-29&end_date=2025-10-05
```

**응답**:
```json
{
  "success": true,
  "data": [
    {
      "date": "2025-09-29",
      "availability": {
        "0": 3, "1": 5, "9": 8, "14": 10, "23": 2
      }
    },
    {
      "date": "2025-09-30",
      "availability": {
        "0": 4, "9": 7, ...
      }
    }
    ... (총 7일치)
  ]
}
```

---

### 5. 서비스 레이어 (재사용)

`ScheduleService.get_team_availability()` 메서드 그대로 활용
- PersonalDaySchedule 조회
- 시간대별 가용 인원 집계
- 비즈니스 로직 변경 없음

---

## 🧪 테스트 시나리오

1. **초기 로드**
   - 페이지 접속 시 SSR로 현재 주차 표시
   - JavaScript 로드 확인

2. **주차 변경**
   - 주차 선택 변경 시 자동 API 호출
   - 페이지 새로고침 없이 테이블 업데이트
   - 날짜 헤더 정확성 확인

3. **제출 버튼 클릭**
   - 폼 제출 방지 확인
   - API 호출 및 데이터 업데이트

4. **에러 처리**
   - 네트워크 오류 시 토스트 메시지
   - 빈 주차 선택 시 경고

5. **로딩 상태**
   - API 호출 중 그리드 반투명 처리
   - 완료 후 정상 복구

---

## 🎯 기대 효과

### 개선 사항
- ✅ 페이지 새로고침 제거 → 부드러운 UX
- ✅ Members 앱과 동일한 API 패턴 적용
- ✅ 기존 API 인프라 100% 재사용
- ✅ 서비스 레이어 변경 불필요

### Members 앱 패턴과의 일관성
- 공통 토스트 메시지 사용 (`showDjangoToast`)
- fetch API 기반 비동기 호출
- DOM 직접 조작 방식

---

## ⚠️ 주의사항

1. **날짜 계산**
   - ISO 8601 표준 준수
   - 로컬 시간대 처리 (`new Date(dayData.date + 'T00:00:00')`)

2. **클래스 관리**
   - 기존 `availability-N` 클래스 제거 후 새 클래스 추가
   - 정규식 사용: `slot.className.replace(/availability-\d+/g, '')`

3. **DOM 선택자**
   - `#schedulediv1` ~ `#schedulediv7` ID 의존
   - `.date-line`, `.day-line` 클래스 의존

---

## 📦 커밋 대기 파일

```
새 파일:
  static/js/pages/scheduler_page.js

수정된 파일:
  schedules/templates/schedules/scheduler_page.html
```

**제안 커밋 메시지**:
```
feat(schedules): scheduler_page API 기반 실시간 업데이트 전환

- POST 폼 방식에서 REST API 호출 방식으로 전환
- 페이지 새로고침 없는 주차 변경 기능 구현
- ISO week → start_date/end_date 변환 로직 추가
- 로딩 상태 및 에러 처리 구현
- 기존 API 엔드포인트 및 서비스 레이어 재사용
```

---

## 🔜 다음 단계

1. **테스트 수행**
   - 브라우저 콘솔 오류 확인
   - 다양한 주차 선택 테스트
   - 에러 케이스 검증

2. **문서 업데이트**
   - `docs/README.md` - Schedules 앱 API 전환 완료 표시
   - `CLAUDE.md` - 우선순위 1번 작업 완료 기록

3. **향후 개선 가능성**
   - 주차 선택 시 URL 파라미터 업데이트 (브라우저 히스토리)
   - 키보드 단축키 (이전/다음 주)
   - 애니메이션 효과 추가

---

## ✅ 테스트 결과 (2025-10-09)

### API 테스트 완료
- ✅ `GET /api/v1/teams/{id}/schedules/team-availability/` 정상 작동
- ✅ 7일치 가용성 데이터 반환 (start_date ~ end_date)
- ✅ 응답 형식: `{"success": true, "data": [...]}`
- ✅ 각 날짜별 24시간 availability 딕셔너리

### 브라우저 테스트
- ✅ 페이지 로드 시 현재 주차 자동 표시
- ✅ 주차 선택 변경 시 API 호출 (페이지 새로고침 없음)
- ✅ DOM 동적 생성 및 업데이트 정상
- ✅ 로딩 상태 표시 (opacity 0.5)
- ✅ 토스트 메시지 표시

### 발견된 이슈
- ⚠️ 초기 schedules 변수 비어있어서 SSR 렌더링 실패
- ✅ 해결: JavaScript에서 DOM 동적 생성으로 변경

---

*작성: 2025-10-09*
*구현 및 테스트 완료 - 커밋 완료 (8302adb)*
