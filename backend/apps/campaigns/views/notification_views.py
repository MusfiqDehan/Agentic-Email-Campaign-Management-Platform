"""
Notification views for real-time campaign and system notifications.
"""
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from core.mixins import CustomResponseMixin
from ..models import Notification
from ..serializers import NotificationSerializer


class NotificationListView(CustomResponseMixin, generics.ListAPIView):
    """
    List all notifications for the authenticated user's organization.
    
    GET /api/v1/campaigns/notifications/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """Return notifications for user's organization, ordered by newest first."""
        return Notification.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False
        ).order_by('-created_at')[:50]  # Limit to recent 50 notifications


class UnreadNotificationCountView(CustomResponseMixin, APIView):
    """
    Get count of unread notifications.
    
    GET /api/v1/campaigns/notifications/unread-count/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return count of unread notifications."""
        count = Notification.objects.filter(
            organization=request.user.organization,
            is_read=False,
            is_deleted=False
        ).count()
        
        return self.success_response(data={'count': count})


class MarkNotificationReadView(CustomResponseMixin, APIView):
    """
    Mark a notification as read.
    
    POST /api/v1/campaigns/notifications/<id>/mark-read/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Mark notification as read."""
        notification = get_object_or_404(
            Notification,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        
        notification.mark_as_read()
        
        return self.success_response(
            data=NotificationSerializer(notification).data,
            message="Notification marked as read"
        )


class MarkAllNotificationsReadView(CustomResponseMixin, APIView):
    """
    Mark all notifications as read.
    
    POST /api/v1/campaigns/notifications/mark-all-read/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Mark all unread notifications as read."""
        updated = Notification.objects.filter(
            organization=request.user.organization,
            is_read=False,
            is_deleted=False
        ).update(is_read=True, read_at=timezone.now())
        
        return self.success_response(
            data={'updated_count': updated},
            message=f"{updated} notification(s) marked as read"
        )


class DeleteNotificationView(CustomResponseMixin, APIView):
    """
    Delete (soft delete) a notification.
    
    DELETE /api/v1/campaigns/notifications/<id>/
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        """Soft delete a notification."""
        notification = get_object_or_404(
            Notification,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        
        notification.is_deleted = True
        notification.save(update_fields=['is_deleted'])
        
        return self.success_response(message="Notification deleted")
