# Email models
from .email_config_models import (
    EmailTemplate,
    TemplateUsageLog,
    TemplateUpdateNotification,
    OrganizationTemplateNotification,
    TemplateApprovalRequest,
)
from .email_tracking_models import (
    EmailValidation,
    EmailQueue,
    EmailDeliveryLog,
    EmailAction,
)

# Organization email configuration
from .organization_email_config import (
    OrganizationEmailConfiguration,
    TenantEmailConfiguration,  # Legacy alias
)

# Provider models
from .provider_models import (
    EmailProvider,
    OrganizationEmailProvider,
    TenantEmailProvider,  # Legacy alias
    ProviderAuditLog,
)

# Automation models
from .automation_rule_model import AutomationRule

# Campaign models (new)
from .campaign_models import Campaign
from .contact_models import ContactList, Contact

# SMS models
from .sms_config_models import SMSConfigurationModel, SMSTemplate

# Push notification models
from .push_notification_config_models import *

# All exportable models
__all__ = [
    # Core models
    'EmailTemplate',
    'TemplateUsageLog',
    'TemplateUpdateNotification',
    'OrganizationTemplateNotification',
    'TemplateApprovalRequest',
    'EmailValidation',
    'EmailQueue',
    'EmailDeliveryLog',
    'EmailAction',
    
    # Organization config
    'OrganizationEmailConfiguration',
    'TenantEmailConfiguration',  # Legacy alias
    
    # Providers
    'EmailProvider',
    'OrganizationEmailProvider',
    'TenantEmailProvider',  # Legacy alias
    'ProviderAuditLog',
    
    # Automation
    'AutomationRule',
    
    # Campaign
    'Campaign',
    'ContactList',
    'Contact',
    
    # SMS
    'SMSConfigurationModel',
    'SMSTemplate',
]