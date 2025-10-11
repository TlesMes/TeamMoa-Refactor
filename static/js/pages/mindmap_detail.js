// 마인드맵 에디터 클래스
class MindmapEditor {
  constructor(teamId, mindmapId, currentUser) {
    this.teamId = teamId;
    this.mindmapId = mindmapId;
    this.currentUser = currentUser; // 현재 사용자 정보 저장
    this.canvas = document.getElementById('mindmap');
    this.ctx = this.canvas.getContext('2d');
    this.socket = null;

    // 가상 캔버스 경계 설정
    this.VIRTUAL_CANVAS = {
      width: 5400,   // 가상 캔버스 폭 (1/2 축소)
      height: 3600,  // 가상 캔버스 높이 (1/2 축소)
      minX: 0,       // 좌측 경계
      minY: 0,       // 상단 경계
      maxX: 5400,    // 우측 경계
      maxY: 3600     // 하단 경계
    };

    // 시각적 피드백 상태
    this.showBoundaryFeedback = false;

    // 상태 관리
    this.nodes = [];
    this.connections = [];
    this.activeUsers = new Map();
    this.isDragging = false;
    this.dragNode = null;
    this.dragOffset = { x: 0, y: 0 };

    // 연결선 관리
    this.isConnecting = false;
    this.connectingFromNode = null;
    this.tempConnectionEnd = null;
    this.hoveredConnection = null;
    this.selectedConnection = null;
    this.prevHoveredConnection = null; // 이전 호버 상태 추적

    // 뷰포트 관리
    this.scale = 1.0;
    this.translateX = 0;
    this.translateY = 0;
    this.isPanning = false;
    this.panStart = { x: 0, y: 0 };

    this.initCanvas();
    this.initWebSocket();
    this.initEventListeners();
    this.loadInitialData();

    // 초기 뷰포트를 가상 캔버스 중심의 2/3 크기로 설정
    this.setInitialView();
  }

  initCanvas() {
    // 캔버스 크기를 부모 컨테이너에 맞게 조정
    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());

    this.ctx.font = '14px GmarketSansMedium, sans-serif';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
  }

  resizeCanvas() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const width = rect.width;
    const height = window.innerHeight - 120;

    this.canvas.width = width;
    this.canvas.height = height;
    this.canvas.style.width = width + 'px';
    this.canvas.style.height = height + 'px';

    this.render();
  }

  initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/mindmap/${this.teamId}/${this.mindmapId}/`;

    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('WebSocket 연결됨');
      this.updateConnectionStatus(true);

      // 본인을 접속자 목록에 추가
      this.activeUsers.set(this.currentUser.userId, {
        username: this.currentUser.username,
        x: 0,
        y: 0,
        isCurrentUser: true
      });
      this.updateActiveUsers();
    };

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleWebSocketMessage(data);
    };

    this.socket.onclose = () => {
      console.log('WebSocket 연결 종료');
      this.updateConnectionStatus(false);

      // 다른 사용자들 제거하고 본인만 남김
      this.activeUsers.clear();
      this.activeUsers.set(this.currentUser.userId, {
        username: this.currentUser.username,
        x: 0,
        y: 0,
        isCurrentUser: true
      });
      this.updateActiveUsers();

      // 자동 재연결 시도
      setTimeout(() => this.initWebSocket(), 3000);
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket 오류:', error);
      this.updateConnectionStatus(false);
    };
  }

  initEventListeners() {
    // 마우스 이벤트
    this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
    this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
    this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
    this.canvas.addEventListener('wheel', (e) => this.onWheel(e), { passive: false });
    this.canvas.addEventListener('dblclick', (e) => this.onDoubleClick(e));
    this.canvas.addEventListener('click', (e) => this.onClick(e));

    // 줌 컨트롤
    document.getElementById('zoomIn').addEventListener('click', () => this.zoom(1.2));
    document.getElementById('zoomOut').addEventListener('click', () => this.zoom(0.8));
    document.getElementById('resetZoom').addEventListener('click', () => this.resetView());

    // 키보드 이벤트
    document.addEventListener('keydown', (e) => this.onKeyDown(e));
  }

  loadInitialData() {
    // 서버에서 전달받은 초기 데이터는 window.mindmapData에서 로드
    if (window.mindmapData && window.mindmapData.nodes) {
      this.nodes = window.mindmapData.nodes;
    }

    if (window.mindmapData && window.mindmapData.connections) {
      this.connections = window.mindmapData.connections;
    }

    this.render();
  }

  // WebSocket 메시지 처리
  handleWebSocketMessage(data) {
    switch (data.type) {
      case 'user_joined':
        console.log(`${data.username} 참가`);
        // 새 사용자를 activeUsers Map에 추가 (본인이 아닌 경우만)
        if (data.user_id !== this.currentUser.userId) {
          this.activeUsers.set(data.user_id, {
            username: data.username,
            x: 0,
            y: 0,
            isCurrentUser: false
          });
        }
        this.updateActiveUsers();
        break;
      case 'user_left':
        console.log(`${data.username} 퇴장`);
        this.activeUsers.delete(data.user_id);
        this.updateActiveUsers();
        break;
      case 'node_moved':
        this.updateNodePosition(data.node_id, data.x, data.y);
        break;
      case 'cursor_moved':
        this.updateUserCursor(data.user_id, data.username, data.x, data.y);
        break;
      case 'connection_created':
        this.addConnection(data.connection_id, data.from_node_id, data.to_node_id);
        break;
      case 'connection_deleted':
        this.removeConnection(data.connection_id);
        break;
    }
  }

  addConnection(connectionId, fromNodeId, toNodeId) {
    // 중복 체크
    if (this.connections.some(c => c.id === connectionId)) {
      return;
    }

    this.connections.push({
      id: connectionId,
      fromNodeId: fromNodeId,
      toNodeId: toNodeId
    });

    console.log(`연결선 추가: ${connectionId} (${fromNodeId} → ${toNodeId})`);
    this.render();
  }

  removeConnection(connectionId) {
    this.connections = this.connections.filter(c => c.id !== connectionId);

    // 선택된 연결선이 삭제된 경우 선택 해제
    if (this.selectedConnection && this.selectedConnection.id === connectionId) {
      this.selectedConnection = null;
    }

    console.log(`연결선 삭제: ${connectionId}`);
    this.render();
  }

  // 마우스 이벤트 핸들러
  onMouseDown(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - this.translateX) / this.scale;
    const y = (e.clientY - rect.top - this.translateY) / this.scale;

    const node = this.getNodeAt(x, y);

    if (node && e.ctrlKey) {
      // Ctrl+클릭: 연결 모드 시작
      this.isConnecting = true;
      this.connectingFromNode = node;
      this.tempConnectionEnd = { x, y };
      this.canvas.style.cursor = 'crosshair';
      e.preventDefault(); // 기본 동작 방지
    } else if (node) {
      // 일반 노드 드래그 시작
      this.isDragging = true;
      this.dragNode = node;
      this.dragOffset = { x: x - node.x, y: y - node.y };
      this.canvas.style.cursor = 'grabbing';
    } else if (e.button === 0) { // 왼쪽 버튼
      // 팬 모드 시작
      this.isPanning = true;
      this.panStart = { x: e.clientX - this.translateX, y: e.clientY - this.translateY };
      this.canvas.style.cursor = 'grabbing';
    }
  }

  onMouseMove(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - this.translateX) / this.scale;
    const y = (e.clientY - rect.top - this.translateY) / this.scale;

    // 커서 위치 전송 (스로틀링)
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      if (!this.cursorThrottle) {
        this.cursorThrottle = setTimeout(() => {
          this.socket.send(JSON.stringify({
            type: 'cursor_move',
            x: x,
            y: y
          }));
          this.cursorThrottle = null;
        }, 50);
      }
    }

    if (this.isConnecting) {
      // 연결 모드: 임시 연결선 미리보기
      this.tempConnectionEnd = { x, y };
      this.render();

      // 호버된 노드 강조
      const targetNode = this.getNodeAt(x, y);
      if (targetNode && targetNode.id !== this.connectingFromNode.id) {
        this.canvas.style.cursor = 'crosshair';
      } else {
        this.canvas.style.cursor = 'not-allowed';
      }

    } else if (this.isDragging && this.dragNode) {
      // 노드 드래그 (가상 캔버스 경계 제한 적용)
      let newX = x - this.dragOffset.x;
      let newY = y - this.dragOffset.y;

      // 경계 도달 감지를 위한 원래 좌표 저장
      const originalX = newX;
      const originalY = newY;

      // 가상 캔버스 경계 내로 제한
      newX = Math.max(this.VIRTUAL_CANVAS.minX, Math.min(this.VIRTUAL_CANVAS.maxX, newX));
      newY = Math.max(this.VIRTUAL_CANVAS.minY, Math.min(this.VIRTUAL_CANVAS.maxY, newY));

      // 경계에 도달했는지 확인하고 시각적 피드백 제공
      const hitBoundary = (originalX !== newX || originalY !== newY);
      if (hitBoundary) {
        this.canvas.style.cursor = 'not-allowed';
        this.showBoundaryFeedback = true;
      } else {
        this.canvas.style.cursor = 'grabbing';
        this.showBoundaryFeedback = false;
      }

      this.dragNode.x = newX;
      this.dragNode.y = newY;

      this.render();

      // WebSocket으로 위치 전송
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({
          type: 'node_move',
          node_id: this.dragNode.id,
          x: newX,
          y: newY
        }));
      }

    } else if (this.isPanning) {
      // 캔버스 팬 (제한 적용)
      const newTranslateX = e.clientX - this.panStart.x;
      const newTranslateY = e.clientY - this.panStart.y;

      const constrained = this.constrainPan(newTranslateX, newTranslateY);
      this.translateX = constrained.x;
      this.translateY = constrained.y;
      this.render();
    } else {
      // 마우스 오버 효과 (노드 및 연결선)
      const node = this.getNodeAt(x, y);
      const connection = this.getConnectionAt(x, y);

      // 호버 상태가 변경된 경우에만 렌더링
      let needsRender = false;

      if (connection) {
        if (this.hoveredConnection !== connection) {
          this.hoveredConnection = connection;
          needsRender = true;
        }
        this.canvas.style.cursor = 'pointer';
      } else if (node) {
        if (this.hoveredConnection !== null) {
          this.hoveredConnection = null;
          needsRender = true;
        }
        this.canvas.style.cursor = 'grab';
      } else {
        if (this.hoveredConnection !== null) {
          this.hoveredConnection = null;
          needsRender = true;
        }
        this.canvas.style.cursor = 'default';
      }

      if (needsRender) {
        this.render();
      }
    }
  }

  async onMouseUp(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - this.translateX) / this.scale;
    const y = (e.clientY - rect.top - this.translateY) / this.scale;

    if (this.isConnecting) {
      // 연결 모드 종료: 대상 노드 확인 및 연결 생성
      const targetNode = this.getNodeAt(x, y);

      if (targetNode && targetNode.id !== this.connectingFromNode.id) {
        // 유효한 대상 노드에 연결
        await this.createConnection(this.connectingFromNode.id, targetNode.id);
      }

      // 연결 모드 상태 초기화
      this.isConnecting = false;
      this.connectingFromNode = null;
      this.tempConnectionEnd = null;
    }

    this.isDragging = false;
    this.dragNode = null;
    this.isPanning = false;
    this.showBoundaryFeedback = false; // 경계 피드백 리셋
    this.canvas.style.cursor = 'default';
    this.render(); // 피드백 제거를 위해 다시 렌더링
  }

  onWheel(e) {
    e.preventDefault();

    const rect = this.canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const wheel = e.deltaY < 0 ? 1.1 : 0.9;

    // 가상 캔버스 크기에 맞춘 줌 범위 조정
    // 최소 스케일: 가상 캔버스가 화면을 완전히 채우는 크기 (줌아웃 제한)
    const minScale = Math.max(
      this.canvas.width / this.VIRTUAL_CANVAS.width,
      this.canvas.height / this.VIRTUAL_CANVAS.height
    );

    const maxScale = 5.0; // 최대 5배까지 확대 가능

    const newScale = Math.min(Math.max(minScale, this.scale * wheel), maxScale);

    // 마우스 위치를 중심으로 줌
    const newTranslateX = mouseX - (mouseX - this.translateX) * (newScale / this.scale);
    const newTranslateY = mouseY - (mouseY - this.translateY) * (newScale / this.scale);

    this.scale = newScale;

    // 줌 후 팬 제한 적용
    const constrained = this.constrainPan(newTranslateX, newTranslateY);
    this.translateX = constrained.x;
    this.translateY = constrained.y;

    this.render();
  }

  onClick(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - this.translateX) / this.scale;
    const y = (e.clientY - rect.top - this.translateY) / this.scale;

    const connection = this.getConnectionAt(x, y);

    if (connection) {
      this.selectedConnection = connection;
      this.render();
    } else {
      this.selectedConnection = null;
      this.render();
    }
  }

  onDoubleClick(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - this.translateX) / this.scale;
    const y = (e.clientY - rect.top - this.translateY) / this.scale;

    const node = this.getNodeAt(x, y);
    const connection = this.getConnectionAt(x, y);

    if (node) {
      // 노드 상세 페이지로 이동
      if (window.mindmapUrls && window.mindmapUrls.nodeDetailBase) {
        window.location.href = window.mindmapUrls.nodeDetailBase + `/${node.id}`;
      }
    } else if (!connection) {
      // 연결선이 아닌 빈 공간에서만 새 노드 생성
      this.createNodeAt(x, y);
    }
  }

  onKeyDown(e) {
    // Delete 키: 선택된 연결선 삭제
    if (e.key === 'Delete' && this.selectedConnection) {
      this.deleteConnection(this.selectedConnection.id);
      e.preventDefault();
    }

    // Esc 키: 연결 모드 취소
    if (e.key === 'Escape' && this.isConnecting) {
      this.isConnecting = false;
      this.connectingFromNode = null;
      this.tempConnectionEnd = null;
      this.canvas.style.cursor = 'default';
      this.render();
      e.preventDefault();
    }
  }

  // 유틸리티 메서드
  getNodeAt(x, y) {
    return this.nodes.find(node => {
      return x >= node.x - node.width/2 && x <= node.x + node.width/2 &&
             y >= node.y - node.height/2 && y <= node.y + node.height/2;
    });
  }

  getConnectionAt(x, y, threshold = 8) {
    // 점과 곡선 사이의 거리 계산 (근사값)
    return this.connections.find(conn => {
      const fromNode = this.nodes.find(n => n.id === conn.fromNodeId);
      const toNode = this.nodes.find(n => n.id === conn.toNodeId);

      if (!fromNode || !toNode) return false;

      // 곡선의 여러 지점을 샘플링하여 거리 계산
      const samples = 20;
      for (let i = 0; i <= samples; i++) {
        const t = i / samples;

        // Bezier 곡선 계산
        const fromX = fromNode.x;
        const fromY = fromNode.y;
        const toX = toNode.x;
        const toY = toNode.y;

        const dx = toX - fromX;
        const dy = toY - fromY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const offset = Math.min(distance * 0.3, 80);

        const midX = (fromX + toX) / 2;
        const midY = (fromY + toY) / 2;
        const normalX = -dy / distance;
        const normalY = dx / distance;
        const cpX = midX + normalX * offset;
        const cpY = midY + normalY * offset;

        // Quadratic Bezier 곡선 상의 점
        const pointX = (1-t)*(1-t)*fromX + 2*(1-t)*t*cpX + t*t*toX;
        const pointY = (1-t)*(1-t)*fromY + 2*(1-t)*t*cpY + t*t*toY;

        // 마우스 위치와의 거리
        const dist = Math.sqrt((x - pointX)**2 + (y - pointY)**2);
        if (dist < threshold) {
          return true;
        }
      }
      return false;
    });
  }

  deleteConnection(connectionId) {
    showConfirmModal('연결선을 삭제하시겠습니까?', async () => {
      try {
        const url = `/api/v1/teams/${this.teamId}/mindmaps/${this.mindmapId}/connections/${connectionId}/`;
        const response = await fetch(url, {
          method: 'DELETE',
          headers: {
            'X-CSRFToken': this.getCSRFToken()
          }
        });

        const data = await response.json();

        if (data.success) {
          this.connections = this.connections.filter(c => c.id !== connectionId);
          this.selectedConnection = null;

          // WebSocket으로 브로드캐스트
          if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
              type: 'connection_delete',
              connection_id: connectionId
            }));
          }

          showDjangoToast(data.message, 'success');
          this.render();
        } else {
          showDjangoToast(data.error || '연결선 삭제에 실패했습니다.', 'error');
        }
      } catch (error) {
        console.error('연결선 삭제 오류:', error);
        showDjangoToast('연결선 삭제 중 오류가 발생했습니다.', 'error');
      }
    });
  }

  // 팬 제한 계산
  calculatePanLimits() {
    const virtualWidth = this.VIRTUAL_CANVAS.width * this.scale;
    const virtualHeight = this.VIRTUAL_CANVAS.height * this.scale;

    return {
      minTranslateX: this.canvas.width - virtualWidth,
      maxTranslateX: 0,
      minTranslateY: this.canvas.height - virtualHeight,
      maxTranslateY: 0
    };
  }

  // 팬 제한 적용
  constrainPan(translateX, translateY) {
    const limits = this.calculatePanLimits();

    return {
      x: Math.max(limits.minTranslateX, Math.min(limits.maxTranslateX, translateX)),
      y: Math.max(limits.minTranslateY, Math.min(limits.maxTranslateY, translateY))
    };
  }

  updateNodePosition(nodeId, x, y) {
    const node = this.nodes.find(n => n.id === nodeId);
    if (node) {
      node.x = x;
      node.y = y;
      this.render();
    }
  }

  updateUserCursor(userId, username, x, y) {
    // 기존 사용자 정보 유지하면서 위치만 업데이트
    const existingUser = this.activeUsers.get(userId);
    if (existingUser) {
      existingUser.x = x;
      existingUser.y = y;
    } else {
      // 새 사용자인 경우 추가 (본인이 아닌 경우만)
      if (userId !== this.currentUser.userId) {
        this.activeUsers.set(userId, {
          username,
          x,
          y,
          isCurrentUser: false
        });
      }
    }
    this.renderUserCursors();
  }

  zoom(factor) {
    const centerX = this.canvas.width / 2;
    const centerY = this.canvas.height / 2;

    // 가상 캔버스 크기에 맞춘 줌 범위 조정
    // 최소 스케일: 가상 캔버스가 화면을 완전히 채우는 크기 (줌아웃 제한)
    const minScale = Math.max(
      this.canvas.width / this.VIRTUAL_CANVAS.width,
      this.canvas.height / this.VIRTUAL_CANVAS.height
    );

    const maxScale = 5.0; // 최대 5배까지 확대 가능

    const newScale = Math.min(Math.max(minScale, this.scale * factor), maxScale);

    this.translateX = centerX - (centerX - this.translateX) * (newScale / this.scale);
    this.translateY = centerY - (centerY - this.translateY) * (newScale / this.scale);
    this.scale = newScale;

    // 줌 후 팬 제한 적용
    const constrained = this.constrainPan(this.translateX, this.translateY);
    this.translateX = constrained.x;
    this.translateY = constrained.y;

    this.render();
  }

  setInitialView() {
    // 초기 뷰: 가상 캔버스 중심을 2.5배 확대하여 표시
    const scaleX = this.canvas.width / this.VIRTUAL_CANVAS.width;
    const scaleY = this.canvas.height / this.VIRTUAL_CANVAS.height;
    this.scale = Math.min(scaleX, scaleY) * 2.5; // 2.5배 확대

    // 가상 캔버스의 중심이 화면 중심에 오도록 조정
    const centerX = this.VIRTUAL_CANVAS.width / 2;  // 가상 캔버스 중심 X (2700)
    const centerY = this.VIRTUAL_CANVAS.height / 2; // 가상 캔버스 중심 Y (1800)

    this.translateX = this.canvas.width / 2 - centerX * this.scale;
    this.translateY = this.canvas.height / 2 - centerY * this.scale;

    this.render();
  }

  resetView() {
    // 리셋: 초기 뷰와 동일하게 설정 (가상 캔버스 중심을 2.5배 확대)
    const scaleX = this.canvas.width / this.VIRTUAL_CANVAS.width;
    const scaleY = this.canvas.height / this.VIRTUAL_CANVAS.height;
    this.scale = Math.min(scaleX, scaleY) * 2.5; // 2.5배 확대

    // 가상 캔버스의 중심이 화면 중심에 오도록 조정
    const centerX = this.VIRTUAL_CANVAS.width / 2;  // 가상 캔버스 중심 X (2700)
    const centerY = this.VIRTUAL_CANVAS.height / 2; // 가상 캔버스 중심 Y (1800)

    this.translateX = this.canvas.width / 2 - centerX * this.scale;
    this.translateY = this.canvas.height / 2 - centerY * this.scale;

    this.render();
  }

  updateConnectionStatus(connected) {
    const status = document.getElementById('connectionStatus');
    if (connected) {
      status.className = 'connection-status connected';
      status.textContent = '실시간 연결됨';
    } else {
      status.className = 'connection-status disconnected';
      status.textContent = '연결 끊어짐';
    }
  }

  updateActiveUsers() {
    const userList = document.getElementById('userList');
    const users = Array.from(this.activeUsers.values()).map(user => {
      if (user.isCurrentUser) {
        return `${user.username} (본인)`;
      }
      return user.username;
    });

    if (users.length === 0) {
      userList.textContent = '연결 중...';
    } else if (users.length === 1) {
      userList.textContent = users[0]; // "김철수 (본인)" 형태
    } else {
      userList.textContent = `${users.join(', ')} (${users.length}명)`;
    }
  }

  createNodeAt(x, y) {
    // 가상 캔버스 경계 내로 좌표 제한
    const constrainedX = Math.max(this.VIRTUAL_CANVAS.minX, Math.min(this.VIRTUAL_CANVAS.maxX, x));
    const constrainedY = Math.max(this.VIRTUAL_CANVAS.minY, Math.min(this.VIRTUAL_CANVAS.maxY, y));

    // 모달 열기
    const modal = document.getElementById('nodeModal');
    const form = document.getElementById('nodeForm');

    // 제한된 좌표 설정
    form.querySelector('[name="posX"]').value = Math.round(constrainedX);
    form.querySelector('[name="posY"]').value = Math.round(constrainedY);

    // 폼 초기화
    form.querySelector('#nodeTitle').value = '';
    form.querySelector('#nodeContent').value = '';

    // 모달 표시 (공통 모달 CSS 사용)
    modal.classList.add('active');

    // 첫 번째 입력 필드에 포커스 (애니메이션 후)
    setTimeout(() => {
      form.querySelector('#nodeTitle').focus();
    }, 300);
  }

  // 렌더링 메서드
  render() {
    this.ctx.save();

    // 캔버스 클리어
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // 변환 적용
    this.ctx.translate(this.translateX, this.translateY);
    this.ctx.scale(this.scale, this.scale);

    // 배경 그리드 표시
    this.renderGrid();

    // 가상 캔버스 경계 표시
    this.renderVirtualCanvasBounds();

    // 연결선 그리기 (선만, 화살표 제외)
    this.renderConnections();

    // 임시 연결선 그리기 (연결 모드 중)
    if (this.isConnecting && this.tempConnectionEnd) {
      this.renderTempConnection();
    }

    // 노드 그리기
    this.renderNodes();

    // 화살표 그리기 (노드 위에 표시)
    this.renderArrows();

    this.ctx.restore();

    // 사용자 커서 렌더링 (변환 영향 없음)
    this.renderUserCursors();
  }

  renderGrid() {
    const gridSize = 50; // 그리드 간격 (픽셀)

    // 현재 뷰포트에서 보이는 영역 계산
    const startX = Math.floor(-this.translateX / this.scale / gridSize) * gridSize;
    const endX = Math.ceil((this.canvas.width - this.translateX) / this.scale / gridSize) * gridSize;
    const startY = Math.floor(-this.translateY / this.scale / gridSize) * gridSize;
    const endY = Math.ceil((this.canvas.height - this.translateY) / this.scale / gridSize) * gridSize;

    this.ctx.strokeStyle = 'rgba(200, 200, 200, 0.3)';
    this.ctx.lineWidth = 1;
    this.ctx.setLineDash([]);

    // 수직선 그리기
    for (let x = startX; x <= endX; x += gridSize) {
      // 가상 캔버스 영역 내에서만 그리드 표시
      if (x >= this.VIRTUAL_CANVAS.minX && x <= this.VIRTUAL_CANVAS.maxX) {
        this.ctx.beginPath();
        this.ctx.moveTo(x, Math.max(startY, this.VIRTUAL_CANVAS.minY));
        this.ctx.lineTo(x, Math.min(endY, this.VIRTUAL_CANVAS.maxY));
        this.ctx.stroke();
      }
    }

    // 수평선 그리기
    for (let y = startY; y <= endY; y += gridSize) {
      // 가상 캔버스 영역 내에서만 그리드 표시
      if (y >= this.VIRTUAL_CANVAS.minY && y <= this.VIRTUAL_CANVAS.maxY) {
        this.ctx.beginPath();
        this.ctx.moveTo(Math.max(startX, this.VIRTUAL_CANVAS.minX), y);
        this.ctx.lineTo(Math.min(endX, this.VIRTUAL_CANVAS.maxX), y);
        this.ctx.stroke();
      }
    }
  }

  renderVirtualCanvasBounds() {
    // 가상 캔버스 경계를 미묘한 테두리로 표시
    const opacity = this.showBoundaryFeedback ? 0.8 : 0.3;
    const lineWidth = this.showBoundaryFeedback ? 3 : 2;

    this.ctx.strokeStyle = `rgba(166, 176, 208, ${opacity})`;
    this.ctx.lineWidth = lineWidth;
    this.ctx.setLineDash([10, 5]); // 점선 스타일

    this.ctx.strokeRect(
      this.VIRTUAL_CANVAS.minX,
      this.VIRTUAL_CANVAS.minY,
      this.VIRTUAL_CANVAS.width,
      this.VIRTUAL_CANVAS.height
    );

    // 경계 도달시 추가 시각적 피드백
    if (this.showBoundaryFeedback) {
      this.ctx.fillStyle = 'rgba(255, 107, 107, 0.1)';
      this.ctx.fillRect(
        this.VIRTUAL_CANVAS.minX,
        this.VIRTUAL_CANVAS.minY,
        this.VIRTUAL_CANVAS.width,
        this.VIRTUAL_CANVAS.height
      );
    }

    // 선 스타일 초기화
    this.ctx.setLineDash([]);
  }

  renderConnections() {
    this.connections.forEach(conn => {
      const fromNode = this.nodes.find(n => n.id === conn.fromNodeId);
      const toNode = this.nodes.find(n => n.id === conn.toNodeId);

      if (fromNode && toNode) {
        // 호버/선택 상태에 따른 스타일링
        const isHovered = this.hoveredConnection && this.hoveredConnection.id === conn.id;
        const isSelected = this.selectedConnection && this.selectedConnection.id === conn.id;

        if (isHovered) {
          this.ctx.strokeStyle = '#ff6b6b';
          this.ctx.lineWidth = 4;
        } else if (isSelected) {
          this.ctx.strokeStyle = '#4dabf7';
          this.ctx.lineWidth = 3;
        } else {
          this.ctx.strokeStyle = '#a6b0d0';
          this.ctx.lineWidth = 2;
        }

        // 점선 초기화 (실선으로)
        this.ctx.setLineDash([]);

        // Bezier 곡선으로 연결선만 그리기 (화살표 제외)
        this.drawCurvedConnectionLine(fromNode, toNode);
      }
    });
  }

  renderArrows() {
    // 모든 연결선의 화살표를 노드 위에 그리기
    this.connections.forEach(conn => {
      const fromNode = this.nodes.find(n => n.id === conn.fromNodeId);
      const toNode = this.nodes.find(n => n.id === conn.toNodeId);

      if (fromNode && toNode) {
        // 호버/선택 상태에 따른 스타일링
        const isHovered = this.hoveredConnection && this.hoveredConnection.id === conn.id;
        const isSelected = this.selectedConnection && this.selectedConnection.id === conn.id;

        if (isHovered) {
          this.ctx.strokeStyle = '#ff6b6b';
        } else if (isSelected) {
          this.ctx.strokeStyle = '#4dabf7';
        } else {
          this.ctx.strokeStyle = '#a6b0d0';
        }

        // drawCurvedConnectionLine과 동일한 로직
        const centerA = { x: fromNode.x, y: fromNode.y };
        const centerB = { x: toNode.x, y: toNode.y };

        const dx = centerB.x - centerA.x;
        const dy = centerB.y - centerA.y;
        const start = this.getRoundRectConnectionPoint(fromNode, dx, dy);
        const end = this.getRoundRectConnectionPoint(toNode, -dx, -dy);

        // 제어점 계산
        const curveStrength = 0.45;  // 곡률 강화
        const midX = (start.x + end.x) / 2;
        const midY = (start.y + end.y) / 2;

        const perpX = -(end.y - start.y);
        const perpY = (end.x - start.x);
        const len = Math.sqrt(perpX * perpX + perpY * perpY);

        const nx = perpX / len;
        const ny = perpY / len;

        const controlX = midX + nx * curveStrength * len * 0.2;
        const controlY = midY + ny * curveStrength * len * 0.2;

        // 화살표 그리기
        this.drawArrow(controlX, controlY, end.x, end.y, toNode);
      }
    });
  }

  drawCurvedConnectionLine(fromNode, toNode) {
    // 1️⃣ 노드 중심 계산
    const centerA = { x: fromNode.x, y: fromNode.y };
    const centerB = { x: toNode.x, y: toNode.y };

    // 2️⃣ 경계점 계산 (둥근 모서리 반영)
    const dx = centerB.x - centerA.x;
    const dy = centerB.y - centerA.y;
    const start = this.getRoundRectConnectionPoint(fromNode, dx, dy);
    const end = this.getRoundRectConnectionPoint(toNode, -dx, -dy);

    // 3️⃣ 베지어 곡선 제어점 계산
    const curveStrength = 0.45;  // 곡률 강화
    const midX = (start.x + end.x) / 2;
    const midY = (start.y + end.y) / 2;

    // 수직 방향 벡터 계산
    const perpX = -(end.y - start.y);
    const perpY = (end.x - start.x);
    const len = Math.sqrt(perpX * perpX + perpY * perpY);

    // 단위 벡터로 정규화
    const nx = perpX / len;
    const ny = perpY / len;

    // 제어점 (중간을 기준으로 곡률만큼 이동)
    const controlX = midX + nx * curveStrength * len * 0.2;
    const controlY = midY + ny * curveStrength * len * 0.2;

    // 곡선 그리기
    this.ctx.beginPath();
    this.ctx.moveTo(start.x, start.y);
    this.ctx.quadraticCurveTo(controlX, controlY, end.x, end.y);
    this.ctx.stroke();
  }

  getRoundRectConnectionPoint(node, dx, dy, cornerRadius = 12, offset = 0) {
    const x = node.x;
    const y = node.y;
    const hw = node.width / 2;
    const hh = node.height / 2;
    const angle = Math.atan2(dy, dx);
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);

    // 우선 직사각형 외곽선과 교차
    const scale = Math.min(hw / Math.abs(cos), hh / Math.abs(sin));
    let px = x + cos * scale;
    let py = y + sin * scale;

    // 모서리 영역이면 (곡선 부분) 원호 교차점으로 재계산
    const edgeX = Math.abs(px - x) > hw - cornerRadius;
    const edgeY = Math.abs(py - y) > hh - cornerRadius;

    if (edgeX && edgeY) {
      const cx = x + (hw - cornerRadius) * Math.sign(cos);
      const cy = y + (hh - cornerRadius) * Math.sign(sin);
      const r = cornerRadius;

      // 선과 원 교차 계산
      const a = dx * dx + dy * dy;
      const b = 2 * (dx * (x - cx) + dy * (y - cy));
      const c = (x - cx) ** 2 + (y - cy) ** 2 - r * r;
      const disc = b * b - 4 * a * c;
      if (disc >= 0) {
        const t = (-b + Math.sqrt(disc)) / (2 * a);
        px = x + dx * t;
        py = y + dy * t;
      }
    }

    // offset만큼 안쪽으로 이동
    if (offset > 0) {
      px -= cos * offset;
      py -= sin * offset;
    }

    return { x: px, y: py };
  }

  drawArrow(cpX, cpY, toEdgeX, toEdgeY, toNode) {
    // 화살표 방향 계산 (제어점에서 도착 경계점으로)
    const dx = toEdgeX - cpX;
    const dy = toEdgeY - cpY;
    const angle = Math.atan2(dy, dx);

    // 화살표 크기
    const arrowLength = 15;
    const arrowAngle = Math.PI / 7;

    // 화살표 날개 계산
    const leftX = toEdgeX - Math.cos(angle - arrowAngle) * arrowLength;
    const leftY = toEdgeY - Math.sin(angle - arrowAngle) * arrowLength;
    const rightX = toEdgeX - Math.cos(angle + arrowAngle) * arrowLength;
    const rightY = toEdgeY - Math.sin(angle + arrowAngle) * arrowLength;

    // 화살표 그리기 (채워진 삼각형)
    this.ctx.beginPath();
    this.ctx.moveTo(toEdgeX, toEdgeY);
    this.ctx.lineTo(leftX, leftY);
    this.ctx.lineTo(rightX, rightY);
    this.ctx.closePath();
    this.ctx.fillStyle = this.ctx.strokeStyle;
    this.ctx.fill();
  }

  renderTempConnection() {
    // 임시 연결선 (점선 스타일)
    this.ctx.strokeStyle = '#4dabf7';
    this.ctx.lineWidth = 2;
    this.ctx.setLineDash([5, 5]); // 점선

    const fromNode = this.connectingFromNode;
    const toX = this.tempConnectionEnd.x;
    const toY = this.tempConnectionEnd.y;

    // 곡선으로 그리기
    const fromX = fromNode.x;
    const fromY = fromNode.y;
    const dx = toX - fromX;
    const dy = toY - fromY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const offset = Math.min(distance * 0.3, 80);

    const midX = (fromX + toX) / 2;
    const midY = (fromY + toY) / 2;
    const normalX = -dy / distance;
    const normalY = dx / distance;
    const cp1X = midX + normalX * offset;
    const cp1Y = midY + normalY * offset;

    this.ctx.beginPath();
    this.ctx.moveTo(fromX, fromY);
    this.ctx.quadraticCurveTo(cp1X, cp1Y, toX, toY);
    this.ctx.stroke();

    // 점선 초기화
    this.ctx.setLineDash([]);
  }

  async createConnection(fromNodeId, toNodeId) {
    try {
      const response = await fetch(`/api/v1/teams/${this.teamId}/mindmaps/${this.mindmapId}/connections/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken()
        },
        body: JSON.stringify({
          from_node_id: fromNodeId,
          to_node_id: toNodeId
        })
      });

      const data = await response.json();

      if (data.success) {
        // 연결선 추가
        this.connections.push({
          id: data.connection.id,
          fromNodeId: data.connection.from_node_id,
          toNodeId: data.connection.to_node_id
        });

        // WebSocket으로 브로드캐스트
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(JSON.stringify({
            type: 'connection_create',
            connection_id: data.connection.id,
            from_node_id: fromNodeId,
            to_node_id: toNodeId
          }));
        }

        showDjangoToast(data.message, 'success');
        this.render();
      } else {
        showDjangoToast(data.error || '연결 생성에 실패했습니다.', 'error');
      }
    } catch (error) {
      console.error('연결 생성 오류:', error);
      showDjangoToast('연결 생성 중 오류가 발생했습니다.', 'error');
    }
  }

  getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  renderNodes() {
    // 노드 렌더링 (상세 로그는 DEBUG_RENDER = true일 때만)
    const DEBUG_RENDER = false;
    if (DEBUG_RENDER) {
      console.log(`🎨 renderNodes 호출됨 - 총 ${this.nodes.length}개 노드 렌더링`);
    }

    this.nodes.forEach((node, index) => {
      if (DEBUG_RENDER) {
        console.log(`  노드 #${index + 1} - ID: ${node.id}, 좌표: (${node.x}, ${node.y}), 크기: ${node.width}x${node.height}`);
      }

      const x = node.x - node.width / 2;
      const y = node.y - node.height / 2;
      const radius = 12; // 둥근 모서리 반지름

      // 그림자 효과
      this.ctx.save();
      this.ctx.shadowColor = 'rgba(0, 0, 0, 0.15)';
      this.ctx.shadowBlur = 8;
      this.ctx.shadowOffsetX = 0;
      this.ctx.shadowOffsetY = 4;

      // 둥근 사각형 노드 배경 (은은한 그라데이션)
      const bgGradient = this.ctx.createLinearGradient(x, y, x, y + node.height);
      bgGradient.addColorStop(0, '#f8fafc');
      bgGradient.addColorStop(1, '#e2e8f0');

      this.ctx.fillStyle = bgGradient;
      this.ctx.beginPath();
      this.ctx.roundRect(x, y, node.width, node.height, radius);
      this.ctx.fill();

      this.ctx.restore();

      // 그라데이션 테두리
      const gradient = this.ctx.createLinearGradient(x, y, x, y + node.height);
      gradient.addColorStop(0, '#667eea');
      gradient.addColorStop(1, '#764ba2');

      this.ctx.strokeStyle = gradient;
      this.ctx.lineWidth = 2;
      this.ctx.beginPath();
      this.ctx.roundRect(x, y, node.width, node.height, radius);
      this.ctx.stroke();

      // 노드 제목 텍스트
      this.ctx.fillStyle = '#2d3748';
      this.ctx.font = 'bold 14px GmarketSansMedium, sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.textBaseline = 'middle';

      // 텍스트 길이에 따른 줄바꿈 처리
      const maxWidth = node.width - 16;
      const lines = this.wrapText(node.title, maxWidth);
      const lineHeight = 16;
      const totalHeight = lines.length * lineHeight;
      const startY = node.y - totalHeight / 2 + lineHeight / 2;

      lines.forEach((line, index) => {
        this.ctx.fillText(line, node.x, startY + index * lineHeight);
      });
    });
  }

  // 텍스트 줄바꿈 헬퍼 함수
  wrapText(text, maxWidth) {
    const words = text.split(' ');
    const lines = [];
    let currentLine = words[0];

    for (let i = 1; i < words.length; i++) {
      const word = words[i];
      const width = this.ctx.measureText(currentLine + ' ' + word).width;
      if (width < maxWidth) {
        currentLine += ' ' + word;
      } else {
        lines.push(currentLine);
        currentLine = word;
      }
    }
    lines.push(currentLine);
    return lines;
  }

  renderUserCursors() {
    // DOM에서 기존 커서들 제거
    document.querySelectorAll('.user-cursor').forEach(el => el.remove());

    this.activeUsers.forEach((user, userId) => {
      const cursor = document.createElement('div');
      cursor.className = 'user-cursor';
      cursor.setAttribute('data-username', user.username);

      // 화면 좌표로 변환
      const screenX = user.x * this.scale + this.translateX;
      const screenY = user.y * this.scale + this.translateY;

      cursor.style.left = screenX + 'px';
      cursor.style.top = screenY + 'px';
      cursor.style.color = this.getUserColor(userId);
      cursor.style.borderColor = this.getUserColor(userId);

      document.body.appendChild(cursor);
    });
  }

  getUserColor(userId) {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3'];
    return colors[userId % colors.length];
  }
}

// 모달 관련 이벤트 핸들러
function initModalEvents() {
  const modal = document.getElementById('nodeModal');
  const closeBtn = document.getElementById('closeModal');
  const cancelBtn = document.getElementById('cancelBtn');
  const form = document.getElementById('nodeForm');

  // 모달 닫기 함수 (공통 모달 CSS 사용)
  function closeModal() {
    modal.classList.remove('active');
  }

  // 닫기 버튼 클릭
  closeBtn.addEventListener('click', closeModal);
  cancelBtn.addEventListener('click', closeModal);

  // 모달 외부 클릭시 닫기
  modal.addEventListener('click', function(e) {
    if (e.target === modal) {
      closeModal();
    }
  });

  // ESC 키로 모달 닫기
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      e.preventDefault();
      closeModal();
    }
  });

  // 입력 필드 에러 상태 제거 (입력 시)
  const titleInput = form.querySelector('#nodeTitle');
  const contentInput = form.querySelector('#nodeContent');

  if (titleInput) {
    titleInput.addEventListener('input', () => clearFieldError(titleInput));
  }
  if (contentInput) {
    contentInput.addEventListener('input', () => clearFieldError(contentInput));
  }

  // 폼 제출 처리 (AJAX 방식)
  form.addEventListener('submit', async function(e) {
    e.preventDefault(); // 기본 폼 제출 동작 방지

    // 필수 필드 검증
    const isValid = validateRequiredFields([
      { input: titleInput, message: '노드 제목을 입력해주세요.' },
      { input: contentInput, message: '노드 내용을 입력해주세요.' }
    ]);

    if (!isValid) {
      return;
    }

    const formData = new FormData(form);
    const data = {
      posX: parseInt(formData.get('posX')),
      posY: parseInt(formData.get('posY')),
      title: formData.get('title'),
      content: formData.get('content')
    };

    try {
      const editor = window.mindmapEditorInstance;
      if (!editor) {
        console.error('MindmapEditor 인스턴스를 찾을 수 없습니다.');
        return;
      }

      const url = `/api/v1/teams/${editor.teamId}/mindmaps/${editor.mindmapId}/nodes/`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': editor.getCSRFToken()
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (response.ok) {
        showDjangoToast(result.message || '노드가 생성되었습니다.', 'success');

        // 새 노드를 로컬에 추가
        editor.nodes.push({
          id: result.node.id,
          x: result.node.posX,
          y: result.node.posY,
          title: result.node.title,
          content: result.node.content,
          width: 120,
          height: 60
        });

        editor.render();
        closeModal();

        // WebSocket으로 다른 사용자들에게 알림
        if (editor.socket && editor.socket.readyState === WebSocket.OPEN) {
          editor.socket.send(JSON.stringify({
            type: 'node_create',
            node_id: result.node.id,
            posX: result.node.posX,
            posY: result.node.posY,
            title: result.node.title,
            content: result.node.content
          }));
        }
      } else {
        showDjangoToast(result.error || '노드 생성에 실패했습니다.', 'error');
      }
    } catch (error) {
      console.error('노드 생성 중 오류:', error);
      showDjangoToast('노드 생성 중 오류가 발생했습니다.', 'error');
    }
  });
}

// 마인드맵 에디터 초기화 함수
function initMindmapEditor(teamId, mindmapId, currentUser) {
  const mindmapEditor = new MindmapEditor(teamId, mindmapId, currentUser);
  window.mindmapEditorInstance = mindmapEditor; // 전역 변수로 저장
  initModalEvents();
  return mindmapEditor;
}

// 전역 변수로 에디터 인스턴스 노출
window.MindmapEditor = MindmapEditor;
window.initMindmapEditor = initMindmapEditor;