from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from .models import Mindmap, Node, NodeConnection, Comment
from teams.models import Team
from accounts.models import User


class MindmapService:
    """
    마인드맵 관련 비즈니스 로직을 처리하는 서비스 클래스
    
    주요 책임:
    - 마인드맵 CRUD 및 권한 관리
    - 노드 생성/삭제/연결 관리
    - JSON 기반 추천 시스템
    - 댓글 관리 시스템
    """
    
    # ================================
    # 마인드맵 관리 메서드
    # ================================
    
    def create_mindmap(self, team_id, title, creator):
        """
        새로운 마인드맵을 생성합니다.
        
        Args:
            team_id (int): 팀 ID
            title (str): 마인드맵 제목
            creator (User): 생성자
            
        Returns:
            Mindmap: 생성된 마인드맵 객체
            
        Raises:
            ValueError: 제목이 비어있거나 유효하지 않은 경우
            ValidationError: 팀이 존재하지 않거나 권한이 없는 경우
        """
        if not title or not title.strip():
            raise ValueError('마인드맵 제목을 입력해주세요.')
        
        team = get_object_or_404(Team, pk=team_id)
        
        # 팀 멤버 권한 검증은 뷰에서 Mixin으로 처리되므로 여기서는 생략
        
        return Mindmap.objects.create(
            title=title.strip(),
            team=team
        )
    
    def delete_mindmap(self, mindmap_id, user):
        """
        마인드맵을 삭제합니다.
        
        Args:
            mindmap_id (int): 마인드맵 ID
            user (User): 삭제를 요청한 사용자
            
        Returns:
            str: 삭제된 마인드맵 제목
            
        Raises:
            ValidationError: 권한이 없거나 마인드맵이 존재하지 않는 경우
        """
        mindmap = get_object_or_404(Mindmap, pk=mindmap_id)
        
        # 팀장 권한 검증은 뷰에서 Mixin으로 처리되므로 여기서는 생략
        
        mindmap_title = mindmap.title
        mindmap.delete()
        
        return mindmap_title
    
    def get_mindmap_with_nodes(self, mindmap_id):
        """
        마인드맵과 관련된 모든 노드, 연결선을 최적화된 쿼리로 조회합니다.
        
        Args:
            mindmap_id (int): 마인드맵 ID
            
        Returns:
            dict: {
                'mindmap': Mindmap 객체,
                'nodes': Node 쿼리셋,
                'lines': NodeConnection 쿼리셋
            }
        """
        mindmap = get_object_or_404(Mindmap, pk=mindmap_id)
        
        # 최적화된 쿼리: 관련 객체들을 한번에 조회
        nodes = Node.objects.filter(mindmap=mindmap).select_related('mindmap').order_by('id')
        lines = NodeConnection.objects.filter(mindmap=mindmap).select_related('mindmap').order_by('id')
        
        return {
            'mindmap': mindmap,
            'nodes': nodes,
            'lines': lines
        }
    
    def get_team_mindmaps(self, team_id):
        """
        팀의 모든 마인드맵을 조회합니다.
        
        Args:
            team_id (int): 팀 ID
            
        Returns:
            QuerySet: Mindmap 쿼리셋
        """
        team = get_object_or_404(Team, pk=team_id)
        
        return Mindmap.objects.filter(team=team).select_related('team').order_by('-id')
    
    # ================================
    # 노드 관리 메서드
    # ================================
    
    @transaction.atomic
    def create_node(self, mindmap_id, node_data, creator):
        """
        새로운 노드를 생성하고 부모 노드와 연결합니다.
        
        Args:
            mindmap_id (int): 마인드맵 ID
            node_data (dict): {
                'posX': int, 'posY': int,
                'title': str, 'content': str,
                'parent': str (optional) - 부모 노드 제목
            }
            creator (User): 생성자
            
        Returns:
            tuple: (Node 객체, 생성된 연결 메시지)
            
        Raises:
            ValueError: 필수 필드가 누락되거나 유효하지 않은 경우
            ValidationError: 마인드맵이 존재하지 않는 경우
        """
        mindmap = get_object_or_404(Mindmap, pk=mindmap_id)
        
        # 필수 필드 검증
        required_fields = ['posX', 'posY', 'title', 'content']
        for field in required_fields:
            if field not in node_data or not str(node_data[field]).strip():
                raise ValueError(f'{field} 필드는 필수입니다.')
        
        # 좌표값 검증
        try:
            pos_x = int(node_data['posX'])
            pos_y = int(node_data['posY'])
            if pos_x < 0 or pos_y < 0:
                raise ValueError('위치 정보는 0 이상의 숫자여야 합니다.')
        except (ValueError, TypeError):
            raise ValueError('위치 정보는 숫자여야 합니다.')
        
        # 노드 생성
        node = Node.objects.create(
            posX=pos_x,
            posY=pos_y,
            title=node_data['title'].strip(),
            content=node_data['content'].strip(),
            mindmap=mindmap
        )
        
        # 부모 노드 연결 처리
        connection_message = ""
        parent_title = node_data.get('parent')
        if parent_title and parent_title.strip():
            try:
                parent_node = Node.objects.get(title=parent_title.strip(), mindmap=mindmap)
                NodeConnection.objects.create(
                    from_node=node,
                    to_node=parent_node,
                    mindmap=mindmap
                )
                connection_message = f" 부모 노드 '{parent_title}'와 연결되었습니다."
            except Node.DoesNotExist:
                connection_message = " 부모 노드를 찾을 수 없어 연결이 생성되지 않았습니다."
        
        return node, connection_message
    
    def delete_node(self, node_id, user):
        """
        노드를 삭제합니다.
        
        Args:
            node_id (int): 노드 ID
            user (User): 삭제를 요청한 사용자
            
        Returns:
            tuple: (삭제된 노드 제목, 마인드맵 ID)
            
        Raises:
            ValidationError: 노드가 존재하지 않는 경우
        """
        node = get_object_or_404(Node, pk=node_id)
        
        node_title = node.title
        mindmap_id = node.mindmap.id
        
        # 노드 삭제 시 관련 연결도 자동으로 삭제됨 (CASCADE)
        node.delete()
        
        return node_title, mindmap_id
    
    def create_node_connection(self, from_node_id, to_node_id, mindmap_id):
        """
        두 노드 사이의 연결을 생성합니다.
        
        Args:
            from_node_id (int): 시작 노드 ID
            to_node_id (int): 끝 노드 ID
            mindmap_id (int): 마인드맵 ID
            
        Returns:
            NodeConnection: 생성된 연결 객체
            
        Raises:
            ValueError: 노드가 다른 마인드맵에 속하거나 자기 자신과 연결하려는 경우
            ValidationError: 노드가 존재하지 않는 경우
        """
        from_node = get_object_or_404(Node, pk=from_node_id)
        to_node = get_object_or_404(Node, pk=to_node_id)
        mindmap = get_object_or_404(Mindmap, pk=mindmap_id)
        
        # 검증: 같은 마인드맵의 노드들인지 확인
        if from_node.mindmap != mindmap or to_node.mindmap != mindmap:
            raise ValueError('다른 마인드맵의 노드들은 연결할 수 없습니다.')
        
        # 검증: 자기 자신과 연결하려는지 확인
        if from_node_id == to_node_id:
            raise ValueError('노드는 자기 자신과 연결할 수 없습니다.')
        
        # 중복 연결 검증
        if NodeConnection.objects.filter(
            from_node=from_node, 
            to_node=to_node, 
            mindmap=mindmap
        ).exists():
            raise ValueError('이미 연결된 노드들입니다.')
        
        return NodeConnection.objects.create(
            from_node=from_node,
            to_node=to_node,
            mindmap=mindmap
        )
    
    def toggle_node_recommendation(self, node_id, user_id):
        """
        노드의 추천 상태를 토글합니다 (JSON 기반).
        
        Args:
            node_id (int): 노드 ID
            user_id (int): 사용자 ID
            
        Returns:
            tuple: (액션 타입, 현재 추천 수)
            액션 타입: 'added' 또는 'removed'
            
        Raises:
            ValidationError: 노드가 존재하지 않는 경우
        """
        node = get_object_or_404(Node, pk=node_id)
        
        # 추천자 목록 초기화 (None인 경우)
        if node.recommended_users is None:
            node.recommended_users = []
        
        if user_id in node.recommended_users:
            # 추천 취소
            node.recommended_users.remove(user_id)
            node.recommendation_count = max(0, node.recommendation_count - 1)
            action = "removed"
        else:
            # 추천 추가
            node.recommended_users.append(user_id)
            node.recommendation_count += 1
            action = "added"
        
        # 데이터 일관성 보장: 실제 배열 길이와 카운트 동기화
        node.recommendation_count = len(node.recommended_users)
        node.save()
        
        return action, node.recommendation_count
    
    # ================================
    # 댓글 관리 메서드
    # ================================
    
    def create_comment(self, node_id, comment_text, user):
        """
        노드에 댓글을 추가합니다.
        
        Args:
            node_id (int): 노드 ID
            comment_text (str): 댓글 내용
            user (User): 댓글 작성자
            
        Returns:
            Comment: 생성된 댓글 객체
            
        Raises:
            ValueError: 댓글 내용이 비어있는 경우
            ValidationError: 노드가 존재하지 않는 경우
        """
        if not comment_text or not comment_text.strip():
            raise ValueError('댓글 내용을 입력해주세요.')
        
        node = get_object_or_404(Node, pk=node_id)
        
        return Comment.objects.create(
            comment=comment_text.strip(),
            node=node,
            user=user
        )
    
    def get_node_with_comments(self, node_id):
        """
        노드와 관련된 모든 댓글을 조회합니다.
        
        Args:
            node_id (int): 노드 ID
            
        Returns:
            dict: {
                'node': Node 객체,
                'comments': Comment 쿼리셋
            }
        """
        node = get_object_or_404(Node, pk=node_id)
        
        # 최적화된 쿼리: 댓글과 관련 사용자 정보 사전 로딩
        comments = Comment.objects.filter(node=node).select_related('node', 'user').order_by('-id')
        
        return {
            'node': node,
            'comments': comments
        }