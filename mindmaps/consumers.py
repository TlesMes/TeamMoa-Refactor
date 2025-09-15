import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import get_object_or_404

from .models import Mindmap, Node, NodeConnection
from teams.models import TeamUser
from .services import MindmapService

logger = logging.getLogger(__name__)

class MindmapConsumer(AsyncWebsocketConsumer):
    """
    마인드맵 실시간 협업을 위한 WebSocket Consumer
    
    기능:
    - 마인드맵 룸 참가/퇴장
    - 실시간 노드 위치 동기화
    - 노드 생성/삭제 동기화
    - 사용자 커서 위치 공유
    """
    
    async def connect(self):
        """WebSocket 연결 시 실행"""
        self.mindmap_id = self.scope['url_route']['kwargs']['mindmap_id']
        self.team_id = self.scope['url_route']['kwargs']['team_id']
        self.room_group_name = f'mindmap_{self.mindmap_id}'
        self.user = self.scope.get('user', AnonymousUser())
        
        # 사용자 인증 및 권한 확인
        if not await self.check_permissions():
            await self.close()
            return
        
        # 룸 그룹에 참가
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.user.username} joined mindmap {self.mindmap_id}")
        
        # 다른 사용자들에게 새 사용자 알림
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )
    
    async def disconnect(self, close_code):
        """WebSocket 연결 종료 시 실행"""
        if hasattr(self, 'room_group_name'):
            # 다른 사용자들에게 사용자 퇴장 알림
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user.id,
                    'username': self.user.username
                }
            )
            
            # 룸 그룹에서 제거
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        logger.info(f"User {getattr(self.user, 'username', 'Anonymous')} left mindmap {self.mindmap_id}")
    
    async def receive(self, text_data):
        """클라이언트로부터 메시지 수신"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # 메시지 타입별 처리
            if message_type == 'node_move':
                await self.handle_node_move(data)
            elif message_type == 'node_create':
                await self.handle_node_create(data)
            elif message_type == 'node_delete':
                await self.handle_node_delete(data)
            elif message_type == 'cursor_move':
                await self.handle_cursor_move(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def handle_node_move(self, data):
        """노드 이동 처리"""
        node_id = data.get('node_id')
        x = data.get('x')
        y = data.get('y')
        
        if node_id is None or x is None or y is None:
            return
        
        # 데이터베이스 업데이트
        success = await self.update_node_position(node_id, x, y)
        if success:
            # 다른 사용자들에게 브로드캐스트 (발신자 제외)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'node_moved',
                    'node_id': node_id,
                    'x': x,
                    'y': y,
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'sender_channel': self.channel_name  # 발신자 구분용
                }
            )
    
    async def handle_node_create(self, data):
        """노드 생성 처리"""
        # 향후 구현
        pass
    
    async def handle_node_delete(self, data):
        """노드 삭제 처리"""
        # 향후 구현
        pass
    
    async def handle_cursor_move(self, data):
        """커서 이동 처리"""
        x = data.get('x')
        y = data.get('y')
        
        if x is None or y is None:
            return
        
        # 다른 사용자들에게 커서 위치 브로드캐스트
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'cursor_moved',
                'x': x,
                'y': y,
                'user_id': self.user.id,
                'username': self.user.username,
                'sender_channel': self.channel_name
            }
        )
    
    # 그룹 메시지 핸들러들
    async def user_joined(self, event):
        """사용자 참가 알림"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    async def user_left(self, event):
        """사용자 퇴장 알림"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    async def node_moved(self, event):
        """노드 이동 알림"""
        # 발신자에게는 전송하지 않음
        if event.get('sender_channel') != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'node_moved',
                'node_id': event['node_id'],
                'x': event['x'],
                'y': event['y'],
                'user_id': event['user_id'],
                'username': event['username']
            }))
    
    async def cursor_moved(self, event):
        """커서 이동 알림"""
        # 발신자에게는 전송하지 않음
        if event.get('sender_channel') != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'cursor_moved',
                'x': event['x'],
                'y': event['y'],
                'user_id': event['user_id'],
                'username': event['username']
            }))
    
    # 데이터베이스 작업 (동기 → 비동기 변환)
    @database_sync_to_async
    def check_permissions(self):
        """사용자 권한 확인"""
        if self.user.is_anonymous:
            return False
        
        try:
            # 팀 멤버인지 확인
            TeamUser.objects.get(team_id=self.team_id, user=self.user)
            # 마인드맵이 존재하는지 확인
            Mindmap.objects.get(id=self.mindmap_id, team_id=self.team_id)
            return True
        except (TeamUser.DoesNotExist, Mindmap.DoesNotExist):
            return False
    
    @database_sync_to_async
    def update_node_position(self, node_id, x, y):
        """노드 위치 업데이트"""
        try:
            node = Node.objects.get(
                id=node_id, 
                mindmap_id=self.mindmap_id
            )
            node.posX = float(x)
            node.posY = float(y)
            node.save()
            return True
        except (Node.DoesNotExist, ValueError, TypeError):
            return False