import re
import logging
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.utils import timezone
from django.utils.html import strip_tags
from ..models import AutomationRule, EmailTemplate, EmailProvider
from ..backends import DynamicEmailBackend

# Legacy imports - commented out as we use the new unified approach
# from service_integration.models import ServiceDefinition
# from service_integration.models import is_service_active_for_product

# Import the new unified email sender
from .unified_email_sender import UnifiedEmailSender

# Import hierarchical resolver for new architecture
from .hierarchy_resolver import HierarchicalResolver
from .hierarchy_resolver import is_email_service_active as hierarchical_is_email_service_active

logger = logging.getLogger(__name__)


def is_email_service_active(product_id=None, tenant_id=None, use_new_architecture=True):
    """
    Checks if the Email Automation service is active through all required layers.
    
    Supports pre-signup scenarios where tenant_id may be None - in this case,
    only global service activation is checked.
    
    Args:
        product_id: Optional UUID of product to check specific activation
        tenant_id: Optional tenant ID to filter services (None for pre-signup)
        use_new_architecture: If True, use new ServiceDefinition architecture; 
                             if False, use legacy ServiceDefinition
        
    Returns:
        bool: True if service is active, False otherwise
    """
    # Use hierarchical resolver for new architecture (supports pre-signup)
    if use_new_architecture:
        try:
            return hierarchical_is_email_service_active(
                tenant_id=tenant_id,
                product_id=product_id
            )
        except Exception as e:
            logger.warning(f"Hierarchical check failed, falling back to legacy: {e}")
            # Fall through to legacy check
    
    # Legacy check (backward compatibility)
    try:
        # For pre-signup (no tenant_id), check global service only
        if not tenant_id:
            global_service = ServiceDefinition.objects.filter(
                service_name="Email Automation",
                tenant_id__isnull=True
            ).first()
            
            if not global_service:
                logger.warning("Global Email Automation service not found.")
                return False
            
            if not global_service.activated_by_tmd:
                logger.warning("Email service is not activated by TMD.")
                return False
            
            if not global_service.enabled_for_td:
                logger.warning("Email service is not enabled for TD.")
                return False
            
            # Global checks passed - allow pre-signup emails
            return True
        
        # For tenant-specific check
        query = {'service_name': "Email Automation", 'tenant_id': tenant_id}
        service = ServiceDefinition.objects.filter(**query).first()
        
        # If no tenant-specific record, fall back to global
        if not service:
            service = ServiceDefinition.objects.filter(
                service_name="Email Automation",
                tenant_id__isnull=True
            ).first()
            
            if not service:
                logger.warning("Email Automation service not found.")
                return False
        
        # Check TMD activation (required for all)
        if not service.activated_by_tmd:
            logger.warning("Email service is not activated by TMD.")
            return False
        
        if not service.enabled_for_td:
            logger.warning(f"Email service is not enabled for TD.")
            return False
        
        # All checks passed
        return True

    except Exception as e:
        logger.error(f"An error occurred while checking email service status: {e}")
        return False


def process_template_variables(template_text, context):
    """
    Replaces variables in template text with values from context.
    Variables are expected in the format {{variable_name}}.
    """
    def replace_var(match):
        var_name = match.group(1).strip()
        return str(context.get(var_name, ''))
    
    # Replace {{variable_name}} with corresponding value from context
    return re.sub(r'{{(.*?)}}', replace_var, template_text)


def render_email_template(email_template, context):
    """Render an EmailTemplate instance with the provided context.

    Args:
        email_template (EmailTemplate): The template instance to render.
        context (dict): Variables used to fill placeholders within the template.

    Returns:
        tuple[str, str, str]: Rendered subject, HTML body, and plain text body.
    """
    if not email_template:
        raise ValueError("Email template is required")

    if not isinstance(email_template, EmailTemplate):
        raise TypeError("render_email_template expects an EmailTemplate instance")

    context = context or {}

    if not isinstance(context, dict):
        raise TypeError("render_email_template context must be a dictionary")

    template_context = Context(context)

    subject_template = Template(email_template.email_subject or "")
    body_template = Template(email_template.email_body or "")

    rendered_subject = subject_template.render(template_context)
    rendered_html = body_template.render(template_context)
    rendered_text = strip_tags(rendered_html)

    return rendered_subject, rendered_html, rendered_text


def send_email_for_specific_rule(rule: AutomationRule, recipient_emails: list,
                                 email_variables: dict,
                                 override_email_template_id: int = None):
    """
    Send email strictly for a given AutomationRule instance.
    Optional override of template/config IDs.
    
    Returns:
        Tuple[bool, str, dict]: success flag, user-facing message, and metadata captured during dispatch
    """
    return UnifiedEmailSender.send_email(
        rule=rule,
        recipient_emails=recipient_emails,
        email_variables=email_variables,
        override_email_template_id=override_email_template_id
    )


def send_automated_email(recipient_emails: list, email_variables: dict, reason_name: str,
                         product_id: str, tenant_id: str = None):
    """
    Legacy / fallback lookup by reason + tenant/product.
    Returns first matching rule after applying precedence.
    
    REFACTORED: Now uses UnifiedEmailSender for consistency.
    """
    try:
        # --- Rule Prioritization Logic ---
        # Collect candidate rules
        rules_qs = AutomationRule.objects.filter(
            communication_type=AutomationRule.CommunicationType.EMAIL,
            reason_name=reason_name,
            activated_by_root=True,
        )
        if product_id:
            rules_qs = rules_qs.filter(product_id=product_id)
        # Prefer tenant-specific first if tenant_id provided
        if tenant_id:
            tenant_rules = rules_qs.filter(tenant_id=tenant_id)
            if tenant_rules.exists():
                rules_qs = tenant_rules
            else:
                rules_qs = rules_qs.filter(tenant_id__isnull=True)
        else:
            rules_qs = rules_qs.filter(tenant_id__isnull=True)

        if not rules_qs.exists():
            raise AutomationRule.DoesNotExist

        # Deterministic ordering: newest wins (or change to 'id')
        rule = rules_qs.order_by('-id').first()
        # --- End Prioritization ---

        # Use the unified email sender
        return UnifiedEmailSender.send_email(
            rule=rule,
            recipient_emails=recipient_emails,
            email_variables=email_variables,
        )
    except AutomationRule.DoesNotExist:
        return False, f"AutomationRule for reason '{reason_name}' not found for the given tenant/product.", {
            'reason': reason_name,
            'recipient_emails': recipient_emails,
            'tenant_id': tenant_id,
            'product_id': product_id,
        }
    except Exception as e:
        logger.error(f"ERROR sending automated email: {e}")
        return False, f"An error occurred while sending the email: {e}", {
            'reason': reason_name,
            'recipient_emails': recipient_emails,
            'tenant_id': tenant_id,
            'product_id': product_id,
            'error': str(e),
        }