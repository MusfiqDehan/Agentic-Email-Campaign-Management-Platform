"""
Django signals for the campaigns app.

Handles audit logging for email provider changes.
"""
import logging
import threading
from django.db.models.signals import pre_save, post_save, post_delete, m2m_changed
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models.provider_models import EmailProvider, ProviderAuditLog
from .models.contact_models import Contact, ContactList
from .models.campaign_models import Campaign
from .models.notification_models import Notification

logger = logging.getLogger(__name__)

# Thread-local storage to capture pre-save state
_provider_pre_save_state = threading.local()


def get_request_from_context():
    """
    Attempt to get the current request from thread-local storage.
    
    This works with middleware that stores the request in thread-local storage.
    Returns None if no request is available.
    """
    try:
        from django.contrib.auth.models import AnonymousUser
        # Try to get request from crum if available
        try:
            from crum import get_current_request
            return get_current_request()
        except ImportError:
            pass
        
        # Fallback: return None if no request available
        return None
    except Exception:
        return None


def get_user_from_context():
    """
    Attempt to get the current user from thread-local storage.
    """
    request = get_request_from_context()
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    return None


@receiver(pre_save, sender=EmailProvider)
def capture_provider_pre_save_state(sender, instance, **kwargs):
    """
    Capture the provider's state before saving for comparison.
    
    This is needed to detect what fields changed during an update.
    """
    if not instance.pk:
        # New instance, nothing to capture
        return
    
    try:
        old_instance = EmailProvider.objects.get(pk=instance.pk)
        
        # Store old values in thread-local storage
        if not hasattr(_provider_pre_save_state, 'instances'):
            _provider_pre_save_state.instances = {}
        
        # Capture relevant fields
        _provider_pre_save_state.instances[str(instance.pk)] = {
            'name': old_instance.name,
            'provider_type': old_instance.provider_type,
            'is_shared': old_instance.is_shared,
            'is_default': old_instance.is_default,
            'priority': old_instance.priority,
            'max_emails_per_minute': old_instance.max_emails_per_minute,
            'max_emails_per_hour': old_instance.max_emails_per_hour,
            'max_emails_per_day': old_instance.max_emails_per_day,
            'health_status': old_instance.health_status,
            'organization_id': str(old_instance.organization_id) if old_instance.organization_id else None,
            'encrypted_config': old_instance.encrypted_config,
        }
    except EmailProvider.DoesNotExist:
        # Instance doesn't exist yet, will be treated as creation
        pass
    except Exception as e:
        logger.warning(f"Failed to capture pre-save state for provider {instance.pk}: {e}")


@receiver(post_save, sender=EmailProvider)
def log_provider_save(sender, instance, created, **kwargs):
    """
    Log provider creation and updates.
    """
    try:
        request = get_request_from_context()
        user = get_user_from_context()
        
        if created:
            # Provider was created
            changed_fields = {
                'name': {'old': None, 'new': instance.name},
                'provider_type': {'old': None, 'new': instance.provider_type},
                'is_shared': {'old': None, 'new': instance.is_shared},
                'is_default': {'old': None, 'new': instance.is_default},
                'priority': {'old': None, 'new': instance.priority},
                'max_emails_per_minute': {'old': None, 'new': instance.max_emails_per_minute},
                'max_emails_per_hour': {'old': None, 'new': instance.max_emails_per_hour},
                'max_emails_per_day': {'old': None, 'new': instance.max_emails_per_day},
            }
            
            # Check if config was provided
            if instance.encrypted_config:
                changed_fields['config'] = {'old': None, 'new': '[SET]'}
            
            ProviderAuditLog.log_action(
                provider=instance,
                action='created',
                user=user,
                request=request,
                changed_fields=changed_fields,
                details=f"Email provider '{instance.name}' created"
            )
            
            logger.info(f"Audit: Provider '{instance.name}' created by {user}")
            
        else:
            # Provider was updated - compare with pre-save state
            old_state = {}
            if hasattr(_provider_pre_save_state, 'instances'):
                old_state = _provider_pre_save_state.instances.pop(str(instance.pk), {})
            
            if not old_state:
                # No pre-save state captured, skip logging
                return
            
            # Compare fields and build changed_fields dict
            changed_fields = {}
            fields_to_check = [
                'name', 'provider_type', 'is_shared', 'is_default', 'priority',
                'max_emails_per_minute', 'max_emails_per_hour', 'max_emails_per_day',
                'health_status'
            ]
            
            for field in fields_to_check:
                old_value = old_state.get(field)
                new_value = getattr(instance, field, None)
                if old_value != new_value:
                    changed_fields[field] = {'old': old_value, 'new': new_value}
            
            # Check if config changed (compare encrypted values)
            old_config = old_state.get('encrypted_config', '')
            new_config = instance.encrypted_config or ''
            if old_config != new_config:
                changed_fields['config'] = {'old': '[SET]' if old_config else None, 'new': '[SET]' if new_config else None}
            
            # Only log if something actually changed
            if changed_fields:
                ProviderAuditLog.log_action(
                    provider=instance,
                    action='updated',
                    user=user,
                    request=request,
                    changed_fields=changed_fields,
                    details=f"Email provider '{instance.name}' updated. Changed: {', '.join(changed_fields.keys())}"
                )
                
                logger.info(f"Audit: Provider '{instance.name}' updated by {user}. Fields: {list(changed_fields.keys())}")
                
    except Exception as e:
        logger.error(f"Failed to log provider save audit: {e}", exc_info=True)


@receiver(post_delete, sender=EmailProvider)
def log_provider_delete(sender, instance, **kwargs):
    """
    Log provider deletion.
    """
    try:
        request = get_request_from_context()
        user = get_user_from_context()
        
        # Create audit log with provider set to None (since it's deleted)
        ProviderAuditLog.objects.create(
            provider=None,
            provider_name=instance.name,
            provider_type=instance.provider_type,
            organization=instance.organization,
            user=user,
            action='deleted',
            changed_fields={
                'name': {'old': instance.name, 'new': None},
                'provider_type': {'old': instance.provider_type, 'new': None},
                'is_shared': {'old': instance.is_shared, 'new': None},
            },
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else '',
            details=f"Email provider '{instance.name}' deleted"
        )
        
        logger.info(f"Audit: Provider '{instance.name}' deleted by {user}")
        
    except Exception as e:
        logger.error(f"Failed to log provider delete audit: {e}", exc_info=True)


def log_provider_health_check(provider, user=None, request=None, is_healthy=None, message=''):
    """
    Manually log a health check action.
    
    Call this from views after performing a health check.
    """
    try:
        ProviderAuditLog.log_action(
            provider=provider,
            action='health_check',
            user=user,
            request=request,
            changed_fields={
                'health_status': {
                    'old': provider.health_status,
                    'new': 'HEALTHY' if is_healthy else 'UNHEALTHY'
                }
            },
            details=f"Health check performed. Result: {'Healthy' if is_healthy else 'Unhealthy'}. {message}"
        )
    except Exception as e:
        logger.error(f"Failed to log health check audit: {e}", exc_info=True)


def log_provider_test_send(provider, user=None, request=None, success=None, 
                           recipient='', message=''):
    """
    Manually log a test send action.
    
    Call this from views after performing a test send.
    """
    try:
        ProviderAuditLog.log_action(
            provider=provider,
            action='test_send',
            user=user,
            request=request,
            changed_fields={},
            details=f"Test email sent to {recipient}. Success: {success}. {message}"
        )
    except Exception as e:
        logger.error(f"Failed to log test send audit: {e}", exc_info=True)
@receiver(m2m_changed, sender=Contact.lists.through)
def update_contact_list_stats_m2m(sender, instance, action, pk_set, **kwargs):
    """Update ContactList stats when contacts are added/removed."""
    if action in ["post_add", "post_remove", "post_clear"]:
        if isinstance(instance, Contact):
            # If a contact was added to lists, update those lists
            if pk_set:
                lists = ContactList.all_objects.filter(pk__in=pk_set)
                for cl in lists:
                    cl.update_stats()
            else:
                # For 'post_clear', we don't have pk_set, so we'd need old PKs...
                # but clearing a contact's lists means it's no longer in those lists.
                # However, this signal is called AFTER the change.
                pass
        elif isinstance(instance, ContactList):
            # If contacts were added to a list, update that list
            instance.update_stats()


@receiver(post_save, sender=Contact)
def update_contact_list_stats_on_save(sender, instance, created, **kwargs):
    """Update ContactList stats when a contact is restored or status changed."""
    # We only need to trigger this if is_deleted or status changed
    # For performance, we could check update_fields, but it's safer to just refresh.
    # Actually, restoring is the main concern here.
    for cl in instance.lists.all():
        cl.update_stats()


@receiver(post_delete, sender=Contact)
def update_contact_list_stats_on_delete(sender, instance, **kwargs):
    """Update ContactList stats when a contact is hard-deleted."""
    for cl in instance.lists.all():
        cl.update_stats()


# Campaign notification signals
@receiver(post_save, sender=Campaign)
def create_campaign_status_notification(sender, instance, created, update_fields, **kwargs):
    """Create notification when campaign status changes to SENT."""
    if created:
        return  # Skip for new campaigns
    
    # Only proceed if status field was updated
    if update_fields is not None and 'status' not in update_fields:
        return  # Status didn't change, skip
    
    # Check if status changed to SENT
    if instance.status == 'SENT':
        try:
            # Check if notification already exists for this campaign
            existing_notification = Notification.objects.filter(
                organization=instance.organization,
                notification_type='CAMPAIGN_SENT',
                related_object_type='campaign',
                related_object_id=instance.id
            ).exists()
            
            if existing_notification:
                logger.debug(f"Notification already exists for campaign {instance.id}, skipping")
                return
            
            # Create notification for organization
            notification = Notification.objects.create(
                organization=instance.organization,
                notification_type='CAMPAIGN_SENT',
                title=f'Campaign "{instance.name}" sent successfully',
                message=f'Your campaign "{instance.name}" has been sent to {instance.stats_total_recipients} recipients.',
                related_object_type='campaign',
                related_object_id=instance.id,
                metadata={
                    'campaign_name': instance.name,
                    'total_recipients': instance.stats_total_recipients,
                    'completed_at': instance.completed_at.isoformat() if instance.completed_at else None,
                }
            )
            logger.info(f"Created notification for campaign {instance.id} sent")
            
            # Broadcast via WebSocket
            channel_layer = get_channel_layer()
            group_name = f"notifications_{instance.organization.id}"
            
            # Import serializer here to avoid circular imports
            from .serializers import NotificationSerializer
            import json
            
            # Get serialized data and convert UUIDs to strings
            serialized_data = NotificationSerializer(notification).data
            # Convert all UUID fields to strings for msgpack serialization
            notification_data = json.loads(json.dumps(serialized_data, default=str))
            
            # Send notification to WebSocket group
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'notification_message',
                    'data': notification_data
                }
            )
            
            # Send updated unread count
            unread_count = Notification.objects.filter(
                organization=instance.organization,
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
            
            logger.info(f"Broadcast notification via WebSocket to {group_name}")
            
        except Exception as e:
            logger.error(f"Failed to create campaign notification: {e}", exc_info=True)


# Campaign status update signal
_campaign_pre_save_state = threading.local()


@receiver(pre_save, sender=Campaign)
def capture_campaign_pre_save_state(sender, instance, **kwargs):
    """Capture campaign's state before saving to detect status changes."""
    if not instance.pk:
        return
    
    try:
        old_instance = Campaign.objects.get(pk=instance.pk)
        if not hasattr(_campaign_pre_save_state, 'instances'):
            _campaign_pre_save_state.instances = {}
        
        _campaign_pre_save_state.instances[str(instance.pk)] = {
            'status': old_instance.status,
        }
    except Campaign.DoesNotExist:
        pass


@receiver(post_save, sender=Campaign)
def broadcast_campaign_status_update(sender, instance, created, **kwargs):
    """Broadcast campaign status changes via WebSocket."""
    if created:
        return  # Don't broadcast new campaigns
    
    # Check if status actually changed
    old_status = None
    if hasattr(_campaign_pre_save_state, 'instances'):
        old_state = _campaign_pre_save_state.instances.get(str(instance.pk))
        if old_state:
            old_status = old_state.get('status')
    
    # Only broadcast if status changed
    if old_status is None or old_status == instance.status:
        return
    
    try:
        channel_layer = get_channel_layer()
        group_name = f"notifications_{instance.organization.id}"
        
        import json
        
        # Prepare campaign update data
        campaign_data = {
            'id': str(instance.id),
            'name': instance.name,
            'status': instance.status,
            'old_status': old_status,
            'stats_sent': instance.stats_sent,
            'stats_delivered': instance.stats_delivered,
            'stats_opened': instance.stats_opened,
            'stats_clicked': instance.stats_clicked,
            'stats_total_recipients': instance.stats_total_recipients,
            'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
        }
        
        # Send campaign status update to WebSocket group
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'campaign_status_update',
                'data': campaign_data
            }
        )
        
        logger.info(f"Broadcast campaign status update: {instance.id} changed from {old_status} to {instance.status}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast campaign status update: {e}", exc_info=True)
