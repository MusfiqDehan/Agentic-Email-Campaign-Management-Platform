"""
WebSocket consumers for real-time notifications.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    
    Users connect to this consumer and join their organization's notification group.
    When notifications are created, they're broadcast to all connected clients in that group.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        # Get token from query string
        query_string = self.scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if not token:
            await self.close(code=4001)
            return
        
        # Authenticate user with JWT token
        self.user = await self.get_user_from_token(token)
        
        if not self.user:
            await self.close(code=4001)
            return
        
        # Get user's organization
        self.organization_id = await self.get_user_organization_id()
        
        if not self.organization_id:
            await self.close(code=4002)
            return
        
        # Join organization notification group
        self.group_name = f"notifications_{self.organization_id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        logger.info(f"WebSocket connected: User {self.user.id} joined {self.group_name}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected: User {self.user.id} left {self.group_name}")
    
    async def receive(self, text_data):
        """
        Handle messages from WebSocket client.
        Currently not used, but could be extended for client->server messages.
        """
        pass
    
    async def notification_message(self, event):
        """
        Handle notification broadcast from group.
        This method is called when a message is sent to the group.
        """
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data']
        }))
    
    async def unread_count_update(self, event):
        """
        Handle unread count updates.
        """
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': event['count']
        }))
    
    async def campaign_status_update(self, event):
        """
        Handle campaign status updates.
        This is called when a campaign's status changes.
        """
        await self.send(text_data=json.dumps({
            'type': 'campaign_status_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_user_from_token(self, token_string):
        """Authenticate user from JWT token."""
        try:
            access_token = AccessToken(token_string)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except Exception as e:
            logger.error(f"Token authentication failed: {e}")
            return None
    
    @database_sync_to_async
    def get_user_organization_id(self):
        """Get user's organization ID."""
        try:
            return str(self.user.organization.id)
        except Exception:
            return None
