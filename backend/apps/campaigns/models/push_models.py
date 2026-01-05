"""
Push notification subscription model.
"""
from django.db import models
from apps.utils.base_models import BaseModel


class PushSubscription(BaseModel):
    """
    Model to store web push notification subscriptions for users.
    """
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )
    organization = models.ForeignKey(
        'authentication.Organization',
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )
    endpoint = models.TextField(unique=True)
    p256dh = models.CharField(max_length=255, help_text="Public key for encryption")
    auth = models.CharField(max_length=255, help_text="Authentication secret")
    is_active = models.BooleanField(default=True)
    user_agent = models.TextField(blank=True, null=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'push_subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['organization', 'is_active']),
        ]

    def __str__(self):
        return f"Push subscription for {self.user.email}"
