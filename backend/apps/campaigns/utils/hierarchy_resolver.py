"""
Hierarchical resolver for automation rules and email templates.

Templates resolve using a 2-level hierarchy:
1. Organization-owned template (when organization_id is provided)
2. Global template (organization IS NULL / is_global=True)

Automation rules are organization-scoped only — the old GLOBAL/TENANT rule
scope no longer exists in the schema.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

EMAIL_AUTOMATION_SERVICE_NAME = "Email Automation"


class HierarchicalResolver:
    """Resolves automation rules and email templates across the org → global hierarchy."""

    @staticmethod
    def get_automation_rule(
        reason_name: str,
        organization_id: str = None,
        communication_type: str = 'EMAIL'
    ):
        """
        Get an organization's automation rule for a reason.

        Args:
            reason_name: The reason/trigger for the automation (e.g., 'PASSWORD_RESET')
            organization_id: Organization UUID. Rules are organization-scoped, so
                this is required to find one.
            communication_type: Type of communication ('EMAIL', 'SMS', etc.)

        Returns:
            AutomationRule instance or None
        """
        from ..models import AutomationRule

        if not organization_id:
            logger.warning(
                f"[HierarchicalResolver] No organization_id given for reason={reason_name}; "
                "automation rules are organization-scoped"
            )
            return None

        rule = AutomationRule.objects.filter(
            organization_id=organization_id,
            reason_name=reason_name,
            communication_type=communication_type,
            is_active=True,
        ).first()

        if rule:
            logger.info(
                f"[HierarchicalResolver] Found rule for reason={reason_name}, "
                f"organization_id={organization_id}, rule_id={rule.id}"
            )
            return rule

        logger.warning(
            f"[HierarchicalResolver] No rule found for reason={reason_name}, "
            f"organization_id={organization_id}, communication_type={communication_type}"
        )
        return None

    @staticmethod
    def get_email_template(category: str, organization_id: str = None):
        """
        Get an email template following the organization → global hierarchy.

        Args:
            category: Template category matching reason_name (e.g., 'PASSWORD_RESET')
            organization_id: Optional organization UUID. If None, only global
                templates are considered.

        Returns:
            EmailTemplate instance or None
        """
        from ..models import EmailTemplate

        # Priority 1: organization-owned template
        if organization_id:
            org_template = EmailTemplate.objects.filter(
                organization_id=organization_id,
                category=category,
                is_active=True,
            ).first()

            if org_template:
                logger.info(
                    f"[HierarchicalResolver] Found organization template for category={category}, "
                    f"organization_id={organization_id}, template_id={org_template.id}"
                )
                return org_template

        # Priority 2: global template
        global_template = EmailTemplate.objects.filter(
            organization__isnull=True,
            is_global=True,
            category=category,
            is_active=True,
        ).first()

        if global_template:
            logger.info(
                f"[HierarchicalResolver] Using global template for category={category}, "
                f"template_id={global_template.id}"
            )
            return global_template

        logger.warning(
            f"[HierarchicalResolver] No template found for category={category}, "
            f"organization_id={organization_id}"
        )
        return None

    @staticmethod
    def get_rule_with_template(
        reason_name: str,
        organization_id: str = None,
        communication_type: str = 'EMAIL'
    ) -> Tuple[Optional[object], Optional[object]]:
        """
        Get both the automation rule and the email template for a reason.

        The rule's explicit template wins; otherwise the template is resolved
        through the organization → global hierarchy.

        Returns:
            Tuple of (AutomationRule or None, EmailTemplate or None)
        """
        rule = HierarchicalResolver.get_automation_rule(
            reason_name=reason_name,
            organization_id=organization_id,
            communication_type=communication_type
        )

        if rule and getattr(rule, 'email_template', None):
            return rule, rule.email_template

        template = HierarchicalResolver.get_email_template(
            category=reason_name,
            organization_id=organization_id
        )

        return rule, template


def is_email_service_active(organization_id: str = None, product_id: str = None) -> bool:
    """
    Whether the email service is active for triggering emails.

    The per-service subscription models this once consulted (ServiceDefinition,
    TenantServiceSubscription, ServiceProductActivation) no longer exist in
    this architecture. Per-organization gating now lives on
    OrganizationEmailConfiguration (is_active / is_suspended) and is enforced
    by can_send_email() on the send path, so this check defers to that.
    """
    from ..models import TenantEmailConfiguration

    if not organization_id:
        return True

    try:
        org_config = TenantEmailConfiguration.objects.get(organization_id=organization_id)
    except TenantEmailConfiguration.DoesNotExist:
        # No configuration yet: allow, the send path creates one on demand.
        return True

    if org_config.is_suspended or not org_config.is_active:
        logger.info(
            f"[is_email_service_active] Email service inactive for organization {organization_id} "
            f"(suspended={org_config.is_suspended}, active={org_config.is_active})"
        )
        return False

    return True
