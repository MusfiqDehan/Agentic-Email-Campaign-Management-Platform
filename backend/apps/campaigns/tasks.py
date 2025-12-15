import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .utils import (
    send_email_for_specific_rule,
    process_template_variables,
    render_email_template,
    send_sms,
    send_whatsapp,
    UnifiedEmailSender,
)
from .models import AutomationRule, EmailDeliveryLog, EmailTemplate, EmailQueue
from twilio.rest import Client
from decouple import config as env_config

logger = logging.getLogger(__name__)


def _delete_queryset_in_batches(queryset, batch_size=1000):
    total_deleted = 0
    model = queryset.model
    while True:
        ids = list(queryset.values_list('id', flat=True)[:batch_size])
        if not ids:
            break
        deleted, _ = model.objects.filter(id__in=ids).delete()
        total_deleted += deleted
    return total_deleted


def _log_email_dispatch(
    rule,
    recipient_emails,
    success,
    message,
    email_template=None,
    planned_delivery_at=None,
    metadata=None,
):
    try:
        # Ensure planned_delivery_at is a datetime
        if isinstance(planned_delivery_at, str):
            parsed = parse_datetime(planned_delivery_at)
            planned_delivery_at = parsed or None
        metadata = metadata or {}
        recipients = recipient_emails or metadata.get('recipient_emails') or []
        if isinstance(recipients, str):
            recipients = [recipients]
        recipients = [email.strip() for email in recipients if email]

        if not recipients:
            fallback_email = metadata.get('recipient_email')
            if fallback_email:
                recipients = [fallback_email]

        tenant_id = getattr(rule, 'tenant_id', None) if rule else metadata.get('tenant_id')
        product_id = getattr(rule, 'product_id', None) if rule else metadata.get('product_id')
        
        # Allow metadata to override tenant_id and product_id from rule (for dynamic triggering)
        if metadata.get('tenant_id') is not None:
            tenant_id = metadata.get('tenant_id')
        if metadata.get('product_id') is not None:
            product_id = metadata.get('product_id')

        reason_name = metadata.get('reason_name') or (rule.reason_name if rule else AutomationRule.ReasonName.OTHER)
        trigger_type = metadata.get('trigger_type') or (rule.trigger_type if rule else AutomationRule.TriggerType.IMMEDIATE)

        template_obj = email_template or getattr(rule, 'email_template_id', None)
        template_id = metadata.get('email_template_id')
        if not template_obj and template_id:
            try:
                from .models import EmailTemplate  # Local import to avoid circular dependency

                template_obj = EmailTemplate.objects.filter(id=template_id).first()
            except Exception:
                template_obj = None

        log_scope = metadata.get('log_scope')
        if not log_scope and rule:
            log_scope = rule.rule_scope
        log_scope = (log_scope or AutomationRule.RuleScope.TENANT).upper()

        delivery_status = metadata.get('delivery_status', 'SENT' if success else 'FAILED')
        context_data = metadata.get('email_variables') or metadata.get('context_data') or {}

        for email in recipients:
            try:
                EmailDeliveryLog.objects.create(
                    automation_rule=rule if rule else None,
                    tenant_id=tenant_id,
                    product_id=product_id,
                    reason_name=reason_name,
                    trigger_type=trigger_type,
                    email_template=template_obj,
                    recipient_email=email,
                    sender_email=metadata.get('sender_email', ''),
                    subject=metadata.get('subject', ''),
                    delivery_status=delivery_status,
                    log_scope=log_scope,
                    planned_delivery_at=planned_delivery_at,
                    context_data=context_data,
                    error_message='' if success else (message or metadata.get('error_message', '')),
                    email_provider_id=metadata.get('provider_id'),
                    provider_message_id=metadata.get('provider_message_id', ''),
                )
            except Exception as inner_e:
                print(f"[EmailDeliveryLog ERROR] recipient={email}: {inner_e}")
    except Exception as e:
        # Avoid crashing the task on logging errors
        print(f"[EmailDeliveryLog ERROR] rule={getattr(rule,'id','?')}: {e}")

@shared_task
def dispatch_email_task(rule_id, recipient_emails, email_variables, email_template_id=None, planned_delivery_at=None, override_tenant_id=None, override_product_id=None):
    rule = None
    try:
        rule = AutomationRule.objects.get(id=rule_id)
        success, msg, metadata = send_email_for_specific_rule(
            rule=rule,
            recipient_emails=recipient_emails,
            email_variables=email_variables,
            override_email_template_id=email_template_id
        )
        
        # Build metadata with overrides for tenant_id and product_id if provided
        dispatch_metadata = {
            **metadata, 
            'email_variables': email_variables,
            'tenant_id': override_tenant_id if override_tenant_id is not None else getattr(rule, 'tenant_id', None),
            'product_id': override_product_id if override_product_id is not None else getattr(rule, 'product_id', None),
        }
        
        _log_email_dispatch(
            rule,
            recipient_emails,
            success,
            msg,
            email_template=(rule.email_template_id if not email_template_id else rule.email_template_id),
            planned_delivery_at=planned_delivery_at,
            metadata=dispatch_metadata,
        )
    except AutomationRule.DoesNotExist:
        _log_email_dispatch(
            None,
            recipient_emails,
            False,
            f"Rule {rule_id} not found",
            planned_delivery_at=planned_delivery_at,
            metadata={'tenant_id': None, 'product_id': None, 'email_variables': email_variables},
        )
    except Exception as e:
        _log_email_dispatch(
            rule,
            recipient_emails,
            False,
            str(e),
            planned_delivery_at=planned_delivery_at,
            metadata={'email_variables': email_variables},
        )

@shared_task
def dispatch_scheduled_email_task(rule_id, planned_delivery_at=None):
    rule = None
    try:
        rule = AutomationRule.objects.get(id=rule_id)
        recipient_emails = []
        if rule.email_template_id and getattr(rule.email_template_id, "recipient_emails_list", ""):
            recipient_emails = [e.strip() for e in rule.email_template_id.recipient_emails_list.split(",") if e.strip()]
        # Default planned_delivery_at for schedules to now if not passed by caller (celery beat)
        if planned_delivery_at is None:
            planned_delivery_at = timezone.now()
        success, msg, metadata = send_email_for_specific_rule(rule=rule, recipient_emails=recipient_emails, email_variables={})
        _log_email_dispatch(
            rule,
            recipient_emails,
            success,
            msg,
            planned_delivery_at=planned_delivery_at,
            metadata={**metadata, 'email_variables': {}, 'tenant_id': getattr(rule, 'tenant_id', None)},
        )
    except AutomationRule.DoesNotExist:
        _log_email_dispatch(
            None,
            [],
            False,
            f"Rule {rule_id} not found",
            planned_delivery_at=planned_delivery_at,
            metadata={'tenant_id': None, 'product_id': None, 'email_variables': {}},
        )
    except Exception as e:
        _log_email_dispatch(
            rule,
            [],
            False,
            str(e),
            planned_delivery_at=planned_delivery_at,
            metadata={'email_variables': {}},
        )

@shared_task
def dispatch_scheduled_sms_task(rule_id, tenant_id=None):
    """
    Task to dispatch scheduled SMS messages based on automation rule.
    """
    try:
        rule = AutomationRule.objects.get(id=rule_id)
        
        # Check if rule supports SMS or WhatsApp
        valid_types = [
            AutomationRule.CommunicationType.SMS,
            getattr(AutomationRule.CommunicationType, 'WHATSAPP', None)
        ]
        if rule.communication_type not in valid_types:
            print(f"Rule {rule_id} is not configured for SMS or WhatsApp")
            return
            
        if not rule.sms_template_id:
            print(f"Rule {rule_id} has no SMS/WhatsApp template configured")
            return
            
        if not rule.sms_config_id:
            print(f"Rule {rule_id} has no SMS/WhatsApp configuration")
            return
        
        # Get SMS configuration
        sms_config = rule.sms_config_id
        
        # Get template
        template = rule.sms_template_id
        
        # Process template with context data (would need to be fetched or passed)
        context = {}  # This would be dynamic based on your application
        body = process_template_variables(template.sms_body, context)
        
        # Get recipient numbers
        recipient_numbers = [num.strip() for num in template.recipient_numbers_list.split(',') if num.strip()]
        
        # Use Twilio to send the SMS
        client = Client(sms_config.account_ssid, sms_config.auth_token)
        
        for number in recipient_numbers:
            try:
                message = client.messages.create(
                    body=body,
                    messaging_service_sid=sms_config.verified_service_id,
                    to=number
                )
                print(f"SMS sent to {number}, SID: {message.sid}")
            except Exception as e:
                print(f"Failed to send SMS to {number}: {str(e)}")

    except AutomationRule.DoesNotExist:
        print(f"Automation rule with ID {rule_id} not found")
    except Exception as e:
        print(f"Error dispatching SMS for rule {rule_id}: {str(e)}")


@shared_task
def dispatch_scheduled_whatsapp_task(rule_id):
    """
    Task to dispatch scheduled WhatsApp messages based on automation rule.
    """
    try:
        rule = AutomationRule.objects.get(id=rule_id)
        
        # Check if rule supports WhatsApp
        valid_types = [
            AutomationRule.CommunicationType.SMS,
            getattr(AutomationRule.CommunicationType, 'WHATSAPP', None)
        ]
        if rule.communication_type not in valid_types:
            print(f"Rule {rule_id} is not configured for SMS or WhatsApp")
            return
            
        if not rule.sms_template_id:
            print(f"Rule {rule_id} has no SMS/WhatsApp template configured")
            return
            
        if not rule.sms_config_id:
            print(f"Rule {rule_id} has no SMS/WhatsApp configuration")
            return
        
        # Get SMS configuration
        sms_config = rule.sms_config_id
        
        # Get template
        template = rule.sms_template_id
        
        # Check if template supports WhatsApp
        if not template.supports_whatsapp:
            print(f"Template {template.id} does not support WhatsApp")
            return
        
        # Process template with context data (would need to be fetched or passed)
        context = {}  # This would be dynamic based on your application
        body = process_template_variables(template.sms_body, context)
        
        # Get recipient numbers
        recipient_numbers = [num.strip() for num in template.recipient_numbers_list.split(',') if num.strip()]
        
        # Use Twilio to send WhatsApp messages
        client = Client(sms_config.account_ssid, sms_config.auth_token)
        
        for number in recipient_numbers:
            try:
                # Format phone number for WhatsApp (must include country code and 'whatsapp:' prefix)
                if not number.startswith('+'):
                    number = f"+1{number.lstrip('1')}"
                to_number = f"whatsapp:{number}"
                from_number = getattr(sms_config, 'whatsapp_from_number', None) or "whatsapp:+14155238886"
                
                message = client.messages.create(
                    body=body,
                    from_=from_number,
                    to=to_number
                )
                print(f"WhatsApp sent to {number}, SID: {message.sid}")
            except Exception as e:
                print(f"Failed to send WhatsApp to {number}: {str(e)}")

    except AutomationRule.DoesNotExist:
        print(f"Automation rule with ID {rule_id} not found")
    except Exception as e:
        print(f"Error dispatching WhatsApp for rule {rule_id}: {str(e)}")


@shared_task
def send_delayed_sms(rule_id, sms_variables=None, recipient_numbers=None):
    """
    Task to send delayed SMS messages.
    """
    print(f"Sending delayed SMS for rule {rule_id}")
    return send_sms(rule_id, sms_variables, recipient_numbers, use_whatsapp=False)


@shared_task
def send_delayed_whatsapp(rule_id, sms_variables=None, recipient_numbers=None):
    """
    Task to send delayed WhatsApp messages.
    """
    print(f"Sending delayed WhatsApp for rule {rule_id}")
    return send_whatsapp(rule_id, sms_variables, recipient_numbers)


@shared_task
def send_immediate_sms(rule_id, sms_variables=None, recipient_numbers=None):
    """
    Task to send immediate SMS messages (can be used for async processing).
    """
    print(f"Sending immediate SMS for rule {rule_id}")
    return send_sms(rule_id, sms_variables, recipient_numbers, use_whatsapp=False)


@shared_task
def send_immediate_whatsapp(rule_id, sms_variables=None, recipient_numbers=None):
    """
    Task to send immediate WhatsApp messages (can be used for async processing).
    """
    print(f"Sending immediate WhatsApp for rule {rule_id}")
    return send_whatsapp(rule_id, sms_variables, recipient_numbers)


@shared_task
def bulk_send_sms(rule_id, sms_variables_list, recipient_numbers_list):
    """
    Task to send SMS to multiple recipients with different variables.
    
    Args:
        rule_id: ID of the AutomationRule
        sms_variables_list: List of dictionaries with template variables for each recipient
        recipient_numbers_list: List of phone numbers
    """
    print(f"Bulk sending SMS for rule {rule_id} to {len(recipient_numbers_list)} recipients")
    results = []
    
    for i, (variables, number) in enumerate(zip(sms_variables_list, recipient_numbers_list)):
        try:
            result = send_sms(rule_id, variables, [number], use_whatsapp=False)
            results.append({"recipient": number, "success": bool(result), "message_sids": result})
        except Exception as e:
            print(f"Failed to send SMS to {number}: {str(e)}")
            results.append({"recipient": number, "success": False, "error": str(e)})
    
    return results


@shared_task
def bulk_send_whatsapp(rule_id, sms_variables_list, recipient_numbers_list):
    """
    Task to send WhatsApp messages to multiple recipients with different variables.
    
    Args:
        rule_id: ID of the AutomationRule
        sms_variables_list: List of dictionaries with template variables for each recipient
        recipient_numbers_list: List of phone numbers
    """
    print(f"Bulk sending WhatsApp for rule {rule_id} to {len(recipient_numbers_list)} recipients")
    results = []
    
    for i, (variables, number) in enumerate(zip(sms_variables_list, recipient_numbers_list)):
        try:
            result = send_whatsapp(rule_id, variables, [number])
            results.append({"recipient": number, "success": bool(result), "message_sids": result})
        except Exception as e:
            print(f"Failed to send WhatsApp to {number}: {str(e)}")
            results.append({"recipient": number, "success": False, "error": str(e)})
    
    return results


@shared_task
def retry_failed_sms(rule_id, failed_recipients, sms_variables=None, max_retries=3):
    """
    Task to retry sending SMS to failed recipients.
    
    Args:
        rule_id: ID of the AutomationRule
        failed_recipients: List of phone numbers that failed to receive SMS
        sms_variables: Dictionary of template variables
        max_retries: Maximum number of retry attempts
    """
    print(f"Retrying SMS for rule {rule_id} to {len(failed_recipients)} failed recipients")
    retry_results = []
    
    for number in failed_recipients:
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                result = send_sms(rule_id, sms_variables, [number], use_whatsapp=False)
                if result:
                    success = True
                    retry_results.append({"recipient": number, "success": True, "retries": retry_count + 1})
                    print(f"SMS retry successful for {number} after {retry_count + 1} attempts")
                else:
                    retry_count += 1
            except Exception as e:
                retry_count += 1
                print(f"SMS retry {retry_count} failed for {number}: {str(e)}")
        
        if not success:
            retry_results.append({"recipient": number, "success": False, "retries": retry_count})
            print(f"SMS retry failed for {number} after {retry_count} attempts")
    
    return retry_results


@shared_task
def retry_failed_whatsapp(rule_id, failed_recipients, sms_variables=None, max_retries=3):
    """
    Task to retry sending WhatsApp messages to failed recipients.
    
    Args:
        rule_id: ID of the AutomationRule
        failed_recipients: List of phone numbers that failed to receive WhatsApp
        sms_variables: Dictionary of template variables
        max_retries: Maximum number of retry attempts
    """
    print(f"Retrying WhatsApp for rule {rule_id} to {len(failed_recipients)} failed recipients")
    retry_results = []
    
    for number in failed_recipients:
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                result = send_whatsapp(rule_id, sms_variables, [number])
                if result:
                    success = True
                    retry_results.append({"recipient": number, "success": True, "retries": retry_count + 1})
                    print(f"WhatsApp retry successful for {number} after {retry_count + 1} attempts")
                else:
                    retry_count += 1
            except Exception as e:
                retry_count += 1
                print(f"WhatsApp retry {retry_count} failed for {number}: {str(e)}")
        
        if not success:
            retry_results.append({"recipient": number, "success": False, "retries": retry_count})
            print(f"WhatsApp retry failed for {number} after {retry_count} attempts")
    
    return retry_results


# Enhanced tasks for new email automation system
@shared_task(bind=True, max_retries=3)
def dispatch_enhanced_email_task(self, rule_id, recipient_emails, email_variables, options=None):
    """
    Enhanced email dispatch task with provider-agnostic support and comprehensive logging
    """
    import uuid
    from django.utils import timezone
    from .models import AutomationRule, EmailQueue, TenantEmailConfiguration
    from .utils.tenant_service import TenantServiceAPI
    from .utils.email_providers import EmailProviderManager
    
    options = options or {}
    correlation_id = options.get('correlation_id', str(uuid.uuid4()))
    
    try:
        # Get automation rule
        rule = AutomationRule.objects.select_related(
            'email_template_id', 'preferred_email_provider'
        ).get(id=rule_id, activated_by_root=True, activated_by_tmd=True)
        
        tenant_id = options.get('tenant_id') or rule.tenant_id
        
        # Validate tenant can send emails
        tenant_config = TenantEmailConfiguration.objects.filter(tenant_id=tenant_id).first()
        if not tenant_config:
            # Create default configuration
            limits = TenantServiceAPI.get_tenant_plan_limits(str(tenant_id))
            tenant_config = TenantEmailConfiguration.objects.create(
                tenant_id=tenant_id,
                plan_type='FREE',
                emails_per_day=limits.get('emails_per_day', 50),
                emails_per_month=limits.get('emails_per_month', 500),
                emails_per_minute=limits.get('emails_per_minute', 5),
                activated_by_tmd=True
            )
        
        can_send, reason = tenant_config.can_send_email()
        if not can_send:
            raise Exception(f"Tenant cannot send emails: {reason}")
        
        # Extract preferred_provider_id from options or rule defaults
        preferred_provider_id = options.get('preferred_provider_id')
        if not preferred_provider_id and getattr(rule, 'preferred_email_provider', None):
            try:
                # TenantEmailProvider.provider is a FK to EmailProvider
                preferred_provider_id = str(rule.preferred_email_provider.provider.id)
                logger.info(f"[dispatch_enhanced_email_task] Extracted provider ID from rule.preferred_email_provider: {preferred_provider_id}")
            except Exception as e:
                logger.warning(f"[dispatch_enhanced_email_task] Failed to extract provider from rule.preferred_email_provider: {e}")
                preferred_provider_id = None
        if not preferred_provider_id and getattr(rule, 'preferred_global_provider', None):
            preferred_provider_id = str(rule.preferred_global_provider_id)
            logger.info(f"[dispatch_enhanced_email_task] Using rule.preferred_global_provider_id: {preferred_provider_id}")
        
        logger.info(f"[dispatch_enhanced_email_task] Final preferred_provider_id: {preferred_provider_id}")
        
        # Determine the effective template once for rendering
        override_template_id = options.get('email_template_id') or email_variables.get('email_template_id')
        resolved_template = None

        if override_template_id:
            resolved_template = EmailTemplate.objects.filter(id=override_template_id).first()

        if not resolved_template:
            try:
                resolved_template = UnifiedEmailSender._resolve_email_template(  # pylint: disable=protected-access
                    rule,
                    override_template_id=override_template_id,
                )
            except Exception:
                resolved_template = None

        # Create queue items for each recipient
        queue_items = []
        for recipient_email in recipient_emails:
            # Process email template with variables
            if resolved_template:
                subject, html_content, text_content = render_email_template(
                    resolved_template,
                    email_variables
                )
            else:
                subject = email_variables.get('subject', 'Notification')
                html_content = email_variables.get('html_content', '')
                text_content = email_variables.get('text_content', '')
            
            # Prepare context data with provider preference
            context_data = email_variables.copy()
            if resolved_template:
                context_data['resolved_template_id'] = str(resolved_template.id)
                context_data.setdefault('template_category', resolved_template.category)
            if preferred_provider_id:
                context_data['preferred_provider_id'] = str(preferred_provider_id)
            context_data.setdefault('reason_name', rule.reason_name)
            context_data.setdefault('trigger_type', rule.trigger_type)
            context_data.setdefault('product_id', str(rule.product_id) if rule.product_id else None)
            context_data.setdefault('rule_scope', rule.rule_scope)
            
            # Create queue item
            queue_item = EmailQueue.objects.create(
                automation_rule=rule,
                tenant_id=tenant_id,
                recipient_email=recipient_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                context_data=context_data,
                priority=options.get('priority', 5),
                scheduled_at=timezone.now(),
                max_retries=rule.max_retries or 3
            )
            queue_items.append(queue_item)
        
        # Process queue items
        results = []
        for queue_item in queue_items:
            result = process_email_queue_item(queue_item, correlation_id)
            results.append(result)
        
        # Update tenant usage
        successful_sends = sum(1 for r in results if r.get('success'))
        if successful_sends > 0:
            tenant_config.increment_usage()
        
        return {
            'success': True,
            'total_emails': len(recipient_emails),
            'successful_sends': successful_sends,
            'failed_sends': len(recipient_emails) - successful_sends,
            'results': results,
            'correlation_id': correlation_id
        }
        
    except Exception as e:
        # Log the error and potentially retry
        print(f"Enhanced email dispatch failed: {e}")
        
        if self.request.retries < self.max_retries:
            # Exponential backoff
            countdown = 2 ** self.request.retries
            raise self.retry(countdown=countdown, exc=e)
        
        return {
            'success': False,
            'error': str(e),
            'correlation_id': correlation_id
        }


def process_email_queue_item(queue_item, correlation_id=None):
    """
    Process a single email queue item with provider failover and logging.
    
    Implements idempotent processing with optimistic locking to prevent:
    - Duplicate delivery logs from concurrent workers
    - Race conditions during queue item processing
    - Retry-induced duplicates
    """
    from django.utils import timezone
    from django.db import transaction, IntegrityError
    from .models import EmailDeliveryLog, EmailValidation, EmailQueue, EmailTemplate
    from .utils.email_providers import EmailProviderManager
    from .utils.sync_utils import ConfigurationHierarchy
    from .models.provider_models import EmailProvider
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Optimistic Locking: Prevent concurrent processing of same queue item
        # Use select_for_update with nowait to fail fast if already locked
        with transaction.atomic():
            try:
                locked_queue_item = EmailQueue.objects.select_for_update(nowait=True).get(id=queue_item.id)
            except Exception as lock_error:
                logger.warning(f"Queue item {queue_item.id} is already being processed by another worker")
                return {
                    'success': False,
                    'queue_item_id': str(queue_item.id),
                    'error': 'Already being processed',
                    'skipped': True
                }
            
            # Check if already processed (idempotency check)
            if locked_queue_item.status in ['SENT', 'FAILED', 'CANCELLED']:
                logger.info(f"Queue item {queue_item.id} already processed with status {locked_queue_item.status}")
                return {
                    'success': locked_queue_item.status == 'SENT',
                    'queue_item_id': str(queue_item.id),
                    'already_processed': True,
                    'status': locked_queue_item.status
                }
            
            # Update queue status to PROCESSING
            locked_queue_item.status = 'PROCESSING'
            locked_queue_item.save(update_fields=['status', 'updated_at'])
            
            # Work with the locked instance from here on
            queue_item = locked_queue_item
        
        context = queue_item.context_data or {}
        effective_sender_email = None

        # Validate email if not skipped
        email_validation = None
        if not context.get('skip_validation', False):
            email_validation, created = EmailValidation.objects.get_or_create(
                email_address=queue_item.recipient_email,
                defaults={
                    'is_valid_format': True,  # Basic validation
                    'validation_status': 'VALID'
                }
            )
            
            # Skip if email is blacklisted
            if email_validation.is_blacklisted:
                queue_item.status = 'FAILED'
                queue_item.error_message = 'Email is blacklisted'
                queue_item.save()
                
                return {
                    'success': False,
                    'queue_item_id': str(queue_item.id),
                    'error': 'Email is blacklisted'
                }
        
        # Get email provider manager
        tenant_identifier = str(queue_item.tenant_id) if queue_item.tenant_id else None
        provider_manager = EmailProviderManager(tenant_identifier)
        
        # Extract preferred_provider_id from context_data if provided
        preferred_provider_id = context.get('preferred_provider_id') if context else None
        logger.info(f"[process_email_queue_item] Queue {queue_item.id}: preferred_provider_id={preferred_provider_id}")
        
        # Determine sender email using the SAME logic as UnifiedEmailSender (ConfigurationHierarchy)
        # This ensures consistency between trigger/email/ and trigger/enhanced-email/
        from campaigns.utils.sync_utils import ConfigurationHierarchy
        from campaigns.models.provider_models import EmailProvider
        
        # Get the provider config to extract from_email
        provider_config = None
        if preferred_provider_id:
            try:
                email_provider = EmailProvider.objects.filter(id=preferred_provider_id).first()
                if email_provider:
                    provider_config = email_provider.decrypt_config()
            except Exception as e:
                logger.warning(f"Failed to get provider config for {preferred_provider_id}: {e}")
        
        # Use ConfigurationHierarchy to resolve sender email (same as UnifiedEmailSender)
        sender_email_candidate = ConfigurationHierarchy.get_effective_from_email(
            tenant_id=str(queue_item.tenant_id) if queue_item.tenant_id else None,
            provider_config=provider_config,
            rule=queue_item.automation_rule
        )
        
        logger.info(f"[process_email_queue_item] Queue {queue_item.id}: Resolved sender_candidate={sender_email_candidate} using ConfigurationHierarchy")
        
        # Send email with fallback (with optional manual provider selection)
        success, message_id, response_data = provider_manager.send_email_with_fallback(
            recipient_email=queue_item.recipient_email,
            subject=queue_item.subject,
            html_content=queue_item.html_content,
            text_content=queue_item.text_content,
            sender_email=sender_email_candidate,
            headers=queue_item.headers,
            preferred_provider_id=preferred_provider_id
        )

        # Determine the effective sender email used for this attempt
        response_sender = None
        if isinstance(response_data, dict):
            response_sender = response_data.get('sender_email')
        
        logger.info(f"[process_email_queue_item] Queue {queue_item.id}: response_sender={response_sender}, response_data keys={list(response_data.keys()) if isinstance(response_data, dict) else 'not a dict'}")

        # Use response sender if available, otherwise fallback to what we passed
        effective_sender_email = (
            (response_sender.strip() if isinstance(response_sender, str) else None)
            or sender_email_candidate
        )

        if not effective_sender_email:
            fallback_domain = env_config('DEFAULT_ORG_DOMAIN', default='example.com')
            effective_sender_email = f"noreply@{fallback_domain}"
        
        logger.info(f"[process_email_queue_item] Queue {queue_item.id}: Final effective_sender_email={effective_sender_email}")

        # Persist sender email snapshot in context for downstream consumers
        context['sender_email'] = effective_sender_email
        
        # Update queue item status
        if success:
            queue_item.status = 'SENT'
            queue_item.processed_at = timezone.now()
        else:
            queue_item.status = 'FAILED'
            queue_item.error_message = response_data.get('error_message', 'Unknown error')
            queue_item.error_code = response_data.get('error_code', 'UNKNOWN')
        
        queue_item.context_data = context
        queue_item.save()
        
        # Resolve the template used for this email (if any)
        resolved_template = None
        resolved_template_id = context.get('resolved_template_id') if context else None
        if resolved_template_id:
            resolved_template = EmailTemplate.objects.filter(id=resolved_template_id).first()
        if not resolved_template:
            resolved_template = queue_item.campaigns.email_template_id

        # Create or update delivery log (idempotent - handles race conditions & retries)
        initial_event = {
            'event': 'LOCAL_STATUS',
            'timestamp': timezone.now().isoformat(),
            'metadata': {
                'status': 'SENT' if success else 'FAILED',
                'provider': response_data.get('provider_name'),
                'provider_id': response_data.get('provider_id'),
                'provider_response': response_data.get('response'),
                'queue_status': queue_item.status,
            }
        }
        
        # Use update_or_create to handle duplicate key violations gracefully
        delivery_log, log_created = EmailDeliveryLog.objects.update_or_create(
            queue_item=queue_item,  # Unique constraint field
            defaults={
                'automation_rule': queue_item.automation_rule,
                'tenant_id': queue_item.tenant_id,
                'email_validation': email_validation,
                'email_provider_id': response_data.get('provider_id'),
                'provider_message_id': message_id or '',
                'recipient_email': queue_item.recipient_email,
                'sender_email': effective_sender_email,
                'subject': queue_item.subject,
                'delivery_status': 'SENT' if success else 'FAILED',
                'bounce_reason': response_data.get('error_message', '') if not success else '',
                'event_history': [initial_event],
                'sent_at': timezone.now() if not hasattr(queue_item, 'delivery_log') else queue_item.delivery_log.sent_at,
                'reason_name': context.get('reason_name') or getattr(queue_item.automation_rule, 'reason_name', ''),
                'trigger_type': context.get('trigger_type') or getattr(queue_item.automation_rule, 'trigger_type', ''),
                'product_id': context.get('product_id') or queue_item.campaigns.product_id,
                'log_scope': (context.get('rule_scope') or queue_item.campaigns.rule_scope or AutomationRule.RuleScope.TENANT),
                'email_template': resolved_template,
                'context_data': context,
            }
        )
        
        # If log already existed, append to event history instead of replacing
        if not log_created:
            logger.info(f"Delivery log already exists for queue item {queue_item.id}, appending event to history")
            if isinstance(delivery_log.event_history, list):
                delivery_log.event_history.append(initial_event)
            else:
                delivery_log.event_history = [initial_event]
            delivery_log.save(update_fields=['event_history', 'delivery_status', 'provider_message_id', 'updated_at'])
        
        # Update email validation reputation if available
        if email_validation:
            if success:
                email_validation.update_reputation('delivered')
            else:
                bounce_type = response_data.get('bounce_type', 'hard')
                if bounce_type == 'hard':
                    email_validation.update_reputation('bounced')
        
        return {
            'success': success,
            'queue_item_id': str(queue_item.id),
            'delivery_log_id': str(delivery_log.id),
            'message_id': message_id,
            'provider': response_data.get('provider_name'),
            'sender_email': effective_sender_email,
            'correlation_id': correlation_id,
            'log_created': log_created  # Indicates if this was a new log or update
        }
    
    except IntegrityError as ie:
        # This should rarely happen now with update_or_create, but handle it defensively
        logger.error(f"IntegrityError processing queue item {queue_item.id}: {ie}")
        
        # Try to fetch the existing delivery log
        try:
            existing_log = EmailDeliveryLog.objects.get(queue_item=queue_item)
            logger.info(f"Found existing delivery log {existing_log.id} for queue item {queue_item.id}")
            
            return {
                'success': existing_log.delivery_status == 'SENT',
                'queue_item_id': str(queue_item.id),
                'delivery_log_id': str(existing_log.id),
                'sender_email': existing_log.sender_email or effective_sender_email,
                'already_exists': True,
                'correlation_id': correlation_id
            }
        except EmailDeliveryLog.DoesNotExist:
            # Log exists but we can't find it - critical error
            queue_item.status = 'FAILED'
            queue_item.error_message = f'IntegrityError: {str(ie)}'
            queue_item.save()
            
            return {
                'success': False,
                'queue_item_id': str(queue_item.id),
                'error': f'IntegrityError: {str(ie)}',
                'sender_email': effective_sender_email,
                'correlation_id': correlation_id
            }
        
    except Exception as e:
        # Update queue item with error
        logger.exception(f"Error processing queue item {queue_item.id}: {e}")
        
        try:
            queue_item.status = 'FAILED'
            queue_item.error_message = str(e)
            queue_item.save()
        except Exception as save_error:
            logger.error(f"Failed to update queue item status: {save_error}")
        
        return {
            'success': False,
            'queue_item_id': str(queue_item.id),
            'error': str(e),
            'sender_email': effective_sender_email,
            'correlation_id': correlation_id
        }


@shared_task(bind=True, max_retries=3, acks_late=True)
def process_email_queue_task(self, queue_item_id):
    """
    Celery task to process individual email queue items.
    
    Features:
    - Idempotent: Can be safely retried without side effects
    - Uses task_id for deduplication (based on queue_item_id)
    - acks_late=True: Ensures task is redelivered if worker crashes
    - Optimistic locking prevents concurrent processing
    
    Args:
        queue_item_id: UUID of the EmailQueue item to process
    """
    from .models import EmailQueue
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        queue_item = EmailQueue.objects.select_related('automation_rule').get(id=queue_item_id)
        
        # Check if this task has already been processed successfully
        # (Additional safety check beyond database-level idempotency)
        if hasattr(queue_item, 'delivery_log') and queue_item.status in ['SENT', 'CANCELLED']:
            logger.info(f"Task {self.request.id}: Queue item {queue_item_id} already has delivery log, skipping")
            return {
                'success': True,
                'queue_item_id': str(queue_item_id),
                'already_processed': True,
                'task_id': self.request.id
            }
        
        result = process_email_queue_item(queue_item)
        
        # Add task metadata to result
        result['task_id'] = self.request.id
        result['retry_count'] = self.request.retries
        
        return result
        
    except EmailQueue.DoesNotExist:
        logger.error(f"Task {self.request.id}: Queue item {queue_item_id} not found")
        return {
            'success': False,
            'error': f'Queue item {queue_item_id} not found',
            'task_id': self.request.id
        }
    except Exception as e:
        logger.exception(f"Task {self.request.id}: Unexpected error processing {queue_item_id}")
        
        # Retry with exponential backoff if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries  # 2s, 4s, 8s
            logger.info(f"Task {self.request.id}: Retrying in {countdown}s (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(countdown=countdown, exc=e)
        
        return {
            'success': False,
            'error': str(e),
            'queue_item_id': str(queue_item_id),
            'task_id': self.request.id,
            'max_retries_exceeded': True
        }


def submit_email_queue_task(queue_item_id, priority=5, eta=None):
    """
    Submit an email queue processing task with idempotency guarantees.
    
    Uses a deterministic task_id based on queue_item_id to prevent duplicate
    task submissions. If a task with the same ID already exists in the queue,
    Celery will reject it.
    
    Args:
        queue_item_id: UUID or string UUID of the queue item
        priority: Task priority (0-9, where 0 is highest)
        eta: Estimated time of arrival (scheduled execution time)
    
    Returns:
        AsyncResult: Celery task result object
    """
    import hashlib
    
    # Convert to string if UUID object
    queue_item_str = str(queue_item_id)
    
    # Create deterministic task ID from queue_item_id
    # This prevents duplicate task submissions for the same queue item
    task_id = f"email-queue-{queue_item_str}"
    
    try:
        # Submit task with deterministic task_id
        result = process_email_queue_task.apply_async(
            args=[queue_item_str],
            task_id=task_id,
            priority=priority,
            eta=eta
        )
        return result
    except Exception as e:
        # If task with this ID already exists, Celery might raise an exception
        # depending on the broker configuration
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to submit task for queue item {queue_item_str}: {e}")
        raise


@shared_task
def process_pending_email_queue():
    """
    Periodic task to process pending emails in the queue
    """
    from django.utils import timezone
    from .models import EmailQueue
    
    # Get pending emails scheduled for now or earlier
    pending_emails = EmailQueue.objects.filter(
        status='PENDING',
        scheduled_at__lte=timezone.now()
    ).order_by('priority', 'scheduled_at')[:100]  # Process in batches
    
    results = []
    for queue_item in pending_emails:
        result = process_email_queue_item(queue_item)
        results.append(result)
    
    return {
        'processed': len(results),
        'successful': sum(1 for r in results if r.get('success')),
        'failed': sum(1 for r in results if not r.get('success'))
    }


@shared_task
def process_email_events():
    """Compatibility wrapper for celery beat schedule."""
    return process_pending_email_queue()


@shared_task
def check_campaign_status():
    """Periodic heartbeat that can later validate campaign states."""
    logger.info("Campaign status check heartbeat")
    return {
        'checked_at': timezone.now().isoformat()
    }


@shared_task
def cleanup_old_logs(retention_days=None, queue_retention_days=None, batch_size=1000):
    """Purge aged delivery logs and terminal queue items to contain storage growth."""
    log_retention_days = retention_days or env_config('EMAIL_LOG_RETENTION_DAYS', default=90, cast=int)
    queue_retention_days = queue_retention_days or env_config('EMAIL_QUEUE_RETENTION_DAYS', default=30, cast=int)
    log_retention_days = max(int(log_retention_days), 1)
    queue_retention_days = max(int(queue_retention_days), 1)

    now = timezone.now()
    log_cutoff = now - timedelta(days=log_retention_days)
    queue_cutoff = now - timedelta(days=queue_retention_days)

    logger.info(
        "[cleanup_old_logs] Starting cleanup window. log_retention=%sd queue_retention=%sd",
        log_retention_days,
        queue_retention_days,
    )

    delivery_log_qs = EmailDeliveryLog.objects.filter(sent_at__lt=log_cutoff)
    deleted_logs = _delete_queryset_in_batches(delivery_log_qs, batch_size=batch_size)

    terminal_statuses = ['SENT', 'FAILED', 'CANCELLED']
    queue_qs = EmailQueue.objects.filter(status__in=terminal_statuses, processed_at__lt=queue_cutoff)
    deleted_queue_items = _delete_queryset_in_batches(queue_qs, batch_size=batch_size)

    logger.info(
        "[cleanup_old_logs] Finished cleanup. removed_logs=%s removed_queue_items=%s",
        deleted_logs,
        deleted_queue_items,
    )

    return {
        'deleted_logs': deleted_logs,
        'deleted_queue_items': deleted_queue_items,
        'log_cutoff': log_cutoff.isoformat(),
        'queue_cutoff': queue_cutoff.isoformat(),
    }


# =============================================================================
# CAMPAIGN TASKS
# =============================================================================

@shared_task(bind=True, max_retries=3, acks_late=True)
def launch_campaign_task(self, campaign_id):
    """
    Launch a campaign and send emails to all recipients in batches.
    
    This task:
    1. Gets all active contacts from the campaign's contact lists
    2. Sends emails in batches using the campaign's provider
    3. Updates campaign statistics
    4. Marks campaign as SENT when complete
    """
    from .models import Campaign, Contact, EmailDeliveryLog, OrganizationEmailProvider, EmailProvider
    from .utils.email_providers import EmailProviderFactory
    
    try:
        campaign = Campaign.objects.select_related(
            'organization', 'email_template', 'email_provider', 'email_provider__provider'
        ).get(id=campaign_id)
    except Campaign.DoesNotExist:
        logger.error(f"[launch_campaign_task] Campaign {campaign_id} not found")
        return {'success': False, 'error': f'Campaign {campaign_id} not found'}
    
    if campaign.status not in ['SENDING', 'PAUSED']:
        logger.info(f"[launch_campaign_task] Campaign {campaign_id} status is {campaign.status}, skipping")
        return {'success': False, 'error': f'Campaign status is {campaign.status}'}
    
    logger.info(f"[launch_campaign_task] Starting campaign {campaign.name} ({campaign_id})")
    
    # Get all active contacts from contact lists
    contacts = Contact.objects.filter(
        lists__in=campaign.contact_lists.all(),
        status='ACTIVE',
        is_active=True,
        is_deleted=False,
        organization=campaign.organization
    ).distinct()
    
    # Exclude already sent contacts (for resume scenarios)
    already_sent_emails = EmailDeliveryLog.objects.filter(
        campaign=campaign,
        delivery_status__in=['SENT', 'DELIVERED', 'OPENED', 'CLICKED']
    ).values_list('recipient_email', flat=True)
    
    contacts = contacts.exclude(email__in=already_sent_emails)
    
    total_contacts = contacts.count()
    if total_contacts == 0:
        campaign.status = 'SENT'
        campaign.completed_at = timezone.now()
        campaign.save(update_fields=['status', 'completed_at'])
        logger.info(f"[launch_campaign_task] Campaign {campaign_id} completed - no contacts to send")
        return {'success': True, 'sent': 0, 'message': 'No contacts to send'}
    
    # Get email provider
    email_provider_instance = None
    provider_name = "Unknown"
    try:
        if campaign.email_provider:
            # Use campaign-specific provider (OrganizationEmailProvider)
            org_provider = campaign.email_provider
            provider_config = org_provider.get_effective_config()
            provider_type = org_provider.provider.provider_type
            provider_name = org_provider.provider.name
            email_provider_instance = EmailProviderFactory.create_provider(provider_type, provider_config)
            logger.info(f"[launch_campaign_task] Using campaign-specific provider: {provider_name}")
        else:
            # Use organization's primary provider
            org_provider = OrganizationEmailProvider.objects.filter(
                organization=campaign.organization,
                is_enabled=True,
                is_primary=True,
                provider__is_active=True
            ).select_related('provider').first()
            
            if org_provider:
                provider_config = org_provider.get_effective_config()
                provider_type = org_provider.provider.provider_type
                provider_name = org_provider.provider.name
                email_provider_instance = EmailProviderFactory.create_provider(provider_type, provider_config)
                logger.info(f"[launch_campaign_task] Using organization primary provider: {provider_name}")
            else:
                # Fallback to organization-owned provider
                owned_provider = EmailProvider.objects.filter(
                    organization=campaign.organization,
                    is_default=True,
                    is_active=True
                ).first()
                
                if owned_provider:
                    provider_config = owned_provider.decrypt_config()
                    provider_name = owned_provider.name
                    email_provider_instance = EmailProviderFactory.create_provider(
                        owned_provider.provider_type, provider_config
                    )
                    logger.info(f"[launch_campaign_task] Using organization-owned provider: {provider_name}")
                else:
                    # Fallback to shared default provider
                    shared_provider = EmailProvider.objects.filter(
                        is_shared=True,
                        is_default=True,
                        is_active=True
                    ).first()
                    
                    if shared_provider:
                        provider_config = shared_provider.decrypt_config()
                        provider_name = shared_provider.name
                        email_provider_instance = EmailProviderFactory.create_provider(
                            shared_provider.provider_type, provider_config
                        )
                        logger.info(f"[launch_campaign_task] Using shared default provider: {provider_name}")
        
        if not email_provider_instance:
            raise Exception("No email provider configured for this organization")
    except Exception as e:
        logger.error(f"[launch_campaign_task] Failed to initialize email provider: {e}")
        campaign.status = 'FAILED'
        campaign.save(update_fields=['status'])
        return {'success': False, 'error': str(e)}
    
    # Process in batches
    batch_size = campaign.batch_size or 100
    batch_delay = campaign.batch_delay_seconds or 0
    sent_count = 0
    failed_count = 0
    
    # Prepare email content
    subject = campaign.subject
    html_content = campaign.html_content
    text_content = campaign.text_content or ''
    from_name = campaign.from_name
    from_email = campaign.from_email
    
    for i, contact in enumerate(contacts.iterator(chunk_size=batch_size)):
        # Check if campaign was paused
        campaign.refresh_from_db(fields=['status'])
        if campaign.status == 'PAUSED':
            logger.info(f"[launch_campaign_task] Campaign {campaign_id} paused, stopping")
            return {
                'success': True,
                'paused': True,
                'sent': sent_count,
                'failed': failed_count
            }
        
        if campaign.status == 'CANCELLED':
            logger.info(f"[launch_campaign_task] Campaign {campaign_id} cancelled, stopping")
            return {
                'success': True,
                'cancelled': True,
                'sent': sent_count,
                'failed': failed_count
            }
        
        # Personalize content for contact
        personalized_subject = subject
        personalized_html = html_content
        personalized_text = text_content
        
        # Simple variable replacement
        variables = {
            'first_name': contact.first_name or '',
            'last_name': contact.last_name or '',
            'email': contact.email,
            'full_name': contact.full_name or '',
            'unsubscribe_url': f'/api/campaigns/unsubscribe/?token={contact.unsubscribe_token}',
        }
        # Add custom fields
        if contact.custom_fields:
            variables.update(contact.custom_fields)
        
        for key, value in variables.items():
            placeholder = '{{' + key + '}}'
            personalized_subject = personalized_subject.replace(placeholder, str(value))
            personalized_html = personalized_html.replace(placeholder, str(value))
            personalized_text = personalized_text.replace(placeholder, str(value))
        
        try:
            # Send email using provider interface
            # Combine from_name and from_email for sender
            if from_name:
                sender_email = f"{from_name} <{from_email}>"
            else:
                sender_email = from_email
            
            # Build headers if needed
            headers = {}
            if campaign.reply_to:
                headers['Reply-To'] = campaign.reply_to
            
            success, message_id, response_data = email_provider_instance.send_email(
                recipient_email=contact.email,
                subject=personalized_subject,
                html_content=personalized_html,
                text_content=personalized_text,
                sender_email=sender_email,
                headers=headers if headers else None
            )
            
            # Log delivery
            delivery_status = 'SENT' if success else 'FAILED'
            EmailDeliveryLog.objects.create(
                campaign=campaign,
                organization=campaign.organization,
                recipient_email=contact.email,
                contact=contact,
                sender_email=from_email,
                subject=personalized_subject,
                delivery_status=delivery_status,
                sent_at=timezone.now(),
                provider_message_id=message_id or '',
                error_message=response_data.get('error_message', '') if not success else '',
            )
            
            if success:
                sent_count += 1
                contact.emails_sent = (contact.emails_sent or 0) + 1
                contact.last_email_sent_at = timezone.now()
                contact.save(update_fields=['emails_sent', 'last_email_sent_at'])
            else:
                failed_count += 1
                
        except Exception as e:
            failed_count += 1
            logger.error(f"[launch_campaign_task] Error sending to {contact.email}: {e}")
            EmailDeliveryLog.objects.create(
                campaign=campaign,
                organization=campaign.organization,
                recipient_email=contact.email,
                contact=contact,
                sender_email=from_email,
                subject=personalized_subject,
                delivery_status='FAILED',
                sent_at=timezone.now(),
                error_message=str(e),
            )
        
        # Batch delay
        if batch_delay > 0 and (i + 1) % batch_size == 0:
            import time
            time.sleep(batch_delay)
    
    # Update campaign status
    campaign.status = 'SENT'
    campaign.completed_at = timezone.now()
    campaign.save(update_fields=['status', 'completed_at'])
    
    # Update stats
    campaign.update_stats_from_logs()
    
    logger.info(f"[launch_campaign_task] Campaign {campaign_id} completed. Sent: {sent_count}, Failed: {failed_count}")
    
    return {
        'success': True,
        'campaign_id': str(campaign_id),
        'sent': sent_count,
        'failed': failed_count,
        'total': total_contacts
    }


@shared_task(bind=True, max_retries=3)
def bulk_create_contacts_task(self, organization_id, contacts, list_id=None, update_existing=False, source='IMPORT', tags=None):
    """
    Async task for bulk contact creation when count exceeds threshold.
    
    Args:
        organization_id: UUID of the organization
        contacts: List of contact dictionaries
        list_id: Optional UUID of contact list to add contacts to
        update_existing: Whether to update existing contacts
        source: Import source identifier
        tags: List of tags to apply to all contacts
    """
    from .models import Contact, ContactList
    from apps.authentication.models import Organization
    from django.db import transaction
    import json
    
    logger.info(f"[bulk_create_contacts_task] Starting bulk import for org {organization_id}, {len(contacts)} contacts")
    
    try:
        organization = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        logger.error(f"[bulk_create_contacts_task] Organization {organization_id} not found")
        return {'success': False, 'error': f'Organization {organization_id} not found'}
    
    contact_list = None
    if list_id:
        contact_list = ContactList.objects.filter(
            id=list_id,
            organization=organization
        ).first()
    
    tags = tags or []
    created = 0
    updated = 0
    skipped = 0
    errors = []
    
    # Process in chunks for database efficiency
    chunk_size = 500
    
    for chunk_start in range(0, len(contacts), chunk_size):
        chunk = contacts[chunk_start:chunk_start + chunk_size]
        
        with transaction.atomic():
            for idx, contact_data in enumerate(chunk):
                row_num = chunk_start + idx + 1
                try:
                    email = contact_data.get('email', '').strip().lower()
                    if not email:
                        errors.append({'row': row_num, 'error': 'Missing email'})
                        continue
                    
                    # Extract standard fields
                    first_name = contact_data.get('first_name', '') or contact_data.get('firstname', '')
                    last_name = contact_data.get('last_name', '') or contact_data.get('lastname', '')
                    phone = contact_data.get('phone', '') or contact_data.get('phone_number', '')
                    
                    # Extract tags from contact data
                    contact_tags = contact_data.get('tags', [])
                    if isinstance(contact_tags, str):
                        contact_tags = [t.strip() for t in contact_tags.split(',') if t.strip()]
                    all_tags = list(set(tags + contact_tags))
                    
                    # Extract metadata/custom_fields
                    metadata = contact_data.get('metadata', {})
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            metadata = {}
                    
                    # Build custom_fields
                    standard_fields = {'email', 'first_name', 'firstname', 'last_name', 'lastname', 
                                       'phone', 'phone_number', 'tags', 'metadata', 'custom_fields'}
                    custom_fields = {
                        k: v for k, v in contact_data.items()
                        if k.lower() not in standard_fields and v
                    }
                    custom_fields.update(metadata)
                    
                    contact, was_created = Contact.objects.get_or_create(
                        organization=organization,
                        email=email,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'phone': phone,
                            'source': source,
                            'tags': all_tags,
                            'custom_fields': custom_fields
                        }
                    )
                    
                    if was_created:
                        created += 1
                    elif update_existing:
                        if first_name:
                            contact.first_name = first_name
                        if last_name:
                            contact.last_name = last_name
                        if phone:
                            contact.phone = phone
                        if all_tags:
                            existing_tags = contact.tags or []
                            contact.tags = list(set(existing_tags + all_tags))
                        if custom_fields:
                            existing_cf = contact.custom_fields or {}
                            contact.custom_fields = {**existing_cf, **custom_fields}
                        contact.save()
                        updated += 1
                    else:
                        skipped += 1
                    
                    if contact_list:
                        contact.lists.add(contact_list)
                        
                except Exception as e:
                    errors.append({
                        'row': row_num,
                        'email': contact_data.get('email', 'unknown'),
                        'error': str(e)
                    })
    
    # Update list stats
    if contact_list:
        contact_list.update_stats()
    
    logger.info(f"[bulk_create_contacts_task] Completed. Created: {created}, Updated: {updated}, Skipped: {skipped}, Errors: {len(errors)}")
    
    return {
        'success': True,
        'created': created,
        'updated': updated,
        'skipped': skipped,
        'errors': errors[:100],  # Limit errors in response
        'total_errors': len(errors),
        'total': len(contacts)
    }


@shared_task(bind=True, max_retries=3)
def send_test_campaign_email(self, campaign_id, recipient_email, subject, html_content, text_content=None):
    """
    Send a test email for a campaign.
    
    Args:
        campaign_id: UUID of the campaign
        recipient_email: Email address to send test to
        subject: Email subject (usually prefixed with [TEST])
        html_content: HTML email body
        text_content: Plain text email body
    """
    from .models import Campaign, OrganizationEmailProvider, EmailProvider
    from .utils.email_providers import EmailProviderFactory
    
    try:
        campaign = Campaign.objects.select_related(
            'organization', 'email_provider', 'email_provider__provider'
        ).get(id=campaign_id)
    except Campaign.DoesNotExist:
        logger.error(f"[send_test_campaign_email] Campaign {campaign_id} not found")
        return {'success': False, 'error': f'Campaign {campaign_id} not found'}
    
    # Get email provider (same logic as launch_campaign_task)
    email_provider_instance = None
    provider_name = "Unknown"
    
    try:
        if campaign.email_provider:
            org_provider = campaign.email_provider
            provider_config = org_provider.get_effective_config()
            provider_type = org_provider.provider.provider_type
            provider_name = org_provider.provider.name
            email_provider_instance = EmailProviderFactory.create_provider(provider_type, provider_config)
        else:
            org_provider = OrganizationEmailProvider.objects.filter(
                organization=campaign.organization,
                is_enabled=True,
                is_primary=True,
                provider__is_active=True
            ).select_related('provider').first()
            
            if org_provider:
                provider_config = org_provider.get_effective_config()
                provider_type = org_provider.provider.provider_type
                provider_name = org_provider.provider.name
                email_provider_instance = EmailProviderFactory.create_provider(provider_type, provider_config)
            else:
                owned_provider = EmailProvider.objects.filter(
                    organization=campaign.organization,
                    is_default=True,
                    is_active=True
                ).first()
                
                if owned_provider:
                    provider_config = owned_provider.decrypt_config()
                    provider_name = owned_provider.name
                    email_provider_instance = EmailProviderFactory.create_provider(
                        owned_provider.provider_type, provider_config
                    )
                else:
                    shared_provider = EmailProvider.objects.filter(
                        is_shared=True,
                        is_default=True,
                        is_active=True
                    ).first()
                    
                    if shared_provider:
                        provider_config = shared_provider.decrypt_config()
                        provider_name = shared_provider.name
                        email_provider_instance = EmailProviderFactory.create_provider(
                            shared_provider.provider_type, provider_config
                        )
        
        if not email_provider_instance:
            raise Exception("No email provider configured")
            
    except Exception as e:
        logger.error(f"[send_test_campaign_email] Failed to initialize email provider: {e}")
        return {'success': False, 'error': str(e)}
    
    # Build sender email
    from_name = campaign.from_name
    from_email = campaign.from_email
    
    if from_name:
        sender_email = f"{from_name} <{from_email}>"
    else:
        sender_email = from_email
    
    # Build headers
    headers = {}
    if campaign.reply_to:
        headers['Reply-To'] = campaign.reply_to
    
    try:
        success, message_id, response_data = email_provider_instance.send_email(
            recipient_email=recipient_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content or '',
            sender_email=sender_email,
            headers=headers if headers else None
        )
        
        logger.info(f"[send_test_campaign_email] Test email sent to {recipient_email}: success={success}, message_id={message_id}")
        
        return {
            'success': success,
            'recipient': recipient_email,
            'message_id': message_id,
            'provider': provider_name,
            'response': response_data
        }
        
    except Exception as e:
        logger.error(f"[send_test_campaign_email] Error sending test email to {recipient_email}: {e}")
        return {
            'success': False,
            'recipient': recipient_email,
            'error': str(e)
        }