"""
Email provider error handling utilities.

This module provides intelligent error classification and handling
for various email provider errors (AWS SES, SMTP, etc.).
"""

import re
import logging
from typing import Tuple, Optional
from botocore.exceptions import ClientError, BotoCoreError

from ..exceptions import (
    EmailSendingError,
    EmailVerificationError,
    EmailQuotaExceededError,
    EmailBlacklistedError,
    EmailInvalidRecipientError,
    EmailProviderConfigError,
    EmailProviderConnectionError,
)

logger = logging.getLogger(__name__)


class EmailErrorHandler:
    """
    Centralized error handling for email sending operations.
    
    Classifies provider-specific errors into actionable exception types
    and provides user-friendly error messages.
    """
    
    # AWS SES error patterns
    SES_VERIFICATION_PATTERNS = [
        r"Email address is not verified",
        r"identity.*not verified",
        r"not authorized to send from",
        r"MAIL FROM domain.*not verified",
    ]
    
    SES_QUOTA_PATTERNS = [
        r"Daily message quota exceeded",
        r"Maximum sending rate exceeded",
        r"Throttling",
        r"sending quota",
    ]
    
    SES_BLACKLIST_PATTERNS = [
        r"Address is on.*suppression list",
        r"recipient.*suppressed",
        r"account.*sending disabled",
    ]
    
    SES_INVALID_PATTERNS = [
        r"Invalid.*email address",
        r"Recipient address rejected",
        r"Malformed.*address",
    ]
    
    # SMTP error patterns
    SMTP_AUTH_PATTERNS = [
        r"authentication failed",
        r"invalid credentials",
        r"535",  # SMTP auth error code
    ]
    
    SMTP_CONNECTION_PATTERNS = [
        r"connection refused",
        r"connection timeout",
        r"network unreachable",
        r"could not connect",
    ]
    
    @classmethod
    def handle_exception(
        cls,
        exception: Exception,
        provider_type: str = None,
        context: dict = None
    ) -> Tuple[bool, str, Optional[Exception]]:
        """
        Process an exception and return structured error information.
        
        Args:
            exception: The caught exception
            provider_type: Email provider type (AWS_SES, SMTP, etc.)
            context: Additional context (recipient, rule_id, etc.)
            
        Returns:
            Tuple of (is_retryable, user_message, classified_exception)
        """
        context = context or {}
        provider_type = (provider_type or "UNKNOWN").upper()
        
        # Handle AWS SES errors
        if provider_type == "AWS_SES" or isinstance(exception, (ClientError, BotoCoreError)):
            return cls._handle_ses_error(exception, context)
        
        # Handle SMTP errors
        if provider_type in {"SMTP", "GMAIL_SMTP", "OUTLOOK_SMTP"} or "SMTP" in str(type(exception).__name__):
            return cls._handle_smtp_error(exception, context)
        
        # Generic error handling
        return cls._handle_generic_error(exception, context)
    
    @classmethod
    def _handle_ses_error(
        cls,
        exception: Exception,
        context: dict
    ) -> Tuple[bool, str, Optional[Exception]]:
        """Handle AWS SES specific errors."""
        error_message = str(exception)
        error_code = None
        
        # Extract error code from ClientError
        if isinstance(exception, ClientError):
            error_code = exception.response.get('Error', {}).get('Code', '')
            error_message = exception.response.get('Error', {}).get('Message', error_message)
        
        # Check for verification errors
        if error_code == "MessageRejected" or any(
            re.search(pattern, error_message, re.IGNORECASE)
            for pattern in cls.SES_VERIFICATION_PATTERNS
        ):
            # Extract unverified email from error message
            unverified_email = cls._extract_email_from_message(error_message)
            if not unverified_email:
                unverified_email = context.get('recipient_email') or context.get('from_email')
            
            user_message = (
                f"Email verification required: '{unverified_email}' is not verified with AWS SES. "
                f"Please verify this email address or domain in your AWS SES console before sending."
            )
            
            classified_error = EmailVerificationError(
                message=user_message,
                unverified_email=unverified_email,
                original_error=exception,
                provider_type="AWS_SES"
            )
            
            logger.warning(
                f"[EmailErrorHandler] SES Verification Error - "
                f"unverified_email={unverified_email} rule_id={context.get('rule_id')}",
                extra={"context": context}
            )
            
            return False, user_message, classified_error
        
        # Check for quota/throttling errors
        if error_code in {"Throttling", "ThrottlingException"} or any(
            re.search(pattern, error_message, re.IGNORECASE)
            for pattern in cls.SES_QUOTA_PATTERNS
        ):
            user_message = (
                "AWS SES sending quota exceeded. Please wait before retrying or "
                "request a quota increase in the AWS console."
            )
            
            classified_error = EmailQuotaExceededError(
                message=user_message,
                original_error=exception,
                provider_type="AWS_SES"
            )
            
            logger.warning(
                f"[EmailErrorHandler] SES Quota Exceeded - rule_id={context.get('rule_id')}",
                extra={"context": context}
            )
            
            return True, user_message, classified_error  # Retryable
        
        # Check for suppression/blacklist errors
        if any(
            re.search(pattern, error_message, re.IGNORECASE)
            for pattern in cls.SES_BLACKLIST_PATTERNS
        ):
            blacklisted_email = context.get('recipient_email')
            user_message = (
                f"Email '{blacklisted_email}' is on the AWS SES suppression list. "
                f"This typically occurs after bounces or complaints. "
                f"Remove it from the suppression list in AWS console to retry."
            )
            
            classified_error = EmailBlacklistedError(
                message=user_message,
                blacklisted_email=blacklisted_email,
                original_error=exception,
                provider_type="AWS_SES"
            )
            
            logger.warning(
                f"[EmailErrorHandler] SES Blacklist Error - "
                f"email={blacklisted_email} rule_id={context.get('rule_id')}",
                extra={"context": context}
            )
            
            return False, user_message, classified_error
        
        # Check for invalid email format
        if any(
            re.search(pattern, error_message, re.IGNORECASE)
            for pattern in cls.SES_INVALID_PATTERNS
        ):
            invalid_email = context.get('recipient_email')
            user_message = (
                f"Invalid email address: '{invalid_email}'. "
                f"Please verify the email format is correct."
            )
            
            classified_error = EmailInvalidRecipientError(
                message=user_message,
                invalid_email=invalid_email,
                original_error=exception,
                provider_type="AWS_SES"
            )
            
            logger.warning(
                f"[EmailErrorHandler] SES Invalid Email - "
                f"email={invalid_email} rule_id={context.get('rule_id')}",
                extra={"context": context}
            )
            
            return False, user_message, classified_error
        
        # Generic SES error
        user_message = f"AWS SES error: {error_message}"
        classified_error = EmailSendingError(
            message=user_message,
            original_error=exception,
            provider_type="AWS_SES"
        )
        
        logger.error(
            f"[EmailErrorHandler] Generic SES Error - "
            f"error_code={error_code} rule_id={context.get('rule_id')} message={error_message}",
            exc_info=True,
            extra={"context": context}
        )
        
        return True, user_message, classified_error  # Default to retryable
    
    @classmethod
    def _handle_smtp_error(
        cls,
        exception: Exception,
        context: dict
    ) -> Tuple[bool, str, Optional[Exception]]:
        """Handle SMTP specific errors."""
        error_message = str(exception)
        
        # Check for authentication errors
        if any(
            re.search(pattern, error_message, re.IGNORECASE)
            for pattern in cls.SMTP_AUTH_PATTERNS
        ):
            user_message = (
                "SMTP authentication failed. Please verify your email credentials "
                "(username and password) are correct."
            )
            
            classified_error = EmailProviderConfigError(
                message=user_message,
                original_error=exception,
                provider_type="SMTP"
            )
            
            logger.error(
                f"[EmailErrorHandler] SMTP Auth Error - rule_id={context.get('rule_id')}",
                extra={"context": context}
            )
            
            return False, user_message, classified_error
        
        # Check for connection errors
        if any(
            re.search(pattern, error_message, re.IGNORECASE)
            for pattern in cls.SMTP_CONNECTION_PATTERNS
        ):
            user_message = (
                "Unable to connect to SMTP server. Please verify the server address, "
                "port, and network connectivity."
            )
            
            classified_error = EmailProviderConnectionError(
                message=user_message,
                original_error=exception,
                provider_type="SMTP"
            )
            
            logger.error(
                f"[EmailErrorHandler] SMTP Connection Error - rule_id={context.get('rule_id')}",
                extra={"context": context}
            )
            
            return True, user_message, classified_error  # Retryable
        
        # Generic SMTP error
        user_message = f"SMTP error: {error_message}"
        classified_error = EmailSendingError(
            message=user_message,
            original_error=exception,
            provider_type="SMTP"
        )
        
        logger.error(
            f"[EmailErrorHandler] Generic SMTP Error - rule_id={context.get('rule_id')}",
            exc_info=True,
            extra={"context": context}
        )
        
        return True, user_message, classified_error
    
    @classmethod
    def _handle_generic_error(
        cls,
        exception: Exception,
        context: dict
    ) -> Tuple[bool, str, Optional[Exception]]:
        """Handle generic/unknown errors."""
        error_message = str(exception)
        user_message = f"Email sending failed: {error_message}"
        
        classified_error = EmailSendingError(
            message=user_message,
            original_error=exception,
            provider_type="UNKNOWN"
        )
        
        logger.error(
            f"[EmailErrorHandler] Generic Error - rule_id={context.get('rule_id')}",
            exc_info=True,
            extra={"context": context}
        )
        
        return True, user_message, classified_error
    
    @staticmethod
    def _extract_email_from_message(message: str) -> Optional[str]:
        """Extract email address from error message using regex."""
        # Pattern to match email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, message)
        
        if matches:
            # Return the last email found (usually the problematic one in SES errors)
            return matches[-1]
        
        return None
