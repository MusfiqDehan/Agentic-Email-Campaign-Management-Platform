import uuid
import json
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from utils.base_models import BaseModel
from authentication.models import Organization


class EmailProvider(BaseModel):
    """Abstract email provider configuration for different email services"""
    
    PROVIDER_TYPES = [
        ('AWS_SES', 'Amazon SES'),
        ('SENDGRID', 'SendGrid'),
        ('BREVO', 'Brevo (formerly Sendinblue)'),
        ('SMTP', 'Custom SMTP'),
        ('INTERNAL', 'Internal System'),
    ]
    
    HEALTH_STATUS_CHOICES = [
        ('HEALTHY', 'Healthy'),
        ('DEGRADED', 'Degraded'),
        ('UNHEALTHY', 'Unhealthy'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    
    org_id = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='organizations')
    is_global = models.BooleanField(
        default=True,
        help_text="Whether this is a global provider (accessible by all tenants)"
    )
    
    # Provider configuration (encrypted JSON)
    encrypted_config = models.TextField(help_text="Encrypted provider-specific configuration")
    
    # Rate limiting per provider
    max_emails_per_minute = models.PositiveIntegerField(default=100)
    max_emails_per_hour = models.PositiveIntegerField(default=1000)
    max_emails_per_day = models.PositiveIntegerField(default=10000)
    
    # Provider status
    is_default = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(default=1, help_text="Lower number = higher priority")
    
    # Health monitoring
    last_health_check = models.DateTimeField(null=True, blank=True)
    health_status = models.CharField(
        max_length=20, 
        choices=HEALTH_STATUS_CHOICES,
        default='UNKNOWN'
    )
    health_details = models.TextField(blank=True)
    
    # Usage tracking
    emails_sent_today = models.PositiveIntegerField(default=0)
    emails_sent_this_hour = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one provider is default per scope (tenant-owned or global)
            if self.tenant_id:
                # For tenant-owned providers: unset default ONLY for same tenant
                EmailProvider.objects.filter(
                    tenant_id=self.tenant_id,
                    is_default=True
                ).exclude(pk=self.pk).update(is_default=False)
            else:
                # For global providers: unset default ONLY for global providers
                EmailProvider.objects.filter(
                    tenant_id__isnull=True,
                    is_default=True
                ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    def encrypt_config(self, config_dict):
        """Encrypt configuration dictionary"""
        try:
            from ..utils.crypto import encrypt_data
            config_json = json.dumps(config_dict)
            self.encrypted_config = encrypt_data(config_json)
        except Exception as e:
            raise ValidationError(f"Failed to encrypt configuration: {str(e)}")
    
    def decrypt_config(self):
        """Decrypt configuration dictionary"""
        try:
            if not self.encrypted_config:
                return {}
            from ..utils.crypto import decrypt_data
            decrypted_json = decrypt_data(self.encrypted_config)
            return json.loads(decrypted_json)
        except Exception as e:
            raise ValidationError(f"Failed to decrypt configuration: {str(e)}")
    
    def can_send_email(self):
        """Check if provider can send email based on rate limits and health"""
        if not self.activated_by_root or not self.activated_by_tmd:
            return False, "Provider is not activated"
        
        if self.health_status == 'UNHEALTHY':
            return False, "Provider is unhealthy"
        
        if self.emails_sent_today >= self.max_emails_per_day:
            return False, "Daily email limit exceeded"
        
        if self.emails_sent_this_hour >= self.max_emails_per_hour:
            return False, "Hourly email limit exceeded"
        
        return True, "OK"
    
    class Meta:
        ordering = ['priority', 'name']
        unique_together = [
            ['name', 'tenant_id'],  # Name unique per tenant (or globally if tenant_id is NULL)
        ]
        indexes = [
            models.Index(fields=['tenant_id', 'is_global']),
            models.Index(fields=['is_global', 'is_default']),
        ]
        verbose_name = "Email Provider"
        verbose_name_plural = "Email Providers"
    
    def __str__(self):
        scope = f" (Tenant: {self.tenant_id})" if self.tenant_id else " (Global)"
        return f"{self.name} ({self.provider_type}){scope}"


class TenantEmailProvider(BaseModel):
    """Tenant-specific email provider configuration and overrides"""
    
    tenant_id = models.UUIDField(db_index=True, help_text="Reference to tenant from tenant microservice")
    provider = models.ForeignKey(EmailProvider, on_delete=models.CASCADE, related_name='tenant_configs')
    
    # Tenant-specific settings
    is_enabled = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False, help_text="Primary provider for this tenant")
    
    # Custom configuration overrides (encrypted)
    custom_encrypted_config = models.TextField(blank=True, help_text="Tenant-specific config overrides")
    
    # Tenant-specific rate limits (override provider defaults)
    custom_max_emails_per_minute = models.PositiveIntegerField(null=True, blank=True)
    custom_max_emails_per_hour = models.PositiveIntegerField(null=True, blank=True)
    custom_max_emails_per_day = models.PositiveIntegerField(null=True, blank=True)
    
    # Usage tracking for this tenant-provider combination
    emails_sent_today = models.PositiveIntegerField(default=0)
    emails_sent_this_hour = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    # Reputation tracking
    bounce_rate = models.FloatField(default=0.0)
    complaint_rate = models.FloatField(default=0.0)
    delivery_rate = models.FloatField(default=100.0)
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one provider is primary per tenant
            TenantEmailProvider.objects.filter(
                tenant_id=self.tenant_id, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
    
    def encrypt_custom_config(self, config_dict):
        """Encrypt tenant-specific configuration dictionary"""
        try:
            if not config_dict:
                self.custom_encrypted_config = ""
                return
            
            from ..utils.crypto import encrypt_data
            config_json = json.dumps(config_dict)
            self.custom_encrypted_config = encrypt_data(config_json)
        except Exception as e:
            raise ValidationError(f"Failed to encrypt custom configuration: {str(e)}")
    
    def decrypt_custom_config(self):
        """Decrypt tenant-specific configuration dictionary"""
        try:
            if not self.custom_encrypted_config:
                return {}
            from ..utils.crypto import decrypt_data
            decrypted_json = decrypt_data(self.custom_encrypted_config)
            return json.loads(decrypted_json)
        except Exception as e:
            raise ValidationError(f"Failed to decrypt custom configuration: {str(e)}")
    
    def get_effective_config(self):
        """Get merged configuration (provider + tenant overrides)"""
        base_config = self.provider.decrypt_config()
        custom_config = self.decrypt_custom_config()
        
        # Merge configurations, with custom config taking precedence
        effective_config = {**base_config, **custom_config}
        return effective_config
    
    def get_rate_limits(self):
        """Get effective rate limits for this tenant-provider combination"""
        return {
            'emails_per_minute': self.custom_max_emails_per_minute or self.provider.max_emails_per_minute,
            'emails_per_hour': self.custom_max_emails_per_hour or self.provider.max_emails_per_hour,
            'emails_per_day': self.custom_max_emails_per_day or self.provider.max_emails_per_day,
        }
    
    def can_send_email(self):
        """Check if this tenant can send email via this provider"""
        if not self.is_enabled or not self.provider.activated_by_root or not self.provider.activated_by_tmd:
            return False, "Provider is disabled or not activated"
        
        limits = self.get_rate_limits()
        
        if self.emails_sent_today >= limits['emails_per_day']:
            return False, "Daily email limit exceeded for this provider"
        
        if self.emails_sent_this_hour >= limits['emails_per_hour']:
            return False, "Hourly email limit exceeded for this provider"
        
        # Check provider-level limits as well
        provider_can_send, provider_message = self.provider.can_send_email()
        if not provider_can_send:
            return False, f"Provider limitation: {provider_message}"
        
        return True, "OK"
    
    class Meta:
        unique_together = ['tenant_id', 'provider']
        indexes = [
            models.Index(fields=['tenant_id', 'is_enabled']),
            models.Index(fields=['tenant_id', 'is_primary']),
        ]
        verbose_name = "Tenant Email Provider"
        verbose_name_plural = "Tenant Email Providers"
    
    def __str__(self):
        return f"Tenant {self.tenant_id} - {self.provider.name}"