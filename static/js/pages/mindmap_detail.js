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
    this.canvas.addEventListener('wheel', (e) => this.onWheel(e));
    this.canvas.addEventListener('dblclick', (e) => this.onDoubleClick(e));

    // 줌 컨트롤
    document.getElementById('zoomIn').addEventListener('click', () => this.zoom(1.2));
    document.getElementById('zoomOut').addEventListener('click', () => this.zoom(0.8));
    document.getElementById('resetZoom').addEventListener('click', () => this.resetView());

    // 키보드 이벤트 (향후 구현)
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
    }
  }

  // 마우스 이벤트 핸들러
  onMouseDown(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - this.translateX) / this.scale;
    const y = (e.clientY - rect.top - this.translateY) / this.scale;

    const node = this.getNodeAt(x, y);

    if (node) {
      // 노드 드래그 시작
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

    if (this.isDragging && this.dragNode) {
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

      // 디버깅: 노드 이동 좌표 출력
      console.log(`노드 ${this.dragNode.id} 이동: (${Math.round(newX)}, ${Math.round(newY)}) ${hitBoundary ? '[경계 제한됨]' : ''}`);

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
      // 마우스 오버 효과
      const node = this.getNodeAt(x, y);
      this.canvas.style.cursor = node ? 'grab' : 'default';
    }
  }

  onMouseUp(e) {
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

  onDoubleClick(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - this.translateX) / this.scale;
    const y = (e.clientY - rect.top - this.translateY) / this.scale;

    const node = this.getNodeAt(x, y);
    if (node) {
      // 노드 상세 페이지로 이동 - window.mindmapUrls에서 URL 가져오기
      if (window.mindmapUrls && window.mindmapUrls.nodeDetail) {
        window.location.href = window.mindmapUrls.nodeDetail.replace('0', node.id);
      }
    } else {
      // 새 노드 생성 (향후 모달로 개선)
      this.createNodeAt(x, y);
    }
  }

  // 유틸리티 메서드
  getNodeAt(x, y) {
    return this.nodes.find(node => {
      return x >= node.x - node.width/2 && x <= node.x + node.width/2 &&
             y >= node.y - node.height/2 && y <= node.y + node.height/2;
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
    // 리셋: 가상 캔버스 전체가 화면에 맞도록 표시
    const scaleX = this.canvas.width / this.VIRTUAL_CANVAS.width;
    const scaleY = this.canvas.height / this.VIRTUAL_CANVAS.height;
    this.scale = Math.min(scaleX, scaleY) * 0.9; // 여백을 위해 90% 크기로

    // 가상 캔버스가 중앙에 오도록 조정
    const scaledWidth = this.VIRTUAL_CANVAS.width * this.scale;
    const scaledHeight = this.VIRTUAL_CANVAS.height * this.scale;

    this.translateX = (this.canvas.width - scaledWidth) / 2;
    this.translateY = (this.canvas.height - scaledHeight) / 2;

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
    form.querySelector('#nodeParent').value = '';

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

    // 연결선 그리기
    this.renderConnections();

    // 노드 그리기
    this.renderNodes();

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
    this.ctx.strokeStyle = '#a6b0d0';
    this.ctx.lineWidth = 2;

    this.connections.forEach(conn => {
      const fromNode = this.nodes.find(n => n.id === conn.fromNodeId);
      const toNode = this.nodes.find(n => n.id === conn.toNodeId);

      if (fromNode && toNode) {
        this.ctx.beginPath();
        this.ctx.moveTo(fromNode.x, fromNode.y);
        this.ctx.lineTo(toNode.x, toNode.y);
        this.ctx.stroke();
      }
    });
  }

  renderNodes() {
    this.nodes.forEach(node => {
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

  onKeyDown(e) {
    // 키보드 단축키 (향후 구현)
    if (e.key === 'Delete' || e.key === 'Backspace') {
      // 선택된 노드 삭제
    } else if (e.key === 'Escape') {
      // 선택 해제
    }
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

  // 폼 제출 후 자동으로 모달 닫기 (페이지 새로고침되므로 실제로는 필요없지만)
  form.addEventListener('submit', function() {
    closeModal();
  });
}

// 마인드맵 에디터 초기화 함수
function initMindmapEditor(teamId, mindmapId, currentUser) {
  const mindmapEditor = new MindmapEditor(teamId, mindmapId, currentUser);
  initModalEvents();
  return mindmapEditor;
}

// 전역 변수로 에디터 인스턴스 노출
window.MindmapEditor = MindmapEditor;
window.initMindmapEditor = initMindmapEditor;