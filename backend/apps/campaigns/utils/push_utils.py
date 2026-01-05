"""
Utility functions for sending web push notifications.
"""
import json
import logging
from typing import Dict, Any, Optional
from pywebpush import webpush, WebPushException
from django.conf import settings

logger = logging.getLogger(__name__)


def send_push_notification(
    subscription,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    icon: str = '/icon-192.png',
    badge: str = '/badge-72.png',
    tag: str = 'campaign-update',
    require_interaction: bool = False
) -> bool:
    """
    Send a web push notification to a subscription.
    
    Args:
        subscription: PushSubscription model instance
        title: Notification title
        body: Notification body text
        data: Additional data to send with notification
        icon: URL to notification icon
        badge: URL to notification badge
        tag: Notification tag for grouping
        require_interaction: Whether notification requires user interaction
        
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    if not subscription or not subscription.is_active:
        logger.warning("Attempted to send push to inactive subscription")
        return False
    
    # Prepare notification payload
    payload = json.dumps({
        'title': title,
        'body': body,
        'icon': icon,
        'badge': badge,
        'tag': tag,
        'data': data or {},
        'requireInteraction': require_interaction,
        'timestamp': None  # Will be set by service worker
    })
    
    try:
        # Get VAPID keys from settings
        vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
        vapid_admin_email = getattr(settings, 'VAPID_ADMIN_EMAIL', 'admin@example.com')
        
        if not vapid_private_key:
            logger.error("VAPID_PRIVATE_KEY not configured in settings")
            return False
        
        # Send push notification
        response = webpush(
            subscription_info={
                'endpoint': subscription.endpoint,
                'keys': {
                    'p256dh': subscription.p256dh,
                    'auth': subscription.auth
                }
            },
            data=payload,
            vapid_private_key=vapid_private_key,
            vapid_claims={
                'sub': f'mailto:{vapid_admin_email}'
            }
        )
        
        logger.info(f"Push notification sent successfully to user {subscription.user_id}")
        return True
        
    except WebPushException as e:
        logger.error(f"WebPush failed for subscription {subscription.id}: {e}")
        
        # Handle expired subscriptions
        if e.response and e.response.status_code in [404, 410]:
            logger.info(f"Subscription {subscription.id} expired, marking as inactive")
            subscription.is_active = False
            subscription.save()
        
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error sending push notification: {e}")
        return False


def send_campaign_status_notification(campaign, old_status: str, new_status: str) -> int:
    """
    Send push notifications to all users in organization about campaign status change.
    
    Args:
        campaign: Campaign model instance
        old_status: Previous campaign status
        new_status: New campaign status
        
    Returns:
        int: Number of notifications sent successfully
    """
    from apps.campaigns.models.push_models import PushSubscription
    
    # Get all active subscriptions for users in this organization
    subscriptions = PushSubscription.objects.filter(
        organization=campaign.organization,
        is_active=True
    ).select_related('user')
    
    # Prepare notification content
    title = f"Campaign Update: {campaign.name}"
    body = f"Status changed from {old_status} to {new_status}"
    data = {
        'url': f'/dashboard/campaigns/{campaign.id}',
        'campaign_id': str(campaign.id),
        'campaign_name': campaign.name,
        'old_status': old_status,
        'new_status': new_status,
    }
    
    # Send to all subscriptions
    sent_count = 0
    for subscription in subscriptions:
        if send_push_notification(
            subscription=subscription,
            title=title,
            body=body,
            data=data,
            require_interaction=False
        ):
            sent_count += 1
    
    logger.info(f"Sent {sent_count} push notifications for campaign {campaign.id} status change")
    return sent_count
