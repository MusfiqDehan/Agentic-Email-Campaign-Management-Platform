import logging
import boto3
import json
import requests
import base64
from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
from django.conf import settings
from django.utils import timezone
from botocore.exceptions import BotoCoreError, ClientError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class EmailProviderException(Exception):
    """Custom exception for email provider errors with standardized format"""
    
    def __init__(self, message: str, provider_type: str, error_code: str = None, suggestions: List[str] = None):
        self.message = message
        self.provider_type = provider_type
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.suggestions = suggestions or []
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to standardized error response format"""
        return {
            "success": False,
            "error": {
                "message": self.message,
                "code": self.error_code,
                "provider": self.provider_type,
                "suggestions": self.suggestions,
                "timestamp": timezone.now().isoformat()
            }
        }


class EmailProviderInterface(ABC):
    """Abstract base class for all email providers"""
    
    @abstractmethod
    def send_email(self, 
                   recipient_email: str, 
                   subject: str, 
                   html_content: str, 
                   text_content: str = None,
                   sender_email: str = None,
                   headers: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Send email via the provider
        
        Returns:
            Tuple of (success: bool, message_id: str, response_data: dict)
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate provider configuration"""
        pass
    
    @abstractmethod
    def health_check(self) -> Tuple[bool, str]:
        """Check if provider is healthy and operational"""
        pass


class AWSSESProvider(EmailProviderInterface):
    """Amazon SES email provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize SES client with provided configuration"""
        try:
            # Accept region, region_name, or aws_region_name
            region = (
                self.config.get('region')
                or self.config.get('region_name')
                or self.config.get('aws_region_name')
                or 'us-east-1'
            )
            # Support temporary credentials via STS
            session_token = self.config.get('aws_session_token') or self.config.get('session_token')
            self.client = boto3.client(
                'ses',
                aws_access_key_id=self.config.get('aws_access_key_id'),
                aws_secret_access_key=self.config.get('aws_secret_access_key'),
                aws_session_token=session_token,
                region_name=region
            )
        except Exception as e:
            logger.error(f"Failed to initialize SES client: {e}")
            raise
    
    def send_email(self, 
                   recipient_email: str, 
                   subject: str, 
                   html_content: str, 
                   text_content: str = None,
                   sender_email: str = None,
                   headers: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Send email via AWS SES"""
        try:
            # Prepare email content
            destination = {'ToAddresses': [recipient_email]}
            
            # Use configured sender or default (support multiple keys)
            source = (
                sender_email
                or self.config.get('default_sender_email')
                or self.config.get('default_from_email')
                or self.config.get('from_email')
            )
            if not source:
                return False, "", {"error": "No sender email configured"}
            
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {}
            }
            
            if html_content:
                message['Body']['Html'] = {'Data': html_content, 'Charset': 'UTF-8'}
            
            if text_content:
                message['Body']['Text'] = {'Data': text_content, 'Charset': 'UTF-8'}
            elif not html_content:
                # If no content provided, create basic text
                message['Body']['Text'] = {'Data': subject, 'Charset': 'UTF-8'}
            
            # Add custom headers if provided
            if headers:
                # SES doesn't support arbitrary headers in the simple send_email method
                # For custom headers, we'd need to use send_raw_email
                pass
            
            # Send email
            response = self.client.send_email(
                Source=source,
                Destination=destination,
                Message=message
            )
            
            message_id = response.get('MessageId', '')
            logger.info(f"Email sent successfully via SES: {message_id}")
            
            return True, message_id, {
                'provider': 'AWS_SES',
                'message_id': message_id,
                'response': response
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"SES ClientError: {error_code} - {error_message}")
            
            # Provide specific suggestions based on error code
            suggestions = []
            if error_code == 'MessageRejected':
                suggestions = [
                    "Verify sender email is verified in SES",
                    "Check recipient email format",
                    "Ensure content doesn't trigger spam filters"
                ]
            elif error_code == 'SendingPausedException':
                suggestions = [
                    "Account sending is paused, check SES console",
                    "Contact AWS support to resume sending"
                ]
            elif error_code == 'MailFromDomainNotVerifiedException':
                suggestions = [
                    "Verify the sender domain in SES console",
                    "Add required DNS records for domain verification"
                ]
            elif error_code == 'ConfigurationSetDoesNotExistException':
                suggestions = [
                    "Check configuration set name",
                    "Ensure configuration set exists in your AWS region"
                ]
            
            return False, "", {
                'success': False,
                'error': {
                    'message': error_message,
                    'code': error_code,
                    'provider': 'AWS_SES',
                    'type': 'ClientError',
                    'suggestions': suggestions,
                    'timestamp': timezone.now().isoformat()
                }
            }
            
        except BotoCoreError as e:
            logger.error(f"SES BotoCoreError: {e}")
            return False, "", {
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'BOTO_CORE_ERROR',
                    'provider': 'AWS_SES',
                    'type': 'BotoCoreError',
                    'suggestions': [
                        "Check AWS credentials and permissions",
                        "Verify AWS region configuration",
                        "Ensure SES service is available in your region"
                    ],
                    'timestamp': timezone.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"SES unexpected error: {e}")
            return False, "", {
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'UNEXPECTED_ERROR',
                    'provider': 'AWS_SES',
                    'type': 'Exception',
                    'suggestions': [
                        "Check email parameters and configuration",
                        "Verify network connectivity",
                        "Review application logs for more details"
                    ],
                    'timestamp': timezone.now().isoformat()
                }
            }
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate SES configuration"""
        # Normalize region
        region = config.get('region') or config.get('region_name') or config.get('aws_region_name')
        
        missing = []
        if not config.get('aws_access_key_id'):
            missing.append('aws_access_key_id')
        if not config.get('aws_secret_access_key'):
            missing.append('aws_secret_access_key')
        if not region:
            missing.append('region (or region_name)')
        if missing:
            return False, f"Missing required field(s): {', '.join(missing)}"
        
        # Test connection
        try:
            test_client = boto3.client(
                'ses',
                aws_access_key_id=config.get('aws_access_key_id'),
                aws_secret_access_key=config.get('aws_secret_access_key'),
                aws_session_token=(config.get('aws_session_token') or config.get('session_token')),
                region_name=region
            )
            test_client.get_send_quota()
            return True, "Configuration valid"
        except ClientError as e:
            code = e.response.get('Error', {}).get('Code')
            if code == 'InvalidClientTokenId':
                return False, "Configuration test failed: STS session token missing/expired or access key invalid. If using temporary credentials, include aws_session_token."
            return False, f"Configuration test failed: {code or str(e)}"
        except Exception as e:
            return False, f"Configuration test failed: {str(e)}"

    
    def health_check(self) -> Tuple[bool, str]:
        """Check SES service health"""
        try:
            if not self.client:
                return False, "SES client not initialized"
            
            # Get send quota as a health check
            response = self.client.get_send_quota()
            sent_last_24h = response.get('SentLast24Hours', 0)
            max_send_rate = response.get('MaxSendRate', 0)
            
            return True, f"Healthy - Sent: {sent_last_24h}, Rate: {max_send_rate}/sec"
            
        except Exception as e:
            return False, f"Health check failed: {str(e)}"


class SendGridProvider(EmailProviderInterface):
    """SendGrid email provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize SendGrid client"""
        try:
            import sendgrid
        except ImportError:
            raise ImportError("SendGrid package is required for SendGridProvider. Install with: pip install sendgrid")
        
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError("SendGrid API key is required")
        
        self.client = sendgrid.SendGridAPIClient(api_key=api_key)
    
    def send_email(self, 
                   recipient_email: str, 
                   subject: str, 
                   html_content: str, 
                   text_content: str = None,
                   sender_email: str = None,
                   headers: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Send email via SendGrid"""
        try:
            from sendgrid.helpers.mail import Mail
            
            # Use configured sender or default
            from_email = sender_email or self.config.get('default_sender_email')
            if not from_email:
                return False, "", {"error": "No sender email configured"}
            
            # Create mail object
            message = Mail(
                from_email=from_email,
                to_emails=recipient_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            
            # Add custom headers if provided
            if headers:
                for key, value in headers.items():
                    message.header = {key: value}
            
            # Send email
            response = self.client.send(message)
            
            # SendGrid returns 202 for success
            if response.status_code == 202:
                # SendGrid doesn't return message ID in the response headers typically
                message_id = response.headers.get('X-Message-Id', f"sendgrid_{timezone.now().timestamp()}")
                
                return True, message_id, {
                    'provider': 'SENDGRID',
                    'status_code': response.status_code,
                    'message_id': message_id
                }
            else:
                return False, "", {
                    'provider': 'SENDGRID',
                    'status_code': response.status_code,
                    'error_message': response.body
                }
                
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return False, "", {
                'provider': 'SENDGRID',
                'error_message': str(e),
                'error_type': 'UnexpectedError'
            }
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate SendGrid configuration"""
        if not config.get('api_key'):
            return False, "SendGrid API key is required"
        
        try:
            import sendgrid
            # Test the API key
            test_client = sendgrid.SendGridAPIClient(api_key=config['api_key'])
            # Make a simple API call to test the key
            response = test_client.user.get()
            if response.status_code == 200:
                return True, "Configuration valid"
            else:
                return False, f"API key test failed with status {response.status_code}"
                
        except Exception as e:
            return False, f"Configuration test failed: {str(e)}"
    
    def health_check(self) -> Tuple[bool, str]:
        """Check SendGrid service health"""
        try:
            if not self.client:
                return False, "SendGrid client not initialized"
            
            # Make a simple API call to check service health
            response = self.client.user.get()
            if response.status_code == 200:
                return True, "SendGrid service is healthy"
            else:
                return False, f"Health check failed with status {response.status_code}"
                
        except Exception as e:
            return False, f"Health check failed: {str(e)}"


class BrevoProvider(EmailProviderInterface):
    """Brevo (formerly Sendinblue) email provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = 'https://api.brevo.com/v3'
        
        if not self.api_key:
            raise ValueError("Brevo API key is required")
    
    def _make_api_request(self, endpoint: str, method: str = 'GET', data: Dict[str, Any] = None):
        """Make API request to Brevo"""
        import requests
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'api-key': self.api_key
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        return response
    
    def send_email(self, 
                   recipient_email: str, 
                   subject: str, 
                   html_content: str, 
                   text_content: str = None,
                   sender_email: str = None,
                   headers: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Send email via Brevo API"""
        try:
            # Use configured sender or default
            from_email = sender_email or self.config.get('from_email')
            from_name = self.config.get('from_name', 'System Notification')
            
            if not from_email:
                return False, "", {"error": "No sender email configured"}
            
            # Prepare email data
            email_data = {
                'sender': {
                    'email': from_email,
                    'name': from_name
                },
                'to': [{'email': recipient_email}],
                'subject': subject
            }
            
            # Add content
            if html_content:
                email_data['htmlContent'] = html_content
            
            if text_content:
                email_data['textContent'] = text_content
            elif not html_content:
                email_data['textContent'] = subject
            
            # Add reply-to if configured
            if self.config.get('reply_to'):
                email_data['replyTo'] = {'email': self.config['reply_to']}
            
            # Add tags if configured
            if self.config.get('tags'):
                email_data['tags'] = self.config['tags']
            
            # Add custom headers
            if headers:
                email_data['headers'] = headers
            
            # Send email via Brevo API
            response = self._make_api_request('smtp/email', method='POST', data=email_data)
            
            if response.status_code == 201:
                response_data = response.json()
                message_id = response_data.get('messageId', f"brevo_{timezone.now().timestamp()}")
                
                logger.info(f"Email sent successfully via Brevo: {message_id}")
                
                return True, message_id, {
                    'provider': 'BREVO',
                    'message_id': message_id,
                    'response': response_data
                }
            else:
                error_data = response.json() if response.content else {}
                return False, "", {
                    'provider': 'BREVO',
                    'status_code': response.status_code,
                    'error_message': error_data.get('message', 'Unknown error'),
                    'error_code': error_data.get('code'),
                    'error_type': 'APIError'
                }
                
        except Exception as e:
            logger.error(f"Brevo error: {e}")
            return False, "", {
                'provider': 'BREVO',
                'error_message': str(e),
                'error_type': 'UnexpectedError'
            }
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Brevo configuration"""
        if not config.get('api_key'):
            return False, "Brevo API key is required"
        
        if not config.get('from_email'):
            return False, "From email is required for Brevo"
        
        try:
            # Test API key by making an account info request
            test_headers = {
                'Accept': 'application/json',
                'api-key': config['api_key']
            }
            
            import requests
            response = requests.get(f"{self.base_url}/account", headers=test_headers)
            
            if response.status_code == 200:
                return True, "Configuration valid"
            else:
                error_data = response.json() if response.content else {}
                return False, f"API key validation failed: {error_data.get('message', 'Invalid API key')}"
                
        except Exception as e:
            return False, f"Configuration test failed: {str(e)}"
    
    def health_check(self) -> Tuple[bool, str]:
        """Check Brevo service health"""
        try:
            # Get account info to check health and quotas
            response = self._make_api_request('account')
            
            if response.status_code == 200:
                account_data = response.json()
                
                # Get plan info if available
                plan_type = account_data.get('plan', [{}])[0].get('type', 'Unknown')
                
                # Get email credits if available
                email_credits = account_data.get('plan', [{}])[0].get('creditsType', {})
                credits_remaining = email_credits.get('credits', 'Unknown')
                
                return True, f"Healthy - Plan: {plan_type}, Credits: {credits_remaining}"
            else:
                return False, f"Health check failed with status {response.status_code}"
                
        except Exception as e:
            return False, f"Health check failed: {str(e)}"


class SMTPProvider(EmailProviderInterface):
    """Enhanced SMTP email provider with OAuth2 support for Outlook/Microsoft 365"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = self._detect_provider_name()
    
    def _detect_provider_name(self) -> str:
        """Detect the SMTP provider based on server configuration"""
        smtp_server = self.config.get('smtp_server', '').lower()
        
        if 'outlook' in smtp_server or 'office365' in smtp_server:
            return 'Outlook SMTP'
        elif 'gmail' in smtp_server:
            return 'Gmail SMTP'
        elif 'yahoo' in smtp_server:
            return 'Yahoo SMTP'
        else:
            return 'Custom SMTP'
    
    def _authenticate_oauth2(self, server, username: str, access_token: str):
        """Authenticate using OAuth2 for Microsoft 365/Outlook"""
        try:
            # OAuth2 string format for SMTP
            auth_string = f"user={username}\x01auth=Bearer {access_token}\x01\x01"
            auth_string = auth_string.encode('ascii')
            
            # Use base64 encoding for the auth string
            import base64
            auth_string = base64.b64encode(auth_string).decode('ascii')
            
            # Send AUTH command
            server.docmd('AUTH', f'XOAUTH2 {auth_string}')
            
        except Exception as e:
            raise Exception(f"OAuth2 authentication failed: {str(e)}")
    
    def _get_oauth2_token(self) -> Optional[str]:
        """Get OAuth2 access token for Microsoft Graph API"""
        if not self.config.get('auth_method') == 'OAUTH2':
            return None
            
        try:
            import requests
            
            tenant_id = self.config.get('tenant_id')
            client_id = self.config.get('client_id')
            client_secret = self.config.get('client_secret')
            
            if not all([tenant_id, client_id, client_secret]):
                raise ValueError("Missing OAuth2 configuration")
            
            # Microsoft OAuth2 endpoint
            token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            
            data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                logger.error(f"OAuth2 token request failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting OAuth2 token: {e}")
            return None
    
    def send_email(self, 
                   recipient_email: str, 
                   subject: str, 
                   html_content: str, 
                   text_content: str = None,
                   sender_email: str = None,
                   headers: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Send email via SMTP with enhanced authentication support"""
        try:
            # Use configured sender or default
            from_email = sender_email or self.config.get('from_email') or self.config.get('username')
            if not from_email:
                return False, "", {"error": "No sender email configured"}
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = recipient_email
            
            # Add provider-specific headers
            if self.provider_name == 'Outlook SMTP':
                msg['X-MS-Exchange-Organization-AuthAs'] = 'Internal'
                msg['X-MS-Exchange-Organization-AuthMechanism'] = '10'
                
                # Add importance and sensitivity for Outlook
                importance = self.config.get('importance', 'normal')
                sensitivity = self.config.get('sensitivity', 'normal')
                
                if importance != 'normal':
                    msg['Importance'] = importance
                if sensitivity != 'normal':
                    msg['Sensitivity'] = sensitivity
            
            # Add custom headers
            if headers:
                for key, value in headers.items():
                    msg[key] = value
            
            # Add content
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Connect to SMTP server with proper SSL/TLS handling
            smtp_server = self.config.get('smtp_server') or self.config.get('host')
            smtp_port = self.config.get('smtp_port') or self.config.get('port', 587)
            
            use_ssl = self.config.get('use_ssl', False)
            use_tls = self.config.get('use_tls', not use_ssl)
            
            if use_ssl:
                # Use SMTP_SSL for port 465 (Gmail SSL)
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                # Use regular SMTP for port 587 (Gmail TLS)
                server = smtplib.SMTP(smtp_server, smtp_port)
                if use_tls:
                    server.starttls()
            
            # Authenticate
            username = self.config.get('username')
            
            if self.config.get('auth_method') == 'OAUTH2':
                # Use OAuth2 authentication
                access_token = self._get_oauth2_token()
                if access_token:
                    self._authenticate_oauth2(server, username, access_token)
                else:
                    return False, "", {
                        'provider': 'SMTP',
                        'error_message': 'Failed to obtain OAuth2 access token',
                        'error_type': 'AuthenticationError'
                    }
            elif username and self.config.get('password'):
                # Use basic authentication
                server.login(username, self.config['password'])
            
            # Send email
            text = msg.as_string()
            server.sendmail(from_email, recipient_email, text)
            server.quit()
            
            # Generate provider-specific message ID
            timestamp = timezone.now().timestamp()
            message_id = f"{self.provider_name.lower().replace(' ', '_')}_{timestamp}"
            
            return True, message_id, {
                'provider': 'SMTP',
                'provider_name': self.provider_name,
                'message_id': message_id,
                'smtp_server': smtp_server,
                'auth_method': self.config.get('auth_method', 'basic')
            }
            
        except Exception as e:
            logger.error(f"SMTP error ({self.provider_name}): {e}")
            return False, "", {
                'provider': 'SMTP',
                'provider_name': self.provider_name,
                'error_message': str(e),
                'error_type': 'SMTPError'
            }
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate SMTP configuration with OAuth2 support"""
        # Basic required fields
        smtp_server = config.get('smtp_server') or config.get('host')
        smtp_port = config.get('smtp_port') or config.get('port')
        
        if not smtp_server:
            return False, "SMTP server is required"
        
        if not smtp_port:
            return False, "SMTP port is required"
        
        # Check authentication configuration
        auth_method = config.get('auth_method', 'basic')
        
        if auth_method == 'OAUTH2':
            # Validate OAuth2 configuration
            required_oauth_fields = ['tenant_id', 'client_id', 'client_secret', 'username']
            for field in required_oauth_fields:
                if not config.get(field):
                    return False, f"Missing required OAuth2 field: {field}"
        else:
            # Validate basic authentication - accept multiple field name variations
            username = (
                config.get('username') 
                or config.get('smtp_username') 
                or config.get('email_host_user')
            )
            password = (
                config.get('password') 
                or config.get('smtp_password')
            )
            
            if not username or not password:
                return False, "Username and password are required for basic authentication"
        
        try:
            # Test connection with proper SSL/TLS handling
            use_ssl = config.get('use_ssl', False)
            use_tls = config.get('use_tls', not use_ssl)  # Default to TLS if SSL is not used
            
            if use_ssl:
                # Use SMTP_SSL for port 465 (Gmail SSL)
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                # Use regular SMTP for port 587 (Gmail TLS)
                server = smtplib.SMTP(smtp_server, smtp_port)
                if use_tls:
                    server.starttls()
            
            # Test authentication
            if auth_method == 'OAUTH2':
                # Test OAuth2 token retrieval
                access_token = self._get_oauth2_token()
                if access_token:
                    # Don't actually authenticate in validation, just check token retrieval
                    server.quit()
                    return True, "OAuth2 configuration valid"
                else:
                    server.quit()
                    return False, "Failed to obtain OAuth2 access token"
            else:
                # Test basic authentication - use the extracted username/password
                username = (
                    config.get('username') 
                    or config.get('smtp_username') 
                    or config.get('email_host_user')
                )
                password = (
                    config.get('password') 
                    or config.get('smtp_password')
                )
                
                if username and password:
                    server.login(username, password)
                
                server.quit()
                return True, "Configuration valid"
            
        except Exception as e:
            return False, f"Configuration test failed: {str(e)}"
    
    def health_check(self) -> Tuple[bool, str]:
        """Enhanced SMTP server health check with provider-specific details"""
        try:
            smtp_server = self.config.get('smtp_server') or self.config.get('host')
            smtp_port = self.config.get('smtp_port') or self.config.get('port', 587)
            
            # Handle SSL vs TLS properly
            use_ssl = self.config.get('use_ssl', False)
            use_tls = self.config.get('use_tls', not use_ssl)
            
            if use_ssl:
                # Use SMTP_SSL for port 465 (Gmail SSL)
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                # Use regular SMTP for port 587 (Gmail TLS)
                server = smtplib.SMTP(smtp_server, smtp_port)
                if use_tls:
                    server.starttls()
                
            status = server.noop()  # No-operation to test connection
            
            # Prepare detailed health info
            health_details = {
                'connection': 'OK',
                'smtp_server': f"{smtp_server}:{smtp_port}",
                'ssl_enabled': self.config.get('use_ssl', False),
                'tls_enabled': self.config.get('use_tls', not self.config.get('use_ssl', False)),
                'provider_name': self.provider_name
            }
            
            # Check authentication method
            auth_method = self.config.get('auth_method', 'basic')
            health_details['auth_method'] = auth_method
            
            if auth_method == 'OAUTH2':
                # Check OAuth2 token status
                access_token = self._get_oauth2_token()
                health_details['oauth_token_valid'] = access_token is not None
                
                if access_token:
                    # For Outlook, we could check token expiry here
                    health_details['authentication'] = 'VALID'
                else:
                    health_details['authentication'] = 'FAILED'
                    
            else:
                # Test basic auth if credentials available
                if self.config.get('username') and self.config.get('password'):
                    try:
                        server.login(self.config['username'], self.config['password'])
                        health_details['authentication'] = 'VALID'
                    except Exception as auth_e:
                        health_details['authentication'] = 'FAILED'
                        health_details['auth_error'] = str(auth_e)
                else:
                    health_details['authentication'] = 'NO_CREDENTIALS'
            
            server.quit()
            
            # Estimate daily limits based on provider
            daily_limit = self.config.get('daily_limit')
            if not daily_limit:
                if 'outlook' in smtp_server.lower():
                    daily_limit = 10000  # Microsoft 365 typical limit
                elif 'gmail' in smtp_server.lower():
                    daily_limit = 2000   # Gmail Workspace limit
                else:
                    daily_limit = 1000   # Conservative default
            
            health_details['daily_limit'] = daily_limit
            health_details['estimated_daily_sent'] = self.config.get('estimated_daily_sent', 0)
            
            return True, f"{self.provider_name} healthy - {health_details}"
            
        except Exception as e:
            return False, f"Health check failed: {str(e)}"


class EmailProviderFactory:
    """Factory class to create email provider instances"""
    
    PROVIDERS = {
        'AWS_SES': AWSSESProvider,
        'SENDGRID': SendGridProvider,
        'BREVO': BrevoProvider,
        'SMTP': SMTPProvider,
        'GMAIL_SMTP': SMTPProvider,
        'OUTLOOK_SMTP': SMTPProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any]) -> EmailProviderInterface:
        """Create an email provider instance"""
        provider_class = cls.PROVIDERS.get(provider_type)
        
        if not provider_class:
            raise ValueError(f"Unsupported provider type: {provider_type}")
        
        return provider_class(config)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider types"""
        return list(cls.PROVIDERS.keys())


class EmailProviderManager:
    """High-level manager for email provider operations"""
    
    def __init__(self, tenant_id: Optional[str]):
        self.tenant_id = tenant_id
        self._providers_cache = {}
    
    def get_provider_for_tenant(self, provider_config=None) -> Optional[EmailProviderInterface]:
        """Get the appropriate email provider for a tenant
        
        Priority order:
        1. Tenant-owned provider (if exists and enabled)
        2. Primary tenant-bound global provider
        3. Global default provider
        """
        from ..models.provider_models import TenantEmailProvider, EmailProvider
        from django.db.models import Q
        
        try:
            # If specific provider config is provided, use it
            if provider_config:
                provider_type = provider_config.provider.provider_type
                config = provider_config.get_effective_config()
                return EmailProviderFactory.create_provider(provider_type, config)
            
            # 1. Check for tenant-owned provider first
            if self.tenant_id:
                tenant_owned_provider = EmailProvider.objects.filter(
                    tenant_id=self.tenant_id,
                    is_global=False,
                    activated_by_root=True,
                    activated_by_tmd=True,
                    is_default=True  # Use the default tenant-owned provider
                ).first()
                
                if tenant_owned_provider:
                    config = tenant_owned_provider.decrypt_config()
                    return EmailProviderFactory.create_provider(tenant_owned_provider.provider_type, config)
            
            # 2. Get primary provider from tenant-bound global providers
            tenant_provider = None
            if self.tenant_id:
                tenant_provider = TenantEmailProvider.objects.filter(
                    tenant_id=self.tenant_id,
                    is_enabled=True,
                    is_primary=True
                ).select_related('provider').first()
            
            if tenant_provider:
                provider_type = tenant_provider.provider.provider_type
                config = tenant_provider.get_effective_config()
                return EmailProviderFactory.create_provider(provider_type, config)
            
            # 3. Fallback to global default provider
            default_provider = EmailProvider.objects.filter(
                is_global=True,
                tenant_id__isnull=True,
                activated_by_root=True,
                activated_by_tmd=True,
                is_default=True
            ).first()
            
            if default_provider:
                config = default_provider.decrypt_config()
                return EmailProviderFactory.create_provider(default_provider.provider_type, config)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting provider for tenant {self.tenant_id}: {e}")
            return None
    
    def send_email_with_fallback(self, 
                                recipient_email: str, 
                                subject: str, 
                                html_content: str, 
                                text_content: str = None,
                                sender_email: str = None,
                                headers: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Send email with automatic fallback to alternative providers"""
        from ..models.provider_models import TenantEmailProvider, EmailProvider
        
        # Get all available providers for tenant, ordered by priority
        if self.tenant_id:
            tenant_providers = TenantEmailProvider.objects.filter(
                tenant_id=self.tenant_id,
                is_enabled=True,
                provider__activated_by_root=True,
                provider__activated_by_tmd=True
            ).select_related('provider').order_by('-is_primary', 'provider__priority')
        else:
            tenant_providers = TenantEmailProvider.objects.none()
        
        last_error = {}
        
        for tenant_provider in tenant_providers:
            try:
                # Check if provider can send email
                can_send, reason = tenant_provider.can_send_email()
                if not can_send:
                    logger.warning(f"Skipping provider {tenant_provider.provider.name}: {reason}")
                    continue
                
                # Create provider instance
                provider = EmailProviderFactory.create_provider(
                    tenant_provider.provider.provider_type,
                    tenant_provider.get_effective_config()
                )
                
                # Attempt to send email
                success, message_id, response_data = provider.send_email(
                    recipient_email=recipient_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    sender_email=sender_email,
                    headers=headers
                )
                
                if success:
                    # Update usage counters
                    tenant_provider.emails_sent_today += 1
                    tenant_provider.emails_sent_this_hour += 1
                    tenant_provider.last_used_at = timezone.now()
                    tenant_provider.save()
                    
                    # Update provider usage
                    provider_obj = tenant_provider.provider
                    provider_obj.emails_sent_today += 1
                    provider_obj.emails_sent_this_hour += 1
                    provider_obj.last_used_at = timezone.now()
                    provider_obj.save()
                    
                    logger.info(f"Email sent successfully via {tenant_provider.provider.name}")
                    response_data['provider_name'] = tenant_provider.provider.name
                    response_data['provider_id'] = str(tenant_provider.provider.id)
                    response_data['provider_type'] = tenant_provider.provider.provider_type
                    if message_id and 'message_id' not in response_data:
                        response_data['message_id'] = message_id
                    return True, message_id, response_data
                
                else:
                    last_error = response_data
                    logger.warning(f"Failed to send via {tenant_provider.provider.name}: {response_data}")
                    
            except Exception as e:
                logger.error(f"Error with provider {tenant_provider.provider.name}: {e}")
                last_error = {'error_message': str(e), 'provider': tenant_provider.provider.name}
        
        # Fallback to global default provider if tenant-specific providers are unavailable or failed
        default_provider = EmailProvider.objects.filter(
            activated_by_root=True,
            activated_by_tmd=True,
            is_default=True
        ).first()
        if default_provider:
            try:
                provider_instance = EmailProviderFactory.create_provider(
                    default_provider.provider_type,
                    default_provider.decrypt_config()
                )
                success, message_id, response_data = provider_instance.send_email(
                    recipient_email=recipient_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    sender_email=sender_email,
                    headers=headers
                )

                if success:
                    default_provider.emails_sent_today += 1
                    default_provider.emails_sent_this_hour += 1
                    default_provider.last_used_at = timezone.now()
                    default_provider.save()

                    response_data['provider_name'] = default_provider.name
                    response_data['provider_id'] = str(default_provider.id)
                    response_data['provider_type'] = default_provider.provider_type
                    if message_id and 'message_id' not in response_data:
                        response_data['message_id'] = message_id
                    return True, message_id, response_data

                last_error = response_data
            except Exception as e:
                logger.error(f"Error with default provider {default_provider.name}: {e}")
                last_error = {'error_message': str(e), 'provider': default_provider.name}

        # If all providers failed
        return False, "", last_error or {'error_message': 'No available email providers'}