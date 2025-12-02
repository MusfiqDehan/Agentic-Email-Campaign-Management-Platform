"""
Hierarchical resolver for automation rules, email templates, and providers.

This module provides utilities to resolve configurations using a 2-level hierarchy:
1. Tenant-specific configuration (if tenant_id is provided)
2. Global configuration (fallback when tenant-specific not found)

This enables pre-signup emails to work using global TMD configurations
before a tenant has their own rules, templates, or providers set up.
"""

import logging
from typing import Optional, Tuple

from django.db.models import Q

logger = logging.getLogger(__name__)

EMAIL_AUTOMATION_SERVICE_NAME = "Email Automation"


class HierarchicalResolver:
    """
    Resolves automation rules, email templates following tenant → global hierarchy.
    
    Hierarchy for all components:
    1. Tenant-specific (tenant_id matches)
    2. Global (tenant_id is NULL)
    
    This allows emails to be triggered before tenant signup is complete,
    using global TMD configurations.
    """
    
    @staticmethod
    def get_automation_rule(
        reason_name: str,
        tenant_id: str = None,
        communication_type: str = 'EMAIL'
    ):
        """
        Get automation rule following tenant → global hierarchy.
        
        Args:
            reason_name: The reason/trigger for the automation (e.g., 'PASSWORD_RESET')
            tenant_id: Optional tenant UUID. If None, only global rules are checked.
            communication_type: Type of communication ('EMAIL', 'SMS', etc.)
            
        Returns:
            AutomationRule instance or None
            
        Priority:
        1. Tenant-specific rule (tenant_id + reason_name + communication_type)
        2. Global rule (tenant_id=NULL + reason_name + communication_type)
        """
        from ..models import AutomationRule
        
        base_filter = {
            'reason_name': reason_name,
            'communication_type': communication_type,
            'activated_by_root': True,
            'activated_by_tmd': True,
            'is_deleted': False,
        }
        
        # Priority 1: Try tenant-specific rule
        if tenant_id:
            tenant_rule = AutomationRule.objects.filter(
                tenant_id=tenant_id,
                rule_scope=AutomationRule.RuleScope.TENANT,
                **base_filter
            ).first()
            
            if tenant_rule:
                logger.info(
                    f"[HierarchicalResolver] Found tenant rule for reason={reason_name}, "
                    f"tenant_id={tenant_id}, rule_id={tenant_rule.id}"
                )
                return tenant_rule
        
        # Priority 2: Fallback to global rule
        global_rule = AutomationRule.objects.filter(
            tenant_id__isnull=True,
            rule_scope=AutomationRule.RuleScope.GLOBAL,
            **base_filter
        ).first()
        
        if global_rule:
            logger.info(
                f"[HierarchicalResolver] Using global rule for reason={reason_name}, "
                f"rule_id={global_rule.id}"
            )
            return global_rule
        
        logger.warning(
            f"[HierarchicalResolver] No rule found for reason={reason_name}, "
            f"tenant_id={tenant_id}, communication_type={communication_type}"
        )
        return None
    
    @staticmethod
    def get_email_template(
        category: str,
        tenant_id: str = None
    ):
        """
        Get email template following tenant → global hierarchy.
        
        Args:
            category: Template category matching reason_name (e.g., 'PASSWORD_RESET')
            tenant_id: Optional tenant UUID. If None, only global templates are checked.
            
        Returns:
            EmailTemplate instance or None
            
        Priority:
        1. Tenant-specific template (tenant_id + category)
        2. Global template (tenant_id=NULL + category)
        """
        from ..models import EmailTemplate
        
        base_filter = {
            'category': category,
            'activated_by_root': True,
            'activated_by_tmd': True,
            'is_deleted': False,
        }
        
        # Priority 1: Try tenant-specific template
        if tenant_id:
            tenant_template = EmailTemplate.objects.filter(
                tenant_id=tenant_id,
                template_type=EmailTemplate.TemplateType.TENANT,
                **base_filter
            ).first()
            
            if tenant_template:
                logger.info(
                    f"[HierarchicalResolver] Found tenant template for category={category}, "
                    f"tenant_id={tenant_id}, template_id={tenant_template.id}"
                )
                return tenant_template
        
        # Priority 2: Fallback to global template
        global_template = EmailTemplate.objects.filter(
            tenant_id__isnull=True,
            template_type=EmailTemplate.TemplateType.GLOBAL,
            **base_filter
        ).first()
        
        if global_template:
            logger.info(
                f"[HierarchicalResolver] Using global template for category={category}, "
                f"template_id={global_template.id}"
            )
            return global_template
        
        logger.warning(
            f"[HierarchicalResolver] No template found for category={category}, "
            f"tenant_id={tenant_id}"
        )
        return None
    
    @staticmethod
    def get_rule_with_template(
        reason_name: str,
        tenant_id: str = None,
        communication_type: str = 'EMAIL'
    ) -> Tuple[Optional[object], Optional[object]]:
        """
        Get both automation rule and email template following hierarchy.
        
        This is a convenience method that resolves both rule and template,
        where each can come from different levels of the hierarchy.
        
        For example:
        - Rule might be tenant-specific
        - Template might fall back to global if tenant doesn't have one
        
        Args:
            reason_name: The reason/trigger for the automation
            tenant_id: Optional tenant UUID
            communication_type: Type of communication
            
        Returns:
            Tuple of (AutomationRule or None, EmailTemplate or None)
        """
        rule = HierarchicalResolver.get_automation_rule(
            reason_name=reason_name,
            tenant_id=tenant_id,
            communication_type=communication_type
        )
        
        # If rule has an explicit template, use that
        if rule and hasattr(rule, 'email_template_id') and rule.email_template_id:
            return rule, rule.email_template_id
        
        # Otherwise, resolve template using hierarchy
        template = HierarchicalResolver.get_email_template(
            category=reason_name,
            tenant_id=tenant_id
        )
        
        return rule, template


def is_email_service_active(tenant_id: str = None, product_id: str = None) -> bool:
    """
    Check if email service is active for triggering emails.
    
    Hierarchy:
    1. Global (tenant_id=None): Only requires ServiceDefinition.activated_by_tmd=True
    2. Tenant (tenant_id provided): 
       - ServiceDefinition.activated_by_tmd=True (global service ON)
       - If tenant has subscription with activated_by_td=True, tenant can send emails
       - If no subscription exists, falls back to global (can still send emails)
    3. Product (product_id provided):
       - All above checks pass
       - ServiceProductActivation.is_active_by_tmd=True AND is_active_by_td=True
    
    Note: enabled_for_td controls whether tenant can subscribe and add their own
    Provider/Template/Rule, but doesn't block email triggering (falls back to global).
    
    Args:
        tenant_id: Optional tenant UUID
        product_id: Optional product UUID (for product-level activation check)
        
    Returns:
        bool: True if email service is active and can send emails
    """
    from service_integration.models import (
        ServiceDefinition, 
        TenantServiceSubscription,
        ServiceProductActivation
    )
    
    # =========================================================================
    # Level 1: Global Service Definition (TMD Control)
    # =========================================================================
    email_service = ServiceDefinition.objects.filter(
        service_name=EMAIL_AUTOMATION_SERVICE_NAME,
        activated_by_root=True,
        is_deleted=False
    ).first()
    
    if not email_service:
        logger.warning(
            "[is_email_service_active] No ServiceDefinition found for '%s'",
            EMAIL_AUTOMATION_SERVICE_NAME
        )
        return False
    
    # Master switch - if TMD hasn't activated, nothing works
    if not email_service.activated_by_tmd:
        logger.info("[is_email_service_active] Email service not activated by TMD")
        return False
    
    # For pre-signup (no tenant_id), global activation is sufficient
    if not tenant_id:
        logger.info("[is_email_service_active] No tenant_id, using global email service")
        return True
    
    # =========================================================================
    # Level 2: Tenant Subscription (TD Control)
    # =========================================================================
    subscription = TenantServiceSubscription.objects.filter(
        service_definition=email_service,
        tenant_id=tenant_id,
        is_deleted=False
    ).first()
    
    # If no subscription exists, tenant uses global config (allowed)
    if not subscription:
        logger.info(
            f"[is_email_service_active] No subscription for tenant {tenant_id}, "
            "using global email service"
        )
        return True
    
    # If tenant has explicitly deactivated the service, block email sending
    if not subscription.activated_by_td:
        logger.info(
            f"[is_email_service_active] Email service deactivated by tenant {tenant_id}"
        )
        return False
    
    # =========================================================================
    # Level 3: Product Activation (Optional - if product_id provided)
    # =========================================================================
    if product_id:
        product_activation = ServiceProductActivation.objects.filter(
            tenant_subscription=subscription,
            product_id=product_id,
            is_deleted=False
        ).first()
        
        # If no product activation exists, fall back to subscription-level (allowed)
        if not product_activation:
            logger.info(
                f"[is_email_service_active] No product activation for product {product_id}, "
                "using subscription-level access"
            )
            return True
        
        # Check TMD-level product activation
        if not product_activation.is_active_by_tmd:
            logger.info(
                f"[is_email_service_active] Product {product_id} not activated by TMD"
            )
            return False
        
        # Check TD-level product activation
        if not product_activation.is_active_by_td:
            logger.info(
                f"[is_email_service_active] Product {product_id} not activated by tenant"
            )
            return False
    
    # All checks passed
    logger.info(
        f"[is_email_service_active] Email service active for tenant={tenant_id}, "
        f"product={product_id}"
    )
    return True
