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


def is_email_service_active(product_id=None, organization_id=None, tenant_id=None):
    """
    Check whether email sending is currently enabled for an organization.

    Args:
        product_id: Unused, retained for backward compatibility.
        organization_id: Organization UUID. None means a pre-signup send, which
            is always allowed.
        tenant_id: Legacy alias for organization_id.

    Returns:
        bool: True if the service is active, False otherwise
    """
    organization_id = organization_id or tenant_id
    try:
        return hierarchical_is_email_service_active(
            organization_id=organization_id,
            product_id=product_id
        )
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
                         product_id: str = None, organization_id: str = None,
                         tenant_id: str = None):
    """
    Look up an organization's automation rule by reason and send through it.

    Args:
        product_id: Unused, retained for backward compatibility.
        organization_id: Organization UUID that owns the rule.
        tenant_id: Legacy alias for organization_id.
    """
    organization_id = organization_id or tenant_id
    try:
        rule = HierarchicalResolver.get_automation_rule(
            reason_name=reason_name,
            organization_id=organization_id,
            communication_type=AutomationRule.CommunicationType.EMAIL,
        )
        if not rule:
            raise AutomationRule.DoesNotExist

        # Use the unified email sender
        return UnifiedEmailSender.send_email(
            rule=rule,
            recipient_emails=recipient_emails,
            email_variables=email_variables,
        )
    except AutomationRule.DoesNotExist:
        return False, f"AutomationRule for reason '{reason_name}' not found for the given organization.", {
            'reason': reason_name,
            'recipient_emails': recipient_emails,
            'organization_id': organization_id,
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