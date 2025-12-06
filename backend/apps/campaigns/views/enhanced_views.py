import uuid
import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Avg
from rest_framework.response import Response
from rest_framework import status, permissions, generics, filters
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from ..models import (
    TenantEmailConfiguration, EmailProvider, TenantEmailProvider,
    EmailValidation, EmailQueue, EmailDeliveryLog, EmailAction,
    AutomationRule
)
from ..serializers import (
    TenantEmailConfigurationSerializer,
    EnhancedEmailDeliveryLogSerializer, EnhancedTriggerEmailSerializer
)
from ..serializers.enhanced_serializers import (
    TenantEmailProviderSerializer, EmailValidationSerializer,
    EmailQueueSerializer, EmailActionSerializer, EmailProviderSerializer,
    TenantOwnEmailProviderSerializer
)
from ..utils.tenant_service import TenantServiceAPI
from ..utils.email_providers import EmailProviderManager
from ..utils.email_utils import is_email_service_active, render_email_template
from ..tasks import process_email_queue_task, dispatch_enhanced_email_task, submit_email_queue_task
from core.mixins import CustomResponseMixin
from core.utils import UniversalAutoFilterMixin

logger = logging.getLogger(__name__)


class TenantEmailConfigurationListCreateView(CustomResponseMixin, generics.ListCreateAPIView):
    """List and create tenant email configurations"""
    
    queryset = TenantEmailConfiguration.objects.all()
    serializer_class = TenantEmailConfigurationSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'plan_type', 'is_suspended']
    search_fields = ['organization__name']
    ordering_fields = ['created_at', 'emails_sent_today', 'reputation_score']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset based on user permissions and organization access"""
        queryset = super().get_queryset()
        
        # Add organization filtering based on user permissions
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        return queryset


class TenantEmailConfigurationDetailView(CustomResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete tenant email configurations"""
    
    queryset = TenantEmailConfiguration.objects.all()
    serializer_class = TenantEmailConfigurationSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class TenantEmailConfigurationResetUsageView(CustomResponseMixin, APIView):
    """Reset usage counters for a tenant"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, pk):
        try:
            config = TenantEmailConfiguration.objects.get(pk=pk)
        except TenantEmailConfiguration.DoesNotExist:
            return self.error_response(
                message="Tenant configuration not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        config.emails_sent_today = 0
        config.emails_sent_this_month = 0
        config.last_daily_reset = timezone.now().date()
        config.last_monthly_reset = timezone.now().date()
        config.save()
        
        return self.success_response(
            data={
                'message': 'Usage counters reset successfully',
                'organization_id': str(config.organization_id)
            },
            message="Usage counters reset successfully"
        )


class TenantEmailConfigurationVerifyDomainView(CustomResponseMixin, APIView):
    """Verify custom domain for tenant"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, pk):
        try:
            config = TenantEmailConfiguration.objects.get(pk=pk)
        except TenantEmailConfiguration.DoesNotExist:
            return self.error_response(
                message="Tenant configuration not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if not config.custom_domain:
            return self.error_response(
                message="No custom domain configured",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # In production, this would involve actual DNS verification
        config.custom_domain_verified = True
        config.save()
        
        return self.success_response(
            data={
                'message': 'Domain verified successfully',
                'domain': config.custom_domain
            },
            message="Domain verified successfully"
        )


class TenantEmailConfigurationUsageStatsView(CustomResponseMixin, APIView):
    """Get usage statistics across tenants"""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        stats = TenantEmailConfiguration.objects.aggregate(
            total_tenants=Count('id'),
            active_tenants=Count('id', filter=Q(activated_by_root=True, activated_by_tmd=True)),
            total_emails_today=Count('emails_sent_today'),
            avg_reputation=Avg('reputation_score')
        )
        
        return self.success_response(
            data=stats,
            message="Usage statistics retrieved successfully"
        )


class EmailProviderListCreateView(UniversalAutoFilterMixin, CustomResponseMixin, generics.ListCreateAPIView):
    """List and create email providers with universal filtering"""
    
    queryset = EmailProvider.objects.filter(is_shared=True)
    serializer_class = EmailProviderSerializer
    permission_classes = [permissions.AllowAny]
    ordering = ['priority', 'name']

    def filter_queryset(self, queryset):
        """Extend base filtering to support config validity filtering.

        Adds support for query parameter `is_valid=true|false` which will
        dynamically validate each provider's decrypted configuration using the
        provider-specific `validate_config` implementation. This is performed in
        Python post-DB filtering because `config_status` is a computed field.

        Example:
            /api/email-providers?is_valid=true
        """
        queryset = super().filter_queryset(queryset)
        config_valid_param = self.request.query_params.get('is_valid')
        if config_valid_param is not None:
            desired = str(config_valid_param).lower() in ['true', '1', 'yes', 'on']
            from ..utils.email_providers import EmailProviderFactory
            matching_ids = []
            for provider in queryset:
                try:
                    config = provider.decrypt_config()
                    provider_instance = EmailProviderFactory.create_provider(provider.provider_type, config)
                    is_valid, _ = provider_instance.validate_config(config)
                except Exception:
                    is_valid = False
                if is_valid == desired:
                    matching_ids.append(provider.id)
            queryset = queryset.filter(id__in=matching_ids)
        return queryset

    
    def perform_create(self, serializer):
        """Override to handle auto health check after successful creation"""
        from ..utils.email_providers import EmailProviderFactory
        
        # Get the auto_health_check flag before creating
        auto_health_check = serializer.validated_data.get('auto_health_check', False)
        config = serializer.validated_data.get('config', {})
        
        logger.info(f"EmailProviderListCreateView.perform_create: auto_health_check={auto_health_check}, has_config={bool(config)}")
        
        # Create the provider instance
        instance = serializer.save()
        logger.info(f"Provider created: {instance.name}, current health_status: {instance.health_status}")
        
        # Perform health check if requested and config is available
        if auto_health_check and config:
            logger.info(f"Starting post-creation health check for {instance.name}")
            try:
                # Create provider instance for health check
                provider = EmailProviderFactory.create_provider(instance.provider_type, config)
                logger.info(f"Provider factory instance created for {instance.name}")
                
                # Perform health check
                is_healthy, message = provider.health_check()
                logger.info(f"Health check result for {instance.name}: healthy={is_healthy}, message={message}")
                
                # Update the instance
                instance.health_status = 'HEALTHY' if is_healthy else 'UNHEALTHY'
                instance.health_details = message
                instance.last_health_check = timezone.now()
                instance.save(update_fields=['health_status', 'health_details', 'last_health_check'])
                
                logger.info(f"Health status updated for {instance.name}: {instance.health_status}")
                
            except Exception as e:
                logger.error(f"Post-creation health check failed for {instance.name}: {e}", exc_info=True)
                instance.health_status = 'UNHEALTHY'
                instance.health_details = f"Health check failed: {str(e)}"
                instance.last_health_check = timezone.now()
                instance.save(update_fields=['health_status', 'health_details', 'last_health_check'])
        else:
            logger.info(f"Health check skipped for {instance.name}: auto_health_check={auto_health_check}, has_config={bool(config)}")


class EmailProviderDetailView(CustomResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete email providers"""
    
    queryset = EmailProvider.objects.all()
    serializer_class = EmailProviderSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        """Prevent unsetting the default provider by updating it to is_default=False.

        Allow other providers to be set as default (which will unset this one
        via the model.save() logic), but disallow direct unsetting that would
        leave no default provider.
        """
        instance = self.get_object()

        # If instance is currently default, do not allow a direct request to unset it
        if instance.is_default and 'is_default' in request.data:
            requested_value = request.data.get('is_default')
            # Normalize common string forms to boolean False
            if isinstance(requested_value, str):
                requested_value_normalized = requested_value.lower() in ['true', '1', 'yes', 'on']
            else:
                requested_value_normalized = bool(requested_value)

            if not requested_value_normalized:
                return self.error_response(
                    message="Cannot unset the default provider directly. Set another provider as default first.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Prevent deletion of the provider when it is the designated default."""
        instance = self.get_object()
        if instance.is_default:
            return self.error_response(
                message="Cannot delete the default provider. Assign a different provider as default before deleting.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)


class EmailProviderHealthCheckView(CustomResponseMixin, APIView):
    """Perform health check on a provider"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, pk):
        try:
            provider = EmailProvider.objects.get(pk=pk)
        except EmailProvider.DoesNotExist:
            return self.error_response(
                message="Email provider not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            from ..utils.email_providers import EmailProviderFactory
            
            config = provider.decrypt_config()
            provider_instance = EmailProviderFactory.create_provider(
                provider.provider_type, config
            )
            
            is_healthy, message = provider_instance.health_check()
            
            # Update provider health status
            provider.health_status = 'HEALTHY' if is_healthy else 'UNHEALTHY'
            provider.health_details = message
            provider.last_health_check = timezone.now()
            provider.save()
            
            return self.success_response(
                data={
                    'provider': provider.name,
                    'is_healthy': is_healthy,
                    'message': message,
                    'checked_at': provider.last_health_check
                },
                message="Health check completed successfully"
            )
            
        except Exception as e:
            logger.error(f"Health check failed for provider {provider.name}: {e}")
            
            provider.health_status = 'UNHEALTHY'
            provider.health_details = str(e)
            provider.last_health_check = timezone.now()
            provider.save()
            
            return self.error_response(
                message="Health check failed",
                data={
                    'provider': provider.name,
                    'is_healthy': False,
                    'message': str(e),
                    'checked_at': provider.last_health_check
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailProviderTestSendView(CustomResponseMixin, APIView):
    """Test email sending with this provider"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, pk):
        try:
            provider = EmailProvider.objects.get(pk=pk)
        except EmailProvider.DoesNotExist:
            return self.error_response(
                message="Email provider not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        test_email = request.data.get('test_email')
        if not test_email:
            return self.error_response(
                message="test_email is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from ..utils.email_providers import EmailProviderFactory
            
            config = provider.decrypt_config()
            provider_instance = EmailProviderFactory.create_provider(
                provider.provider_type, config
            )
            
            success, message_id, response_data = provider_instance.send_email(
                recipient_email=test_email,
                subject='Test Email from Email Automation System',
                html_content='<h1>Test Email</h1><p>This is a test email to verify provider configuration.</p>',
                text_content='Test Email\n\nThis is a test email to verify provider configuration.'
            )
            
            if success:
                return self.success_response(
                    data={
                        'success': True,
                        'message': 'Test email sent successfully',
                        'message_id': message_id,
                        'provider': provider.name
                    },
                    message="Test email sent successfully"
                )
            else:
                return self.error_response(
                    message="Failed to send test email",
                    data={
                        'success': False,
                        'error_details': response_data
                    },
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Test send failed for provider {provider.name}: {e}")
            return self.error_response(
                message="Test send failed",
                data={
                    'success': False,
                    'error': str(e)
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


TRUTHY_QUERY_VALUES = {'true', '1', 'yes', 'on', 'all'}


def _extract_email_body_from_log(log):
    """Return rendered HTML and text bodies for an email delivery log."""
    queue_item = getattr(log, 'queue_item', None)

    html_body = ''
    text_body = ''

    if queue_item:
        html_body = queue_item.html_content or ''
        text_body = queue_item.text_content or ''

    needs_render = not html_body or not text_body

    if needs_render:
        template = (
            getattr(log, 'email_template', None)
            or getattr(getattr(log, 'automation_rule', None), 'email_template_id', None)
        )
        context_data = getattr(log, 'context_data', {})
        context = context_data if isinstance(context_data, dict) else {}

        if template:
            try:
                _, rendered_html, rendered_text = render_email_template(template, context)
                html_body = html_body or rendered_html or ''
                text_body = text_body or rendered_text or ''
            except Exception as exc:
                logger.warning("Failed to render template for log %s: %s", log.id, exc)

    return {
        'html': html_body,
        'text': text_body,
    }


def _build_queue_payload_from_log(log, recipient_email, priority, subject_prefix=''):
    """Construct EmailQueue payload from an EmailDeliveryLog entry."""
    if not recipient_email:
        raise ValueError("Recipient email is required")

    automation_rule = log.automation_rule
    if not automation_rule:
        raise ValueError("Email delivery log is not linked to an automation rule")

    queue_item = getattr(log, 'queue_item', None)
    context_data = {}
    headers = {}
    subject = log.subject or ''
    html_content = ''
    text_content = ''

    if queue_item:
        context_data = queue_item.context_data or {}
        headers = queue_item.headers or {}
        html_content = queue_item.html_content or ''
        text_content = queue_item.text_content or ''
        subject = queue_item.subject or subject
    else:
        context_data = log.context_data or {}
        template = log.email_template or getattr(automation_rule, 'email_template_id', None)
        if template:
            try:
                rendered_subject, rendered_html, rendered_text = render_email_template(template, context_data)
                subject = rendered_subject or subject
                html_content = rendered_html or html_content
                text_content = rendered_text or text_content
            except Exception as exc:
                logger.warning(
                    "Failed to re-render template for log %s during resend/forward: %s",
                    log.id,
                    exc,
                    exc_info=True,
                )
        else:
            logger.warning(
                "No email template available for log %s; resend will use stored subject only",
                log.id,
            )

    context_data = context_data if isinstance(context_data, dict) else {}
    headers = headers if isinstance(headers, dict) else {}

    if subject_prefix:
        subject = f"{subject_prefix}{subject}" if subject else subject_prefix.strip()

    if not html_content and subject:
        html_content = f"<p>{subject}</p>"
    if not text_content and subject:
        text_content = subject

    return {
        'automation_rule': automation_rule,
        'tenant_id': (
            log.tenant_id
            or getattr(automation_rule, 'tenant_id', None)
            or getattr(getattr(automation_rule, 'tenant_email_config', None), 'tenant_id', None)
        ),
        'recipient_email': recipient_email,
        'subject': subject,
        'html_content': html_content,
        'text_content': text_content,
        'context_data': context_data,
        'headers': headers,
        'status': 'PENDING',
        'priority': priority,
        'scheduled_at': timezone.now(),
        'assigned_provider': log.email_provider,
        'error_message': '',
    }


class EmailDeliveryLogListView(UniversalAutoFilterMixin, CustomResponseMixin, generics.ListAPIView):
    """List email delivery logs with advanced dynamic filtering, searching and ordering.

    Features:
    - Dynamic filters on all primitive model fields (exact, contains, gte/lte, etc.)
    - Search across all text fields plus JSON key `context_data.name`
    - Ordering by any field plus annotated JSON key `context_name` (from `context_data.name`)
    - Range queries for `sent_at` via `sent_at__gte`, `sent_at__lte`, or `sent_at__range`

    Scope Handling:
    - `scope=global` returns only GLOBAL logs
    - `scope=tenant` returns only TENANT logs
    - `scope=all` or `include_global=true` returns combined scopes
    """

    queryset = EmailDeliveryLog.objects.all()
    serializer_class = EnhancedEmailDeliveryLogSerializer
    permission_classes = [permissions.AllowAny]
    # Default ordering when no explicit ordering param supplied
    ordering = ['-sent_at']

    def get_search_fields(self):  # Extend mixin search fields with JSON key lookup
        base_fields = super().get_search_fields()
        # Ensure core recipient and subject are present (should already be included)
        for f in ['recipient_email', 'subject', 'sender_email']:
            if f not in base_fields:
                base_fields.append(f)
        # Add JSON key path for name inside context_data
        json_key = 'context_data__name'
        if json_key not in base_fields:
            base_fields.append(json_key)
        return base_fields

    def get_ordering_fields(self):  # Extend ordering with annotated context_name
        base_fields = super().get_ordering_fields()
        if 'context_name' not in base_fields:
            base_fields.append('context_name')
        return base_fields

    def filter_queryset(self, queryset):  # Annotate before backends apply ordering/search
        try:
            from django.contrib.postgres.fields.jsonb import KeyTextTransform
            queryset = queryset.annotate(context_name=KeyTextTransform('name', 'context_data'))
        except Exception:
            # Non-Postgres or import issue: skip annotation silently
            pass
        return super().filter_queryset(queryset)

    def get_queryset(self):
        """Filter logs based on tenant and product access"""
        queryset = super().get_queryset()
        
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(
                Q(product_id=product_id) | Q(automation_rule__product_id=product_id)
            )
        
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(sent_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(sent_at__lte=date_to)
        
        return queryset.select_related('automation_rule', 'email_provider', 'email_validation', 'email_template')

    def list(self, request, *args, **kwargs):
        scope = request.query_params.get('scope', '').lower()
        include_global_flag = str(request.query_params.get('include_global', '')).lower()
        include_global = include_global_flag in TRUTHY_QUERY_VALUES

        # Remove scope and include_global from query params to prevent them from being treated as filters
        # These are special parameters for log_scope filtering, not model fields
        filtered_params = request.query_params.copy()
        filtered_params.pop('scope', None)
        filtered_params.pop('include_global', None)
        
        # Temporarily replace query_params to exclude scope parameters during filtering
        original_query_params = request.query_params
        request._request.GET = filtered_params
        
        queryset = self.filter_queryset(self.get_queryset())
        
        # Restore original query_params
        request._request.GET = original_query_params

        if scope == 'global':
            queryset = queryset.filter(log_scope='GLOBAL')
        elif scope == 'tenant':
            queryset = queryset.filter(log_scope='TENANT')
        elif scope == 'all':
            pass  # include both scopes
        elif include_global:
            pass  # include both scopes when explicitly requested
        else:
            queryset = queryset.filter(log_scope='TENANT')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        if scope == 'global':
            message = "Global email logs retrieved successfully"
            response_scope = 'GLOBAL'
        elif scope == 'tenant' and not include_global:
            message = "Tenant email logs retrieved successfully"
            response_scope = 'TENANT'
        elif include_global or scope == 'all':
            message = "Combined tenant and global email logs retrieved successfully"
            response_scope = 'COMBINED'
        else:
            message = "Tenant email logs retrieved successfully"
            response_scope = 'TENANT'

        return self.success_response(
            data={
                'count': len(serializer.data),
                'scope': response_scope,
                'results': serializer.data
            },
            message=message
        )


class EmailDeliveryLogDetailView(CustomResponseMixin, generics.RetrieveAPIView):
    """Retrieve email delivery log details"""
    
    queryset = EmailDeliveryLog.objects.all()
    serializer_class = EnhancedEmailDeliveryLogSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        log = self.get_object()
        serializer = self.get_serializer(log)
        data = dict(serializer.data)

        email_body = _extract_email_body_from_log(log)
        data['email_template_body'] = email_body.get('html', '')
        data['email_template_text_body'] = email_body.get('text', '')

        return self.success_response(
            data=data,
            message="Email delivery log retrieved successfully"
        )


class EmailDeliveryLogResendView(CustomResponseMixin, APIView):
    """Resend a failed or bounced email"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, pk):
        try:
            log = EmailDeliveryLog.objects.get(pk=pk)
        except EmailDeliveryLog.DoesNotExist:
            return self.error_response(
                message="Email delivery log not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if email can be resent
        if log.delivery_status not in ['FAILED', 'BOUNCED']:
            return self.error_response(
                message="Email can only be resent if status is FAILED or BOUNCED",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payload = _build_queue_payload_from_log(log, log.recipient_email, priority=1)
        except ValueError as exc:
            return self.error_response(
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                from ..models import EmailQueue

                new_queue_item = EmailQueue.objects.create(**payload)
                
                # Create action record
                EmailAction.objects.create(
                    original_log=log,
                    action_type='RESEND',
                    reason=request.data.get('reason', 'Manual resend'),
                    performed_by=request.user.id if hasattr(request.user, 'id') else None
                )
                
                # Trigger processing with idempotency guarantees
                try:
                    submit_email_queue_task(new_queue_item.id, priority=1)
                except Exception as task_error:
                    logger.warning(f"Task submission failed (might be duplicate): {task_error}")
                    # Task submission failure is not critical - task might already exist
                
                return self.success_response(
                    data={
                        'message': 'Email queued for resend',
                        'new_queue_id': str(new_queue_item.id)
                    },
                    message="Email queued for resend successfully"
                )
                
        except Exception as e:
            logger.error(f"Failed to resend email {log.id}: {e}")
            return self.error_response(
                message="Failed to queue email for resend",
                data={'details': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailDeliveryLogForwardView(CustomResponseMixin, APIView):
    """Forward email to a different recipient"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, pk):
        try:
            log = EmailDeliveryLog.objects.get(pk=pk)
        except EmailDeliveryLog.DoesNotExist:
            return self.error_response(
                message="Email delivery log not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        new_recipient = request.data.get('new_recipient')
        if not new_recipient:
            return self.error_response(
                message="new_recipient is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payload = _build_queue_payload_from_log(
                log,
                new_recipient,
                priority=3,
                subject_prefix='Fwd: '
            )
        except ValueError as exc:
            return self.error_response(
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                from ..models import EmailQueue

                new_queue_item = EmailQueue.objects.create(**payload)
                
                # Create action record
                EmailAction.objects.create(
                    original_log=log,
                    action_type='FORWARD',
                    new_recipient=new_recipient,
                    reason=request.data.get('reason', 'Manual forward'),
                    performed_by=request.user.id if hasattr(request.user, 'id') else None
                )
                
                # Trigger processing with idempotency guarantees
                try:
                    submit_email_queue_task(new_queue_item.id, priority=3)
                except Exception as task_error:
                    logger.warning(f"Task submission failed (might be duplicate): {task_error}")
                    # Task submission failure is not critical - task might already exist
                
                return self.success_response(
                    data={
                        'message': 'Email queued for forward',
                        'new_queue_id': str(new_queue_item.id),
                        'new_recipient': new_recipient
                    },
                    message="Email queued for forward successfully"
                )
                
        except Exception as e:
            logger.error(f"Failed to forward email {log.id}: {e}")
            return self.error_response(
                message="Failed to queue email for forward",
                data={'details': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailDeliveryLogAnalyticsView(CustomResponseMixin, APIView):
    """Get email analytics and statistics"""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Use the same filtering logic as the list view
        queryset = EmailDeliveryLog.objects.all()
        
        # Apply same filters as list view
        tenant_id = request.query_params.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        product_id = request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(
                Q(product_id=product_id) | Q(automation_rule__product_id=product_id)
            )
        scope = request.query_params.get('scope')
        if scope:
            scope = scope.upper()
            if scope in {'GLOBAL', 'TENANT'}:
                queryset = queryset.filter(log_scope=scope)
        
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(sent_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(sent_at__lte=date_to)
        
        # Basic stats
        total_emails = queryset.count()
        
        if total_emails == 0:
            return self.success_response(
                data={
                    'total_emails': 0,
                    'delivery_rates': {},
                    'engagement_rates': {},
                    'provider_stats': {}
                },
                message="No email data found for the specified filters"
            )
        
        # Delivery status breakdown
        delivery_stats = queryset.values('delivery_status').annotate(
            count=Count('id')
        ).order_by('delivery_status')
        
        # Engagement metrics
        opened_emails = queryset.filter(open_count__gt=0).count()
        clicked_emails = queryset.filter(click_count__gt=0).count()
        
        # Provider performance
        provider_stats = queryset.values(
            'email_provider__name'
        ).annotate(
            total=Count('id'),
            delivered=Count('id', filter=Q(delivery_status='DELIVERED')),
            bounced=Count('id', filter=Q(delivery_status='BOUNCED'))
        ).order_by('-total')
        
        return self.success_response(
            data={
                'total_emails': total_emails,
                'delivery_rates': {
                    stat['delivery_status']: {
                        'count': stat['count'],
                        'percentage': round((stat['count'] / total_emails) * 100, 2)
                    }
                    for stat in delivery_stats
                },
                'engagement_rates': {
                    'open_rate': round((opened_emails / total_emails) * 100, 2),
                    'click_rate': round((clicked_emails / total_emails) * 100, 2)
                },
                'provider_stats': [
                    {
                        'provider': stat['email_provider__name'],
                        'total': stat['total'],
                        'delivery_rate': round((stat['delivered'] / stat['total']) * 100, 2) if stat['total'] > 0 else 0,
                        'bounce_rate': round((stat['bounced'] / stat['total']) * 100, 2) if stat['total'] > 0 else 0
                    }
                    for stat in provider_stats
                ]
            },
            message="Email analytics retrieved successfully"
        )


# ========================================================================
# SECTION: TENANT-OWNED EMAIL PROVIDERS
# Allows tenants to create and manage their own email providers
# ========================================================================

class TenantOwnEmailProviderListCreateView(CustomResponseMixin, generics.ListCreateAPIView):
    """Tenants can create and manage their own email providers"""
    
    serializer_class = TenantOwnEmailProviderSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['provider_type', 'health_status', 'is_default']
    ordering_fields = ['priority', 'name', 'created_at']
    ordering = ['priority', 'name']
    
    def get_queryset(self):
        """Only show tenant-owned providers for this tenant"""
        tenant_id = self._get_tenant_from_request()
        
        if not tenant_id:
            return EmailProvider.objects.none()
        
        # Return ONLY organization-owned providers (not shared providers)
        return EmailProvider.objects.filter(
            organization_id=tenant_id,
            is_shared=False
        )
    
    def _get_tenant_from_request(self):
        """Extract tenant_id from request (query params or request body)"""
        # First check query parameters
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return tenant_id
        
        # Then check request body
        if hasattr(self.request, 'data') and isinstance(self.request.data, dict):
            tenant_id = self.request.data.get('tenant_id')
            if tenant_id:
                return tenant_id
        
        # Try to extract from JWT token or headers
        if hasattr(self.request, 'user') and hasattr(self.request.user, 'tenant_id'):
            return self.request.user.tenant_id
        
        return None
    
    def get_serializer_context(self):
        """Add tenant_id to serializer context"""
        context = super().get_serializer_context()
        tenant_id = self._get_tenant_from_request()
        context['tenant_id'] = tenant_id
        return context
    
    def perform_create(self, serializer):
        """Create tenant-owned provider with proper error handling"""
        tenant_id = self._get_tenant_from_request()
        
        if not tenant_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'tenant_id': 'tenant_id is required. Provide it as query parameter (?tenant_id=xxx) or in request body'
            })
        
        # Validate tenant_id format
        try:
            import uuid
            uuid.UUID(str(tenant_id))
        except (ValueError, AttributeError):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'tenant_id': f'Invalid tenant_id format. Must be a valid UUID, got: {tenant_id}'
            })
        
        serializer.save(organization_id=tenant_id, is_shared=False)

class TenantOwnEmailProviderDetailView(CustomResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete tenant-owned email provider configurations"""
    
    serializer_class = TenantOwnEmailProviderSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'
    
    def get_queryset(self):
        """Only show provider if it belongs to the tenant"""
        tenant_id = self._get_tenant_from_request()
        
        if not tenant_id:
            return EmailProvider.objects.none()
        
        return EmailProvider.objects.filter(
            organization_id=tenant_id,
            is_shared=False
        )
    
    def _get_tenant_from_request(self):
        """Extract tenant_id from request (query params, body, or JWT)"""
        # First check query parameters
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return tenant_id
        
        # Then check request body
        if hasattr(self.request, 'data') and isinstance(self.request.data, dict):
            tenant_id = self.request.data.get('tenant_id')
            if tenant_id:
                return tenant_id
        
        # Try to extract from JWT token or headers
        if hasattr(self.request, 'user') and hasattr(self.request.user, 'tenant_id'):
            return self.request.user.tenant_id
        
        return None
    
    def get_serializer_context(self):
        """Add tenant_id to serializer context"""
        context = super().get_serializer_context()
        tenant_id = self._get_tenant_from_request()
        context['tenant_id'] = tenant_id
        return context
    
    def destroy(self, request, *args, **kwargs):
        """Prevent deletion of default provider"""
        instance = self.get_object()
        if instance.is_default:
            return self.error_response(
                message="Cannot delete the default provider. Set another provider as default first.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

class TenantOwnEmailProviderHealthCheckView(CustomResponseMixin, APIView):
    """Perform health check on tenant-owned provider"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, pk):
        # Extract tenant_id from query params, body, or JWT
        tenant_id = (
            request.query_params.get('tenant_id') or
            (request.data.get('tenant_id') if isinstance(request.data, dict) else None) or
            (getattr(request.user, 'tenant_id', None) if hasattr(request, 'user') else None)
        )
        
        if not tenant_id:
            return self.error_response(
                message="tenant_id is required as query parameter, in request body, or must be authenticated",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            provider = EmailProvider.objects.get(
                pk=pk,
                organization_id=tenant_id,
                is_shared=False
            )
        except EmailProvider.DoesNotExist:
            return self.error_response(
                message="Email provider not found for this tenant",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            from ..utils.email_providers import EmailProviderFactory
            
            config = provider.decrypt_config()
            provider_instance = EmailProviderFactory.create_provider(
                provider.provider_type, config
            )
            
            is_healthy, message = provider_instance.health_check()
            
            # Update provider health status
            provider.health_status = 'HEALTHY' if is_healthy else 'UNHEALTHY'
            provider.health_details = message
            provider.last_health_check = timezone.now()
            provider.save()
            
            return self.success_response(
                data={
                    'provider': provider.name,
                    'is_healthy': is_healthy,
                    'message': message,
                    'checked_at': provider.last_health_check
                },
                message="Health check completed successfully"
            )
            
        except Exception as e:
            logger.error(f"Health check failed for provider {provider.name}: {e}")
            
            provider.health_status = 'UNHEALTHY'
            provider.health_details = str(e)
            provider.last_health_check = timezone.now()
            provider.save()
            
            return self.error_response(
                message="Health check failed",
                data={'error': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )


class TenantEmailProviderListCreateView(CustomResponseMixin, generics.ListCreateAPIView):
    """List and create tenant email provider configurations"""
    
    queryset = TenantEmailProvider.objects.all()
    serializer_class = TenantEmailProviderSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['organization', 'provider', 'is_enabled', 'is_primary']
    ordering_fields = ['created_at', 'provider__priority']
    ordering = ['provider__priority']


class TenantEmailProviderDetailView(CustomResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update and delete tenant email provider configurations"""
    
    queryset = TenantEmailProvider.objects.all()
    serializer_class = TenantEmailProviderSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class EmailValidationListView(CustomResponseMixin, generics.ListAPIView):
    """List email validation records"""
    
    queryset = EmailValidation.objects.all()
    serializer_class = EmailValidationSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['validation_status', 'is_valid_format', 'is_disposable', 'is_blacklisted']
    search_fields = ['email_address']
    ordering_fields = ['last_validated_at', 'validation_score']
    ordering = ['-last_validated_at']


class EmailValidationDetailView(CustomResponseMixin, generics.RetrieveAPIView):
    """Retrieve email validation details"""
    
    queryset = EmailValidation.objects.all()
    serializer_class = EmailValidationSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class EmailQueueListView(CustomResponseMixin, generics.ListAPIView):
    """List email queue items"""
    
    queryset = EmailQueue.objects.all()
    serializer_class = EmailQueueSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tenant_id', 'status', 'priority', 'automation_rule']
    search_fields = ['recipient_email', 'subject']
    ordering_fields = ['scheduled_at', 'created_at', 'priority']
    ordering = ['priority', 'scheduled_at']

    def get_queryset(self):
        """Filter queue based on tenant access"""
        queryset = super().get_queryset()
        
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        return queryset


class EmailQueueDetailView(CustomResponseMixin, generics.RetrieveAPIView):
    """Retrieve email queue item details"""
    
    queryset = EmailQueue.objects.all()
    serializer_class = EmailQueueSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class EmailQueueProcessView(CustomResponseMixin, APIView):
    """Process email queue items"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Trigger processing of pending email queue items"""
        try:
            from ..tasks import process_email_queue_batch
            
            # Get parameters
            batch_size = request.data.get('batch_size', 10)
            tenant_id = request.data.get('tenant_id')
            
            # Trigger batch processing
            task_result = process_email_queue_batch.delay(
                batch_size=batch_size,
                tenant_id=tenant_id
            )
            
            return self.success_response(
                data={
                    'message': 'Email queue processing started',
                    'task_id': str(task_result.id),
                    'batch_size': batch_size
                },
                message="Email queue processing initiated successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to process email queue: {e}")
            return self.error_response(
                message="Failed to initiate queue processing",
                data={'details': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailActionListView(CustomResponseMixin, generics.ListAPIView):
    """List email actions (resend, forward, etc.)"""
    
    queryset = EmailAction.objects.all()
    serializer_class = EmailActionSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action_type', 'original_log__tenant_id']
    search_fields = ['original_log__recipient_email', 'new_recipient']
    ordering_fields = ['performed_at']
    ordering = ['-performed_at']

    def get_queryset(self):
        """Filter actions based on tenant access"""
        queryset = super().get_queryset()
        
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(original_log__tenant_id=tenant_id)
        
        return queryset


class EmailActionDetailView(CustomResponseMixin, generics.RetrieveAPIView):
    """Retrieve email action details"""
    
    queryset = EmailAction.objects.all()
    serializer_class = EmailActionSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class EnhancedTriggerEmailView(CustomResponseMixin, generics.GenericAPIView):
    """Enhanced email triggering with provider-agnostic support"""
    
    permission_classes = [permissions.AllowAny]
    serializer_class = EnhancedTriggerEmailSerializer
    queryset = AutomationRule.objects.all()

    def post(self, request, *args, **kwargs):
        # Get correlation ID for tracing
        correlation_id = (
            request.headers.get("X-Request-ID") or 
            request.headers.get("X-Correlation-ID") or 
            str(uuid.uuid4())
        )
        
        debug = str(request.query_params.get("debug", "")).lower() in ("1", "true", "yes")
        
        # Validate request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            # Find the automation rule
            rule = self._find_automation_rule(data)
            if not rule:
                return Response({
                    "error_code": "RULE_NOT_FOUND",
                    "message": "No matching automation rule found",
                    "correlation_id": correlation_id
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if tenant can send emails
            tenant_id = data.get('tenant_id') or rule.tenant_id
            if not self._check_tenant_can_send(tenant_id):
                return Response({
                    "error_code": "TENANT_CANNOT_SEND",
                    "message": "Tenant is not allowed to send emails",
                    "tenant_id": str(tenant_id),
                    "correlation_id": correlation_id
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Process the email sending
            result = self._process_email_sending(rule, data, correlation_id, debug)
            return result
            
        except Exception as e:
            logger.exception(f"Error processing email trigger: {e}")
            return Response({
                "error_code": "PROCESSING_ERROR",
                "message": "Failed to process email trigger",
                "details": str(e),
                "correlation_id": correlation_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _find_automation_rule(self, data):
        """
        Find automation rule based on provided criteria.
        
        Priority:
        1. Rule ID (if provided)
        2. Tenant-specific rule matching criteria + product
        3. Tenant-specific rule matching criteria (ignore product)
        4. Global rule matching criteria + product
        5. Global rule matching criteria (ignore product - broadest fallback)
        """
        logger.info(f"Searching for automation rule with data: {data}")
        
        if data.get('rule_id'):
            rule = AutomationRule.objects.filter(
                id=data['rule_id'],
                activated_by_root=True,
                activated_by_tmd=True
            ).first()
            logger.info(f"Rule ID search result: {rule}")
            return rule
        
        # Build base filter criteria
        base_criteria = {
            'activated_by_root': True,
            'activated_by_tmd': True,
            'communication_type': AutomationRule.CommunicationType.EMAIL
        }
        
        # Add optional filters
        if data.get('automation_name'):
            base_criteria['automation_name'] = data['automation_name']
        
        if data.get('reason_name'):
            base_criteria['reason_name'] = data['reason_name']
        
        logger.info(f"Base search criteria: {base_criteria}")
        
        # First, try to find a tenant-specific rule
        tenant_id = data.get('tenant_id')
        product_id = data.get('product_id')
        
        if tenant_id:
            # Try with product_id first (most specific)
            if product_id:
                tenant_product_criteria = {**base_criteria, 'tenant_id': tenant_id, 'product_id': product_id}
                logger.info(f"Searching for tenant+product-specific rule with criteria: {tenant_product_criteria}")
                tenant_rule = AutomationRule.objects.filter(**tenant_product_criteria).first()
                if tenant_rule:
                    logger.info(f"Found tenant+product-specific rule: {tenant_rule.id}")
                    return tenant_rule
            
            # Try tenant-specific without product requirement
            tenant_criteria = {**base_criteria, 'tenant_id': tenant_id}
            logger.info(f"Searching for tenant-specific rule (any product) with criteria: {tenant_criteria}")
            tenant_rule = AutomationRule.objects.filter(**tenant_criteria).first()
            if tenant_rule:
                logger.info(f"Found tenant-specific rule: {tenant_rule.id} for tenant {tenant_id}")
                return tenant_rule
            else:
                logger.info(f"No tenant-specific rule found for tenant {tenant_id}")
        
        # Fallback to global rules (tenant_id__isnull=True)
        # Try with product_id first
        if product_id:
            global_product_criteria = {**base_criteria, 'tenant_id__isnull': True, 'product_id': product_id}
            logger.info(f"Searching for global+product rule with criteria: {global_product_criteria}")
            global_rule = AutomationRule.objects.filter(**global_product_criteria).first()
            if global_rule:
                logger.info(f"Using global+product rule: {global_rule.id}")
                return global_rule
        
        # Broadest fallback: global rule without product requirement
        global_criteria = {**base_criteria, 'tenant_id__isnull': True}
        logger.info(f"Searching for global rule (any product) with criteria: {global_criteria}")
        global_rule = AutomationRule.objects.filter(**global_criteria).first()
        
        if global_rule:
            logger.info(f"Using global rule: {global_rule.id} for tenant {tenant_id or 'N/A'}")
        else:
            logger.warning(f"No global rule found with criteria: {global_criteria}")
            # Debug: Check what rules exist at all
            all_rules = AutomationRule.objects.filter(
                activated_by_root=True,
                activated_by_tmd=True,
                communication_type=AutomationRule.CommunicationType.EMAIL
            ).values('id', 'automation_name', 'reason_name', 'product_id', 'tenant_id')
            logger.warning(f"Available rules in database: {list(all_rules)}")
        
        return global_rule
    
    def _check_tenant_can_send(self, tenant_id):
        """Check if tenant can send emails using service activation and local limits."""
        try:
            tenant_id_str = str(tenant_id) if tenant_id else None

            # Ensure the Email Automation service is active for this tenant (or globally as fallback)
            if tenant_id_str:
                if not is_email_service_active(tenant_id=tenant_id_str):
                    # from service_integration.models import ServiceDefinition  # Legacy - module doesn't exist
                    # Simplified: if service is not active, log and deny
                    logger.warning(
                        "Email service is not activated for tenant %s. Activate the service to proceed.",
                        tenant_id_str
                    )
                    return False
            else:
                if not is_email_service_active():
                    logger.warning("Email service is not activated globally; denying send request with no tenant context.")
                    return False

            # Check tenant-specific configuration limits
            if tenant_id_str:
                config = TenantEmailConfiguration.objects.filter(tenant_id=tenant_id).first()

                if config:
                    can_send, reason = config.can_send_email()
                    if not can_send:
                        logger.warning(
                            "Tenant %s cannot send email due to configuration limits: %s", tenant_id_str, reason
                        )
                    return can_send

                # If no config exists, provision a default configuration using tenant plan limits
                logger.info(
                    "No local email config for tenant %s. Creating default configuration and allowing send.",
                    tenant_id_str
                )
                limits = TenantServiceAPI.get_tenant_plan_limits(tenant_id_str)
                TenantEmailConfiguration.objects.get_or_create(
                    tenant_id=tenant_id,
                    defaults={
                        'plan_type': 'FREE',
                        'emails_per_day': limits.get('emails_per_day', 50),
                        'emails_per_month': limits.get('emails_per_month', 500),
                        'emails_per_minute': limits.get('emails_per_minute', 5),
                        'activated_by_tmd': True
                    }
                )

                return True

            # If we reach here without a tenant context, allow send (global context already validated)
            return True

        except Exception as e:
            logger.error("Error checking tenant send capability for %s: %s", tenant_id, e, exc_info=True)
            return False
    
    def _process_email_sending(self, rule, data, correlation_id, debug):
        """Process the actual email sending"""
        try:
            # Prepare task arguments
            task_args = [
                str(rule.id),
                data['recipient_emails'],
                data['email_variables'],
                {
                    'tenant_id': str(data.get('tenant_id') or rule.tenant_id),
                    'product_id': str(data.get('product_id') or rule.product_id) if data.get('product_id') or rule.product_id else None,
                    'email_template_id': str(data.get('email_template_id')) if data.get('email_template_id') else None,
                    'preferred_provider_id': str(data.get('preferred_provider_id')) if data.get('preferred_provider_id') else None,
                    'priority': data.get('priority', 5),
                    'correlation_id': correlation_id,
                    'skip_validation': data.get('skip_validation', False)
                }
            ]
            
            # Handle scheduling
            schedule_at = data.get('schedule_at')
            if schedule_at:
                # Schedule for future delivery
                delay_seconds = (schedule_at - timezone.now()).total_seconds()
                if delay_seconds <= 0:
                    delay_seconds = 0
                
                result = dispatch_enhanced_email_task.apply_async(
                    args=task_args, 
                    countdown=delay_seconds
                )
                
                return Response({
                    "message": f"Email scheduled for delivery at {schedule_at}",
                    "task_id": str(result.id),
                    "rule_id": str(rule.id),
                    "scheduled_at": schedule_at.isoformat(),
                    "correlation_id": correlation_id
                }, status=status.HTTP_202_ACCEPTED)
            
            elif rule.trigger_type == AutomationRule.TriggerType.IMMEDIATE:
                # Send immediately
                result = dispatch_enhanced_email_task.delay(*task_args)
                
                return Response({
                    "message": "Email queued for immediate delivery",
                    "task_id": str(result.id),
                    "rule_id": str(rule.id),
                    "correlation_id": correlation_id
                }, status=status.HTTP_202_ACCEPTED)
            
            elif rule.trigger_type == AutomationRule.TriggerType.DELAY:
                # Apply rule delay
                try:
                    delay_kwargs = {rule.delay_unit.lower(): rule.delay_amount}
                    delay_seconds = timedelta(**delay_kwargs).total_seconds()
                    
                    result = dispatch_enhanced_email_task.apply_async(
                        args=task_args, 
                        countdown=delay_seconds
                    )
                    
                    return Response({
                        "message": f"Email scheduled with {rule.delay_amount} {rule.delay_unit.lower()} delay",
                        "task_id": str(result.id),
                        "rule_id": str(rule.id),
                        "delay_seconds": delay_seconds,
                        "correlation_id": correlation_id
                    }, status=status.HTTP_202_ACCEPTED)
                    
                except Exception as e:
                    return Response({
                        "error_code": "INVALID_DELAY_CONFIG",
                        "message": "Invalid delay configuration",
                        "details": str(e),
                        "correlation_id": correlation_id
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            else:
                return Response({
                    "error_code": "UNSUPPORTED_TRIGGER_TYPE",
                    "message": f"Trigger type {rule.trigger_type} not supported for manual triggering",
                    "correlation_id": correlation_id
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.exception("Failed to process email sending")
            return Response({
                "error_code": "TASK_DISPATCH_FAILED",
                "message": "Failed to dispatch email task",
                "details": str(e),
                "correlation_id": correlation_id
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)