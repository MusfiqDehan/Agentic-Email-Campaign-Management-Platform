from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using Django's send_mail function."""
    
    def send_verification_email(self, to_email: str, token: str):
        """
        Send email verification link to user.
        
        Args:
            to_email: Recipient email address
            token: Verification token UUID
        """
        subject = 'Verify Your Email Address'
        
        # Construct verification URL (update domain as needed)
        verification_url = f"http://localhost:3000/verify-email?token={token}"
        
        message = f"""
        Welcome to Email Campaign Management Platform!
        
        Please verify your email address by clicking the link below:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        
        Best regards,
        Email Campaign Management Team
        """
        
        html_message = f"""
        <html>
            <body>
                <h2>Welcome to Email Campaign Management Platform!</h2>
                <p>Please verify your email address by clicking the button below:</p>
                <p>
                    <a href="{verification_url}" 
                       style="background-color: #4CAF50; color: white; padding: 14px 20px; 
                              text-align: center; text-decoration: none; display: inline-block; 
                              border-radius: 4px;">
                        Verify Email Address
                    </a>
                </p>
                <p>Or copy and paste this link in your browser:</p>
                <p><a href="{verification_url}">{verification_url}</a></p>
                <p><small>This link will expire in 24 hours.</small></p>
                <hr>
                <p><small>If you didn't create an account, please ignore this email.</small></p>
            </body>
        </html>
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Verification email sent successfully to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {to_email}: {str(e)}")
            raise

    def send_password_reset_email(self, to_email: str, token: str):
        """
        Send password reset link to user.
        
        Args:
            to_email: Recipient email address
            token: Password reset token UUID
        """
        subject = 'Reset Your Password'
        
        # Construct reset URL (update domain as needed)
        reset_url = f"http://localhost:3000/reset-password?token={token}"
        
        message = f"""
        Password Reset Request
        
        We received a request to reset your password. Click the link below to reset it:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email or contact support if you have concerns.
        
        Best regards,
        Email Campaign Management Team
        """
        
        html_message = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your password.</p>
                <p>Click the button below to reset your password:</p>
                <p>
                    <a href="{reset_url}" 
                       style="background-color: #2196F3; color: white; padding: 14px 20px; 
                              text-align: center; text-decoration: none; display: inline-block; 
                              border-radius: 4px;">
                        Reset Password
                    </a>
                </p>
                <p>Or copy and paste this link in your browser:</p>
                <p><a href="{reset_url}">{reset_url}</a></p>
                <p><small>This link will expire in 1 hour.</small></p>
                <hr>
                <p><small>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</small></p>
            </body>
        </html>
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Password reset email sent successfully to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
            raise