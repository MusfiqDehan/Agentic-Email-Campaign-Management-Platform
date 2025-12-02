"""
Unified email sending utility that consolidates email dispatch logic.

This module provides a single, comprehensive function for sending emails that:
- Handles both global and tenant-specific email automation
- Properly resolves configuration hierarchy
- Enforces rate limits across all layers
- Updates usage metrics consistently
- Reduces code duplication across views

The priority chain is Email Provider selection as follows:
1. Explicit provider ID supplied with the request.
2. Rule-level preference (get_effective_email_provider ⇒ tenant provider or rule’s preferred_global_provider).
3. Tenant’s primary enabled provider.
4. Global provider marked is_default=True.
5. Highest-priority remaining active global provider (ordered by priority, then name).

"""

import logging
from typing import Any, Dict, List, Tuple, Optional
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.utils.html import strip_tags

from ..models import AutomationRule, EmailTemplate, EmailProvider
from ..backends import DynamicEmailBackend
from ..exceptions import (
    EmailSendingError,
    EmailVerificationError,
    EmailQuotaExceededError,
    EmailBlacklistedError,
    EmailInvalidRecipientError,
)
from .sync_utils import ConfigurationHierarchy, RateLimitChecker
from .error_handlers import EmailErrorHandler

logger = logging.getLogger(__name__)


class UnifiedEmailSender:
    """Unified email sender that handles all email dispatch scenarios."""
    
    @staticmethod
    def send_email(
        rule: AutomationRule,
        recipient_emails: List[str],
        email_variables: Dict,
        override_email_template_id: str = None,
        override_from_email: str = None,
        preferred_provider_id: str = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Send email for a given AutomationRule with proper configuration resolution.
        
        This is the SINGLE source of truth for sending emails in the system.
        
        Args:
            rule: AutomationRule instance
            recipient_emails: List of recipient email addresses
            email_variables: Dict of template variables
            override_email_template_id: Optional EmailTemplate ID to use
            override_from_email: Optional from email address
            preferred_provider_id: Optional EmailProvider ID to use (manual override)
            
        Returns:
            Tuple of (success: bool, message: str, metadata: dict)
        """
        # Initialize variables that might be referenced in exception handlers
        from_email = None
        provider = None
        tenant_provider = None
        email_template = None
        
        try:
            metadata: Dict[str, Any] = {
                'rule_id': str(rule.id) if rule else None,
                'recipient_emails': recipient_emails,
                'override_email_template_id': str(override_email_template_id) if override_email_template_id else None,
                'preferred_provider_id': str(preferred_provider_id) if preferred_provider_id else None,
            }
            # 1. Resolve email template
            email_template = UnifiedEmailSender._resolve_email_template(
                rule, override_email_template_id
            )
            
            if not email_template:
                metadata['email_template_id'] = None
                return False, f"No email template found for rule '{rule.automation_name}'", metadata
            metadata['email_template_id'] = str(email_template.id)
            
            # 2. Render template
            rendered_subject, rendered_html, rendered_text = UnifiedEmailSender._render_template(
                email_template, email_variables
            )
            metadata['subject'] = rendered_subject
            metadata['html_body'] = rendered_html
            metadata['text_body'] = rendered_text
            
            # 3. Resolve provider and configuration (with optional manual override)
            provider, tenant_provider, provider_config = ConfigurationHierarchy.get_effective_provider(
                tenant_id=rule.tenant_id,
                rule=rule,
                preferred_provider_id=preferred_provider_id
            )
            
            if not provider:
                metadata['provider_id'] = None
                metadata['provider_name'] = None
                return False, "No email provider configured. Please configure at least one active provider.", metadata
            metadata['provider_id'] = str(provider.id)
            metadata['provider_name'] = provider.name
            metadata['provider_type'] = provider.provider_type
            metadata['tenant_provider_id'] = str(tenant_provider.id) if tenant_provider else None
            metadata['provider_selection'] = 'manual' if preferred_provider_id else 'automatic'
            
            # 4. Check rate limits across all layers
            can_send, reason = RateLimitChecker.can_send_email(
                tenant_id=rule.tenant_id,
                provider=provider,
                tenant_provider=tenant_provider
            )
            
            if not can_send:
                metadata['rate_limit_reason'] = reason
                return False, f"Rate limit check failed: {reason}", metadata
            
            # 5. Determine from_email
            try:
                from_email = UnifiedEmailSender._resolve_from_email(
                    override_from_email=override_from_email,
                    tenant_id=rule.tenant_id,
                    provider_config=provider_config
                )
                if not from_email:
                    metadata['from_email_error'] = 'No from_email could be resolved'
                    return False, "Failed to determine sender email address", metadata
                metadata['sender_email'] = from_email
            except Exception as e:
                logger.error(f"Error resolving from_email: {e}", exc_info=True)
                metadata['from_email_error'] = str(e)
                return False, f"Failed to determine sender email address: {str(e)}", metadata
            
            # 6. Build email connection
            connection = UnifiedEmailSender._build_connection(
                provider=provider,
                provider_config=provider_config
            )
            
            if not connection:
                metadata['connection_error'] = 'Failed to establish email connection'
                return False, "Failed to establish email connection", metadata
            
            # 7. Send email
            msg = EmailMultiAlternatives(
                subject=rendered_subject,
                body=rendered_text,
                from_email=from_email,
                to=recipient_emails,
                connection=connection,
            )
            msg.attach_alternative(rendered_html, "text/html")
            msg.send()
            
            # 8. Update usage metrics across all applicable layers
            RateLimitChecker.increment_usage_counters(
                tenant_id=rule.tenant_id,
                provider=provider,
                tenant_provider=tenant_provider
            )
            
            logger.info(
                f"[UnifiedEmailSender] Successfully sent email - rule={rule.id} "
                f"template={email_template.id} provider={provider.name} "
                f"recipients={len(recipient_emails)}"
            )
            
            metadata['delivery_status'] = 'SENT'
            return True, "Email sent successfully", metadata
            
        except (EmailVerificationError, EmailBlacklistedError, EmailInvalidRecipientError) as e:
            # These are non-retryable errors - provide clear user feedback
            logger.warning(
                f"[UnifiedEmailSender] Non-retryable email error for rule {rule.id}: {e.message}",
                extra={
                    "rule_id": str(rule.id),
                    "error_type": type(e).__name__,
                    "provider_type": getattr(e, 'provider_type', 'unknown'),
                }
            )
            metadata['error_type'] = type(e).__name__
            metadata['delivery_status'] = 'FAILED'
            metadata['error_message'] = e.message
            return False, e.message, metadata
            
        except EmailQuotaExceededError as e:
            # Quota exceeded - log as warning, may be retryable later
            logger.warning(
                f"[UnifiedEmailSender] Quota exceeded for rule {rule.id}: {e.message}",
                extra={
                    "rule_id": str(rule.id),
                    "provider_type": getattr(e, 'provider_type', 'unknown'),
                }
            )
            metadata['error_type'] = type(e).__name__
            metadata['delivery_status'] = 'FAILED'
            metadata['error_message'] = e.message
            return False, e.message, metadata
            
        except Exception as e:
            # Use error handler to classify the error
            is_retryable, user_message, classified_error = EmailErrorHandler.handle_exception(
                exception=e,
                provider_type=provider.provider_type if provider else None,
                context={
                    'rule_id': str(rule.id),
                    'recipient_email': recipient_emails[0] if recipient_emails else None,
                    'from_email': from_email if from_email else 'not_set',
                    'provider_name': provider.name if provider else 'unknown',
                }
            )
            
            logger.error(
                f"[UnifiedEmailSender] Failed to send email for rule {rule.id}: {user_message}",
                exc_info=True,
                extra={
                    "rule_id": str(rule.id),
                    "is_retryable": is_retryable,
                    "error_type": type(classified_error).__name__ if classified_error else type(e).__name__,
                    "provider_type": provider.provider_type if provider else 'unknown',
                }
            )
            
            metadata['error_type'] = type(classified_error).__name__ if classified_error else type(e).__name__
            metadata['delivery_status'] = 'FAILED'
            metadata['error_message'] = user_message
            metadata['is_retryable'] = is_retryable
            return False, user_message, metadata
    
    @staticmethod
    def _resolve_email_template(rule: AutomationRule, override_template_id: str = None) -> Optional[EmailTemplate]:
        """
        Resolve EmailTemplate using hierarchical resolution.
        
        Priority:
        1. Override template ID (explicit parameter)
        2. Rule's email_template_id (if set on the rule)
        3. Hierarchical lookup: Tenant-specific template → Global template (by category/reason_name)
        """
        from .hierarchy_resolver import HierarchicalResolver
        
        if override_template_id:
            template = EmailTemplate.objects.filter(id=override_template_id).first()
            if template:
                return template
            logger.warning(f"Override template {override_template_id} not found")
        
        if hasattr(rule, 'email_template_id') and rule.email_template_id:
            return rule.email_template_id
        
        # Use hierarchical resolver for tenant → global fallback
        return HierarchicalResolver.get_email_template(
            category=rule.reason_name,
            tenant_id=rule.tenant_id
        )
    
    @staticmethod
    def _render_template(template: EmailTemplate, variables: Dict) -> Tuple[str, str, str]:
        """
        Render email template with variables.
        
        Returns:
            Tuple of (subject, html_body, text_body)
        """
        context = Context(variables or {})
        
        subject_template = Template(template.email_subject or "")
        body_template = Template(template.email_body or "")
        
        rendered_subject = subject_template.render(context)
        rendered_html = body_template.render(context)
        rendered_text = strip_tags(rendered_html)
        
        return rendered_subject, rendered_html, rendered_text
    
    @staticmethod
    def _resolve_from_email(
        override_from_email: str = None,
        tenant_id: str = None,
        provider_config: Dict = None
    ) -> str:
        """
        Resolve from_email address.
        
        Priority:
        1. Override from_email
        2. Tenant custom/default domain (from TenantEmailConfiguration)
        3. Provider config from_email
        4. Fallback default
        """
        if override_from_email:
            return override_from_email
        
        # Use configuration hierarchy
        return ConfigurationHierarchy.get_effective_from_email(
            tenant_id=tenant_id,
            provider_config=provider_config,
            rule=None
        )
    
    @staticmethod
    def _build_connection(
        provider: EmailProvider = None,
        provider_config: Dict = None
    ):
        """
        Build email backend connection using EmailProvider.
        
        Args:
            provider: EmailProvider instance
            provider_config: Decrypted provider configuration dict
            
        Returns:
            Email backend connection or None
        """
        if not provider or not provider_config:
            logger.error("No provider or provider_config available")
            return None
            
        try:
            logger.info(f"[UnifiedEmailSender] Building connection - provider_type={provider.provider_type}, config_keys={list(provider_config.keys())}")
            connection, metadata = DynamicEmailBackend.build_provider_connection(
                provider.provider_type,
                provider_config,
                fail_silently=False,
            )
            logger.info(f"[UnifiedEmailSender] Connection built successfully - metadata={metadata}")
            return connection
        except Exception as e:
            logger.error(f"Failed to build provider connection: {e}", exc_info=True)
            return None


# Maintain backward compatibility with existing function names
# def send_email_for_specific_rule(
#     rule: AutomationRule,
#     recipient_emails: list,
#     email_variables: dict,
#     override_email_template_id: int = None
# ):
#     """
#     Backward compatible wrapper for send_email_for_specific_rule.
    
#     DEPRECATED: Use UnifiedEmailSender.send_email directly.
#     """
#     return UnifiedEmailSender.send_email(
#         rule=rule,
#         recipient_emails=recipient_emails,
#         email_variables=email_variables,
#         override_email_template_id=override_email_template_id
#     )


# def send_automated_email(
#     recipient_emails: list,
#     email_variables: dict,
#     reason_name: str,
#     product_id: str,
#     tenant_id: str = None
# ):
#     """
#     Backward compatible wrapper for send_automated_email.
    
#     DEPRECATED: Use UnifiedEmailSender.send_email with proper rule lookup.
#     """
#     try:
#         # Find matching rule
#         rules_qs = AutomationRule.objects.filter(
#             communication_type=AutomationRule.CommunicationType.EMAIL,
#             reason_name=reason_name,
#             activated_by_root=True,
#         )
        
#         if product_id:
#             rules_qs = rules_qs.filter(product_id=product_id)
        
#         if tenant_id:
#             tenant_rules = rules_qs.filter(tenant_id=tenant_id)
#             if tenant_rules.exists():
#                 rules_qs = tenant_rules
#             else:
#                 rules_qs = rules_qs.filter(tenant_id__isnull=True)
#         else:
#             rules_qs = rules_qs.filter(tenant_id__isnull=True)
        
#         if not rules_qs.exists():
#             raise AutomationRule.DoesNotExist
        
#         rule = rules_qs.order_by('-id').first()
        
#         return UnifiedEmailSender.send_email(
#             rule=rule,
#             recipient_emails=recipient_emails,
#             email_variables=email_variables
#         )
        
#     except AutomationRule.DoesNotExist:
#         return False, f"AutomationRule for reason '{reason_name}' not found"
#     except Exception as e:
#         logger.error(f"Error in send_automated_email: {e}")
#         return False, f"An error occurred: {e}"

