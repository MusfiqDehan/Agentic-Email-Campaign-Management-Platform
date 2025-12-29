# Utils package for automation rule functionality

# Import from crypto module
from .crypto import (
    get_encryption_key,
    encrypt_data,
    decrypt_data,
)

# Import from email_utils module
from .email_utils import (
    is_email_service_active,
    process_template_variables,
    render_email_template,
    send_email_for_specific_rule,
    send_automated_email,
)

# Import from sms_utils module
from .sms_utils import (
    send_sms,
    send_whatsapp,
)

# Import from tenant_service module
from .tenant_service import TenantServiceAPI

# Import from unified_email_sender module
from .unified_email_sender import UnifiedEmailSender

# Import from sync_utils module
from .sync_utils import (
    ConfigurationHierarchy,
    RateLimitChecker,
    ConfigurationValidator,
    ConfigurationSync,
)

# Import from error_handlers module
from .error_handlers import EmailErrorHandler

# Import from hierarchy_resolver module
from .hierarchy_resolver import HierarchicalResolver, is_email_service_active as hierarchical_is_email_service_active

# Make all functions available at the package level
__all__ = [
    # Crypto functions
    'get_encryption_key',
    'encrypt_data',
    'decrypt_data',
    
    # Email functions
    'is_email_service_active',
    'process_template_variables',
    'render_email_template',
    'send_email_for_specific_rule',
    'send_automated_email',
    
    # SMS/WhatsApp functions
    'send_sms',
    'send_whatsapp',
    
    # Tenant service
    'TenantServiceAPI',
    
    # Unified email sender
    'UnifiedEmailSender',
    
    # Configuration sync utilities
    'ConfigurationHierarchy',
    'RateLimitChecker',
    'ConfigurationValidator',
    'ConfigurationSync',
    
    # Error handlers
    'EmailErrorHandler',
    
    # Hierarchical resolver
    'HierarchicalResolver',
]


