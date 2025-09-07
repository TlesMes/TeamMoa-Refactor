# Mindmaps 앱 전면 재설계 계획

## 📊 현재 상태 분석

### 🚨 주요 문제점 (사용성 점수: 2.0/10)

#### 1. 기술적 한계
- **Canvas 기반 수동 좌표 입력**: 사용자가 X, Y 좌표를 직접 숫자로 입력해야 함
- **드래그 앤 드롭 부재**: 노드 이동이나 연결을 위한 시각적 조작 불가
- **고정 크기**: 800x600px 고정으로 확대/축소 기능 없음
- **원시적 Canvas API**: 직접적인 2D 컨텍스트 조작으로 유지보수성 저하

#### 2. 사용성 문제
- **비직관적 인터페이스**: 마인드맵 생성을 위해 수학적 좌표 계산 필요
- **편집 제약**: 기존 노드 위치 변경이나 텍스트 수정 불가
- **협업 한계**: 실시간 협업 기능 전무
- **모바일 지원 부족**: 터치 기반 조작 불가

#### 3. 기능적 결함
- **노드 관계 복잡성**: 부모 노드를 텍스트로 검색하여 연결
- **시각적 피드백 부족**: 연결선과 노드의 시각적 구분 부족
- **접근성 부족**: 키보드 네비게이션, 스크린 리더 지원 없음

### ✅ 현재 강점
- **서비스 레이어 완성**: 비즈니스 로직 분리 완료 (MindmapService)
- **권한 관리 체계**: TeamMemberRequiredMixin으로 접근 제어
- **추천 시스템**: JSON 기반 추천 기능 구현
- **댓글 시스템**: 노드별 협업 기능 지원

## 🎯 재설계 목표

### 1. 현대적 UI/UX 구현
- 직관적 드래그 앤 드롭 노드 조작
- 실시간 시각적 피드백
- 반응형 디자인 (모바일 최적화)
- 접근성 표준 준수

### 2. 고급 기능 도입
- 실시간 협업 지원
- 무한 캔버스 (줌/팬 기능)
- 다양한 노드 타입
- 실행취소/다시실행

### 3. 성능 최적화
- 가상화를 통한 대규모 마인드맵 지원
- 효율적인 렌더링 엔진
- 최적화된 데이터 구조

## 🛠️ 기술 스택 선정

### 프론트엔드 라이브러리 비교

#### Option 1: React Flow (★★★★★ 추천)
**장점:**
- 마인드맵 전용 컴포넌트 생태계
- 뛰어난 성능과 확장성
- 실시간 협업 지원 용이
- 풍부한 문서화와 커뮤니티

**단점:**
- React 의존성 (현재 Django 템플릿 기반)
- 초기 학습 곡선

**적용 방안:**
- 특정 페이지만 React 컴포넌트로 구현
- Django REST API와 연동

#### Option 2: D3.js + Custom Implementation (★★★☆☆)
**장점:**
- 최대한의 커스터마이징 가능
- 기존 Django 템플릿과 호환성

**단점:**
- 높은 개발 복잡도
- 유지보수 부담 증가

#### Option 3: JointJS (★★★★☆)
**장점:**
- 강력한 다이어그램 엔진
- TypeScript 지원

**단점:**
- 상용 라이선스 필요
- 높은 비용

### 🎯 선정 결과: React Flow 기반 하이브리드 접근법

#### 구현 전략
1. **마인드맵 에디터만 React 컴포넌트화**
2. **나머지 페이지는 기존 Django 템플릿 유지**
3. **Django REST API로 데이터 연동**

## 🏗️ 새로운 아키텍처 설계

### 1. 데이터 모델 개선

#### 기존 모델 유지 + 확장
```python
class Mindmap(models.Model):
    title = models.CharField(max_length=64)
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE)
    
    # 새로운 필드 추가
    layout_data = models.JSONField(default=dict, blank=True)  # 레이아웃 설정
    zoom_level = models.FloatField(default=1.0)             # 줌 레벨
    center_x = models.FloatField(default=0)                 # 중심 X 좌표
    center_y = models.FloatField(default=0)                 # 중심 Y 좌표
    
    updated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

class Node(models.Model):
    # 기존 필드 유지
    posX = models.FloatField()  # int → float로 변경 (정밀도 향상)
    posY = models.FloatField()
    title = models.CharField(max_length=64)
    content = models.TextField()
    mindmap = models.ForeignKey('Mindmap', on_delete=models.CASCADE)
    
    # 새로운 필드 추가
    node_type = models.CharField(max_length=20, default='default')  # 노드 타입
    width = models.FloatField(default=100)                         # 노드 너비
    height = models.FloatField(default=60)                         # 노드 높이
    style_data = models.JSONField(default=dict, blank=True)        # 스타일 설정
    
    # 기존 추천 시스템 유지
    recommended_users = models.JSONField(default=list, blank=True)
    recommendation_count = models.PositiveIntegerField(default=0)
    
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class NodeConnection(models.Model):
    from_node = models.ForeignKey('Node', related_name='outgoing_connections', on_delete=models.CASCADE)
    to_node = models.ForeignKey('Node', related_name='incoming_connections', on_delete=models.CASCADE)
    mindmap = models.ForeignKey('Mindmap', on_delete=models.CASCADE)
    
    # 새로운 필드 추가
    connection_type = models.CharField(max_length=20, default='default')  # 연결선 타입
    style_data = models.JSONField(default=dict, blank=True)              # 스타일 설정

# 실시간 협업을 위한 새 모델
class MindmapSession(models.Model):
    mindmap = models.ForeignKey('Mindmap', on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    session_id = models.CharField(max_length=32, unique=True)
    cursor_x = models.FloatField(default=0)
    cursor_y = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['mindmap', 'user']
```

### 2. API 레이어 설계

#### REST API 엔드포인트
```python
# urls.py
api_patterns = [
    path('api/mindmaps/<int:mindmap_id>/', MindmapAPIView.as_view()),
    path('api/mindmaps/<int:mindmap_id>/nodes/', NodeListAPIView.as_view()),
    path('api/mindmaps/<int:mindmap_id>/nodes/<int:node_id>/', NodeDetailAPIView.as_view()),
    path('api/mindmaps/<int:mindmap_id>/connections/', ConnectionListAPIView.as_view()),
    path('api/mindmaps/<int:mindmap_id>/collaborate/', CollaborationAPIView.as_view()),
]
```

#### API 응답 구조
```json
{
  "mindmap": {
    "id": 1,
    "title": "프로젝트 계획",
    "layout_data": {"algorithm": "tree", "direction": "down"},
    "zoom_level": 1.0,
    "center_x": 0,
    "center_y": 0
  },
  "nodes": [
    {
      "id": 1,
      "posX": 100.5,
      "posY": 200.5,
      "title": "메인 아이디어",
      "content": "프로젝트의 핵심 개념",
      "node_type": "root",
      "width": 120,
      "height": 60,
      "style_data": {"backgroundColor": "#4A90E2", "color": "#FFFFFF"},
      "recommendation_count": 3
    }
  ],
  "connections": [
    {
      "id": 1,
      "from_node": 1,
      "to_node": 2,
      "connection_type": "solid",
      "style_data": {"strokeWidth": 2, "color": "#A6B0D0"}
    }
  ],
  "active_users": [
    {
      "user_id": 1,
      "username": "김개발",
      "cursor_x": 150.0,
      "cursor_y": 250.0
    }
  ]
}
```

### 3. 프론트엔드 컴포넌트 구조

#### React Flow 기반 컴포넌트
```javascript
// MindmapEditor.jsx
import React, { useState, useCallback } from 'react';
import ReactFlow, {
  addEdge,
  useNodesState,
  useEdgesState,
  Background,
  Controls,
  MiniMap
} from '@xyflow/react';

const MindmapEditor = ({ mindmapId, teamId }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // 실시간 협업 훅
  useRealtimeCollaboration(mindmapId);
  
  // 드래그 앤 드롭 핸들러
  const onConnect = useCallback((params) => {
    setEdges((eds) => addEdge(params, eds));
  }, []);

  return (
    <div className="mindmap-editor">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
};
```

### 4. 실시간 협업 시스템

#### WebSocket 구현
```python
# consumers.py
class MindmapConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.mindmap_id = self.scope['url_route']['kwargs']['mindmap_id']
        self.room_group_name = f'mindmap_{self.mindmap_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # 노드 이동, 생성, 삭제 등 실시간 동기화
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'mindmap_update',
                'message': data
            }
        )
```

### 5. 서비스 레이어 확장

#### MindmapService 개선
```python
class MindmapService:
    # 기존 메서드 유지 + 새로운 메서드 추가
    
    def update_node_position(self, node_id, x, y, user):
        """실시간 노드 위치 업데이트"""
        node = get_object_or_404(Node, pk=node_id)
        node.posX = x
        node.posY = y
        node.save()
        
        # WebSocket으로 실시간 브로드캐스트
        self._broadcast_update(node.mindmap_id, {
            'type': 'node_moved',
            'node_id': node_id,
            'x': x,
            'y': y,
            'user': user.username
        })
        
        return node
    
    def auto_layout(self, mindmap_id, algorithm='tree'):
        """자동 레이아웃 적용"""
        mindmap = get_object_or_404(Mindmap, pk=mindmap_id)
        nodes = Node.objects.filter(mindmap=mindmap)
        
        if algorithm == 'tree':
            positioned_nodes = self._apply_tree_layout(nodes)
        elif algorithm == 'force':
            positioned_nodes = self._apply_force_layout(nodes)
        
        # 일괄 업데이트
        Node.objects.bulk_update(positioned_nodes, ['posX', 'posY'])
        
        return positioned_nodes
```

## 🚀 구현 로드맵

### Phase 1: 기반 구축 (2-3주)
- [ ] Django REST Framework 설정
- [ ] React Flow 환경 구축
- [ ] 기본 CRUD API 개발
- [ ] 단순한 마인드맵 렌더링 구현

### Phase 2: 핵심 기능 (3-4주)
- [ ] 드래그 앤 드롭 노드 이동
- [ ] 시각적 연결선 그리기
- [ ] 노드 생성/편집 인터페이스
- [ ] 확대/축소/팬 기능

### Phase 3: 고급 기능 (2-3주)
- [ ] 자동 레이아웃 알고리즘
- [ ] 다양한 노드 타입
- [ ] 스타일 커스터마이징
- [ ] 키보드 단축키

### Phase 4: 협업 기능 (3-4주)
- [ ] WebSocket 실시간 동기화
- [ ] 멀티 커서 표시
- [ ] 변경 히스토리 관리
- [ ] 실행취소/다시실행

### Phase 5: 최적화 및 완성 (2주)
- [ ] 성능 최적화
- [ ] 접근성 개선
- [ ] 모바일 반응형
- [ ] 테스트 코드 작성

## 📊 예상 효과

### 사용성 개선
- **현재 2.0점 → 목표 8.5점** (325% 향상)
- 직관적 조작으로 사용자 학습 비용 90% 절감
- 모바일 지원으로 접근성 대폭 향상

### 기술적 이점
- 현대적 기술 스택 도입
- 실시간 협업으로 팀워크 효율성 증대
- 확장 가능한 아키텍처 구축

### 비즈니스 가치
- 사용자 경험 혁신으로 경쟁력 강화
- 협업 도구로서의 실용성 극대화
- 향후 다른 앱 현대화의 모범 사례 제공

---
*최종 업데이트: 2025.09.07*