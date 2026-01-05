"""
Views for push notifications.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from urllib.parse import unquote

from apps.campaigns.models.push_models import PushSubscription
from apps.campaigns.serializers.push_serializers import (
    PushSubscriptionSerializer,
    PushSubscriptionListSerializer
)
from apps.campaigns.utils.push_utils import send_push_notification


class PushSubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing push subscriptions."""
    permission_classes = [IsAuthenticated]
    serializer_class = PushSubscriptionSerializer
    
    def get_queryset(self):
        """Get subscriptions for current user."""
        return PushSubscription.objects.filter(
            user=self.request.user,
            is_active=True
        )
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'list':
            return PushSubscriptionListSerializer
        return PushSubscriptionSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Delete subscription by endpoint (URL encoded)."""
        endpoint = unquote(kwargs.get('pk', ''))
        
        subscription = get_object_or_404(
            PushSubscription,
            user=request.user,
            endpoint=endpoint
        )
        
        subscription.is_active = False
        subscription.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'])
    def test(self, request):
        """Send a test push notification."""
        endpoint = request.data.get('endpoint')
        
        if not endpoint:
            return Response(
                {'error': 'Endpoint is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            subscription = PushSubscription.objects.get(
                user=request.user,
                endpoint=endpoint,
                is_active=True
            )
            
            # Send test notification
            success = send_push_notification(
                subscription=subscription,
                title='Test Notification',
                body='This is a test push notification from your Email Campaign Platform!',
                data={
                    'url': '/dashboard/campaigns',
                    'test': True
                }
            )
            
            if success:
                return Response({'message': 'Test notification sent successfully'})
            else:
                return Response(
                    {'error': 'Failed to send test notification'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except PushSubscription.DoesNotExist:
            return Response(
                {'error': 'Subscription not found'},
                status=status.HTTP_404_NOT_FOUND
            )
