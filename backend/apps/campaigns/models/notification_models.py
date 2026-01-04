"""
Notification models for campaign events and system notifications.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

from apps.authentication.models import Organization
from apps.utils.base_models import BaseModel


class Notification(BaseModel):
    """
    Universal notification model for campaign events and system messages.
    """
    
    TYPE_CHOICES = [
        ('CAMPAIGN_SENT', 'Campaign Sent'),
        ('CAMPAIGN_SCHEDULED', 'Campaign Scheduled'),
        ('CAMPAIGN_FAILED', 'Campaign Failed'),
        ('CONTACT_ADDED', 'Contact Added'),
        ('CONTACT_SUBSCRIBED', 'Contact Subscribed'),
        ('CONTACT_UNSUBSCRIBED', 'Contact Unsubscribed'),
        ('TEMPLATE_UPDATED', 'Template Updated'),
        ('SYSTEM_UPDATE', 'System Update'),
        ('SYSTEM_ALERT', 'System Alert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who receives this notification
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Organization that owns this notification"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text="Specific user (if user-specific notification)"
    )
    
    # Notification content
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related object (optional)
    related_object_type = models.CharField(max_length=50, blank=True, help_text="Type of related object (e.g., 'campaign', 'contact')")
    related_object_id = models.UUIDField(null=True, blank=True, help_text="ID of related object")
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional data (e.g., stats, links)"
    )
    
    # Status
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'is_read', '-created_at']),
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['notification_type', '-created_at']),
        ]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
    
    def __str__(self):
        return f"{self.organization.name} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read and broadcast update via WebSocket."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
            
            # Broadcast unread count update via WebSocket
            try:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer
                
                channel_layer = get_channel_layer()
                group_name = f"notifications_{self.organization.id}"
                
                # Calculate new unread count
                unread_count = Notification.objects.filter(
                    organization=self.organization,
                    is_read=False,
                    is_deleted=False
                ).count()
                
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'unread_count_update',
                        'count': unread_count
                    }
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to broadcast unread count update: {e}")
