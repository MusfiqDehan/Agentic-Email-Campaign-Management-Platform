"""
Test cases for email error handling.
"""

import pytest
from unittest.mock import Mock
from botocore.exceptions import ClientError

from campaigns.utils.error_handlers import EmailErrorHandler
from campaigns.exceptions import (
    EmailVerificationError,
    EmailQuotaExceededError,
    EmailBlacklistedError,
    EmailInvalidRecipientError,
    EmailProviderConfigError,
    EmailProviderConnectionError,
)


class TestEmailErrorHandler:
    """Test suite for EmailErrorHandler."""
    
    def test_ses_verification_error_with_message_rejected(self):
        """Test handling of AWS SES MessageRejected error for unverified email."""
        # Create a mock ClientError as raised by boto3
        error_response = {
            'Error': {
                'Code': 'MessageRejected',
                'Message': 'Email address is not verified. The following identities failed the check in region EU-NORTH-1: mrdehan2016+td2@gmail.com'
            }
        }
        exception = ClientError(error_response, 'SendEmail')
        
        context = {
            'rule_id': 'test-rule-123',
            'recipient_email': 'mrdehan2016+td2@gmail.com',
        }
        
        is_retryable, user_message, classified_error = EmailErrorHandler.handle_exception(
            exception=exception,
            provider_type='AWS_SES',
            context=context
        )
        
        assert is_retryable is False
        assert isinstance(classified_error, EmailVerificationError)
        assert 'verification required' in user_message.lower()
        assert 'mrdehan2016+td2@gmail.com' in user_message
        assert classified_error.unverified_email == 'mrdehan2016+td2@gmail.com'
    
    def test_ses_throttling_error(self):
        """Test handling of AWS SES throttling/quota errors."""
        error_response = {
            'Error': {
                'Code': 'Throttling',
                'Message': 'Maximum sending rate exceeded'
            }
        }
        exception = ClientError(error_response, 'SendEmail')
        
        is_retryable, user_message, classified_error = EmailErrorHandler.handle_exception(
            exception=exception,
            provider_type='AWS_SES',
            context={'rule_id': 'test-rule-123'}
        )
        
        assert is_retryable is True
        assert isinstance(classified_error, EmailQuotaExceededError)
        assert 'quota exceeded' in user_message.lower()
    
    def test_ses_suppression_list_error(self):
        """Test handling of AWS SES suppression list errors."""
        error_response = {
            'Error': {
                'Code': 'MessageRejected',
                'Message': 'Address is on suppression list'
            }
        }
        exception = ClientError(error_response, 'SendEmail')
        
        context = {
            'rule_id': 'test-rule-123',
            'recipient_email': 'bounced@example.com',
        }
        
        is_retryable, user_message, classified_error = EmailErrorHandler.handle_exception(
            exception=exception,
            provider_type='AWS_SES',
            context=context
        )
        
        assert is_retryable is False
        assert isinstance(classified_error, EmailBlacklistedError)
        assert 'suppression list' in user_message.lower()
    
    def test_ses_invalid_email_error(self):
        """Test handling of AWS SES invalid email format errors."""
        error_response = {
            'Error': {
                'Code': 'InvalidParameterValue',
                'Message': 'Invalid email address format'
            }
        }
        exception = ClientError(error_response, 'SendEmail')
        
        context = {
            'rule_id': 'test-rule-123',
            'recipient_email': 'invalid-email',
        }
        
        is_retryable, user_message, classified_error = EmailErrorHandler.handle_exception(
            exception=exception,
            provider_type='AWS_SES',
            context=context
        )
        
        assert is_retryable is False
        assert isinstance(classified_error, EmailInvalidRecipientError)
        assert 'invalid email' in user_message.lower()
    
    def test_smtp_authentication_error(self):
        """Test handling of SMTP authentication failures."""
        exception = Exception('535 Authentication failed: Invalid credentials')
        
        is_retryable, user_message, classified_error = EmailErrorHandler.handle_exception(
            exception=exception,
            provider_type='SMTP',
            context={'rule_id': 'test-rule-123'}
        )
        
        assert is_retryable is False
        assert isinstance(classified_error, EmailProviderConfigError)
        assert 'authentication failed' in user_message.lower()
    
    def test_smtp_connection_error(self):
        """Test handling of SMTP connection failures."""
        exception = Exception('Connection refused by SMTP server')
        
        is_retryable, user_message, classified_error = EmailErrorHandler.handle_exception(
            exception=exception,
            provider_type='SMTP',
            context={'rule_id': 'test-rule-123'}
        )
        
        assert is_retryable is True
        assert isinstance(classified_error, EmailProviderConnectionError)
        assert 'unable to connect' in user_message.lower()
    
    def test_extract_email_from_message(self):
        """Test email extraction from error messages."""
        message = "Email address is not verified. The following identities failed the check in region EU-NORTH-1: mrdehan2016+td2@gmail.com"
        
        email = EmailErrorHandler._extract_email_from_message(message)
        
        assert email == 'mrdehan2016+td2@gmail.com'
    
    def test_generic_error_handling(self):
        """Test handling of generic/unknown errors."""
        exception = Exception('Some unknown error occurred')
        
        is_retryable, user_message, classified_error = EmailErrorHandler.handle_exception(
            exception=exception,
            provider_type=None,
            context={'rule_id': 'test-rule-123'}
        )
        
        assert is_retryable is True  # Default to retryable
        assert 'email sending failed' in user_message.lower()
