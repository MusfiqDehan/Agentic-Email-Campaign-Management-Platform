"""
Custom exceptions for campaigns app.

These exceptions provide better error categorization and handling
for email/SMS automation failures.
"""


class EmailSendingError(Exception):
    """Base exception for email sending failures."""
    def __init__(self, message: str, original_error=None, provider_type: str = None):
        self.message = message
        self.original_error = original_error
        self.provider_type = provider_type
        super().__init__(self.message)


class EmailVerificationError(EmailSendingError):
    """
    Raised when an email address or domain is not verified with the provider.
    
    This is typically recoverable by verifying the email/domain with the provider.
    """
    def __init__(self, message: str, unverified_email: str = None, **kwargs):
        self.unverified_email = unverified_email
        super().__init__(message, **kwargs)


class EmailQuotaExceededError(EmailSendingError):
    """
    Raised when the email provider's sending quota is exceeded.
    
    This may be temporary and could be resolved by waiting or upgrading quota.
    """
    pass


class EmailBlacklistedError(EmailSendingError):
    """
    Raised when attempting to send to a blacklisted or suppressed email address.
    """
    def __init__(self, message: str, blacklisted_email: str = None, **kwargs):
        self.blacklisted_email = blacklisted_email
        super().__init__(message, **kwargs)


class EmailInvalidRecipientError(EmailSendingError):
    """
    Raised when the recipient email address is invalid or malformed.
    """
    def __init__(self, message: str, invalid_email: str = None, **kwargs):
        self.invalid_email = invalid_email
        super().__init__(message, **kwargs)


class EmailProviderConfigError(EmailSendingError):
    """
    Raised when there's an issue with provider configuration (credentials, settings, etc.).
    """
    pass


class EmailProviderConnectionError(EmailSendingError):
    """
    Raised when unable to connect to the email provider.
    """
    pass


class SMSSendingError(Exception):
    """Base exception for SMS sending failures."""
    def __init__(self, message: str, original_error=None, provider_type: str = None):
        self.message = message
        self.original_error = original_error
        self.provider_type = provider_type
        super().__init__(self.message)
