from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from ..models import (
    TenantEmailConfiguration, EmailProvider, TenantEmailProvider,
    EmailValidation, EmailQueue, EmailDeliveryLog, EmailAction,
    AutomationRule
)
from ..utils.tenant_service import TenantServiceAPI
from ..utils.email_providers import EmailProviderFactory
import logging

logger = logging.getLogger(__name__)


class TenantEmailConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for tenant email configuration"""
    
    tenant_name = serializers.SerializerMethodField(read_only=True)
    usage_percentage_daily = serializers.SerializerMethodField(read_only=True)
    usage_percentage_monthly = serializers.SerializerMethodField(read_only=True)
    can_send_email = serializers.SerializerMethodField(read_only=True)
    effective_from_domain = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = TenantEmailConfiguration
        fields = [
            'id', 'organization', 'plan_type', 'emails_per_day', 'emails_per_month',
            'emails_per_minute', 'custom_domain_allowed', 'advanced_analytics',
            'priority_support', 'bulk_email_allowed', 'default_from_domain',
            'custom_domain', 'custom_domain_verified', 'emails_sent_today',
            'emails_sent_this_month', 'last_email_sent_at',
            'is_suspended', 'suspension_reason', 'bounce_rate', 'complaint_rate',
            'reputation_score', 'tenant_name', 'usage_percentage_daily',
            'usage_percentage_monthly', 'can_send_email', 'effective_from_domain',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'emails_sent_today', 'emails_sent_this_month', 'last_email_sent_at',
            'last_daily_reset', 'last_monthly_reset', 'domain_verification_token',
            'bounce_rate', 'complaint_rate', 'reputation_score'
        ]
    
    def get_tenant_name(self, obj):
        """Get organization name from the related organization object"""
        try:
            if obj.organization:
                return obj.organization.name
            return 'Unknown'
        except Exception as e:
            logger.error(f"Error fetching organization name: {e}")
            return 'Unknown'
    
    def get_usage_percentage_daily(self, obj):
        """Calculate daily usage percentage"""
        if obj.emails_per_day == 0:
            return 0
        return round((obj.emails_sent_today / obj.emails_per_day) * 100, 2)
    
    def get_usage_percentage_monthly(self, obj):
        """Calculate monthly usage percentage"""
        if obj.emails_per_month == 0:
            return 0
        return round((obj.emails_sent_this_month / obj.emails_per_month) * 100, 2)
    
    def get_can_send_email(self, obj):
        """Check if tenant can send email"""
        can_send, reason = obj.can_send_email()
        return {'can_send': can_send, 'reason': reason}
    
    def get_effective_from_domain(self, obj):
        """Get effective from domain"""
        return obj.get_effective_from_domain()


class EmailProviderSerializer(serializers.ModelSerializer):
    """Serializer for email providers"""
    
    config = serializers.JSONField(write_only=True, required=False)
    auto_health_check = serializers.BooleanField(write_only=True, required=False, default=False, help_text="Set to true to automatically perform health check after creation")
    config_status = serializers.SerializerMethodField(read_only=True)
    health_info = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = EmailProvider
        fields = [
            'id', 'name', 'provider_type', 'organization', 'is_shared',
            'max_emails_per_minute', 'max_emails_per_hour', 'max_emails_per_day',
            'is_default', 'priority', 'last_health_check', 'health_status',
            'health_details', 'emails_sent_today', 'emails_sent_this_hour',
            'last_used_at', 'config', 'auto_health_check', 'config_status', 'health_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'encrypted_config', 'last_health_check', 'health_status',
            'health_details', 'emails_sent_today', 'emails_sent_this_hour',
            'last_used_at'
        ]
    
    def get_config_status(self, obj):
        """Check if configuration is valid"""
        try:
            config = obj.decrypt_config()
            provider = EmailProviderFactory.create_provider(obj.provider_type, config)
            is_valid, message = provider.validate_config(config)
            return {'is_valid': is_valid, 'message': message}
        except Exception as e:
            return {'is_valid': False, 'message': str(e)}
    
    def get_health_info(self, obj):
        """Get provider health information"""
        return {
            'status': obj.health_status,
            'details': obj.health_details,
            'last_check': obj.last_health_check
        }
    
    def create(self, validated_data):
        config = validated_data.pop('config', {})
        auto_health_check = validated_data.pop('auto_health_check', False)  # Default to False, explicit opt-in
        
        logger.info(f"Creating provider with auto_health_check={auto_health_check}, config present: {bool(config)}")
        
        instance = super().create(validated_data)
        
        if config:
            instance.encrypt_config(config)
            
            # Perform automatic health check if requested and config is valid
            if auto_health_check:
                logger.info(f"Starting auto health check for {instance.name}")
                try:
                    provider = EmailProviderFactory.create_provider(instance.provider_type, config)
                    logger.info(f"Provider instance created successfully for {instance.name}")
                    
                    is_healthy, message = provider.health_check()
                    logger.info(f"Health check completed for {instance.name}: healthy={is_healthy}")
                    
                    instance.health_status = 'HEALTHY' if is_healthy else 'UNHEALTHY'
                    instance.health_details = message
                    instance.last_health_check = timezone.now()
                    
                    logger.info(f"Auto health check for {instance.name}: {instance.health_status} - {message}")
                    
                except Exception as e:
                    logger.error(f"Auto health check failed for {instance.name}: {e}", exc_info=True)
                    instance.health_status = 'UNHEALTHY'
                    instance.health_details = f"Health check failed: {str(e)}"
                    instance.last_health_check = timezone.now()
            else:
                logger.info(f"Auto health check skipped for {instance.name} (auto_health_check={auto_health_check})")
            
            instance.save()
            logger.info(f"Provider {instance.name} saved with health_status: {instance.health_status}")
        else:
            logger.warning(f"No config provided for provider {instance.name}")
        
        return instance
    
    def update(self, instance, validated_data):
        config = validated_data.pop('config', None)
        auto_health_check = validated_data.pop('auto_health_check', False)  # Default False for updates
        
        instance = super().update(instance, validated_data)
        
        if config is not None:
            instance.encrypt_config(config)
            
            # Perform automatic health check if requested and config is updated
            if auto_health_check:
                try:
                    provider = EmailProviderFactory.create_provider(instance.provider_type, config)
                    is_healthy, message = provider.health_check()
                    
                    instance.health_status = 'HEALTHY' if is_healthy else 'UNHEALTHY'
                    instance.health_details = message
                    instance.last_health_check = timezone.now()
                    
                    logger.info(f"Auto health check for {instance.name} (update): {instance.health_status}")
                    
                except Exception as e:
                    logger.error(f"Auto health check failed for {instance.name} (update): {e}")
                    instance.health_status = 'UNHEALTHY'
                    instance.health_details = f"Health check failed: {str(e)}"
                    instance.last_health_check = timezone.now()
            
            instance.save()
        
        return instance
    
    def validate_config(self, value):
        """Validate provider configuration"""
        provider_type = self.initial_data.get('provider_type')
        if provider_type and value:
            try:
                provider = EmailProviderFactory.create_provider(provider_type, value)
                is_valid, message = provider.validate_config(value)
                if not is_valid:
                    raise serializers.ValidationError(f"Invalid configuration: {message}")
            except Exception as e:
                raise serializers.ValidationError(f"Configuration error: {str(e)}")
        return value


class TenantOwnEmailProviderSerializer(serializers.ModelSerializer):
    """Serializer for tenant-owned email providers"""
    
    config = serializers.JSONField(write_only=True, required=False)
    auto_health_check = serializers.BooleanField(write_only=True, required=False, default=False)
    config_status = serializers.SerializerMethodField(read_only=True)
    health_info = serializers.SerializerMethodField(read_only=True)
    is_tenant_owned = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = EmailProvider
        fields = [
            'id', 'tenant_id', 'name', 'provider_type', 'max_emails_per_minute',
            'max_emails_per_hour', 'max_emails_per_day', 'activated_by_root', 'activated_by_tmd',
            'is_default', 'priority', 'is_global', 'last_health_check', 'health_status',
            'health_details', 'emails_sent_today', 'emails_sent_this_hour',
            'last_used_at', 'config', 'auto_health_check', 'config_status', 'health_info',
            'is_tenant_owned', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'tenant_id', 'encrypted_config', 'last_health_check', 'health_status',
            'health_details', 'emails_sent_today', 'emails_sent_this_hour',
            'last_used_at', 'is_global', 'is_tenant_owned'
        ]
    
    def get_config_status(self, obj):
        """Check if configuration is valid"""
        try:
            config = obj.decrypt_config()
            provider = EmailProviderFactory.create_provider(obj.provider_type, config)
            is_valid, message = provider.validate_config(config)
            return {'is_valid': is_valid, 'message': message}
        except Exception as e:
            return {'is_valid': False, 'message': str(e)}
    
    def get_health_info(self, obj):
        """Get provider health information"""
        return {
            'status': obj.health_status,
            'details': obj.health_details,
            'last_check': obj.last_health_check
        }
    
    def get_is_tenant_owned(self, obj):
        """Check if this is a tenant-owned provider"""
        return obj.tenant_id is not None and not obj.is_global
    
    def create(self, validated_data):
        config = validated_data.pop('config', {})
        auto_health_check = validated_data.pop('auto_health_check', False)
        
        # Set tenant_id from context and ensure it's not global
        tenant_id = self.context.get('tenant_id')
        if not tenant_id:
            raise serializers.ValidationError("tenant_id must be provided in context")
        
        validated_data['tenant_id'] = tenant_id
        validated_data['is_global'] = False
        
        logger.info(f"Creating tenant-owned provider: {validated_data.get('name')} for tenant {tenant_id}")
        
        instance = super().create(validated_data)
        
        if config:
            instance.encrypt_config(config)
            
            if auto_health_check:
                logger.info(f"Starting auto health check for {instance.name}")
                try:
                    provider = EmailProviderFactory.create_provider(instance.provider_type, config)
                    is_healthy, message = provider.health_check()
                    
                    instance.health_status = 'HEALTHY' if is_healthy else 'UNHEALTHY'
                    instance.health_details = message
                    instance.last_health_check = timezone.now()
                    
                    logger.info(f"Auto health check for {instance.name}: {instance.health_status}")
                    
                except Exception as e:
                    logger.error(f"Auto health check failed for {instance.name}: {e}", exc_info=True)
                    instance.health_status = 'UNHEALTHY'
                    instance.health_details = f"Health check failed: {str(e)}"
                    instance.last_health_check = timezone.now()
            
            instance.save()
        
        return instance
    
    def update(self, instance, validated_data):
        config = validated_data.pop('config', None)
        auto_health_check = validated_data.pop('auto_health_check', False)
        
        # Prevent changing is_global and tenant_id after creation
        validated_data.pop('is_global', None)
        validated_data.pop('tenant_id', None)
        
        instance = super().update(instance, validated_data)
        
        if config is not None:
            instance.encrypt_config(config)
            
            if auto_health_check:
                try:
                    provider = EmailProviderFactory.create_provider(instance.provider_type, config)
                    is_healthy, message = provider.health_check()
                    
                    instance.health_status = 'HEALTHY' if is_healthy else 'UNHEALTHY'
                    instance.health_details = message
                    instance.last_health_check = timezone.now()
                    
                    logger.info(f"Auto health check for {instance.name} (update): {instance.health_status}")
                    
                except Exception as e:
                    logger.error(f"Auto health check failed for {instance.name} (update): {e}")
                    instance.health_status = 'UNHEALTHY'
                    instance.health_details = f"Health check failed: {str(e)}"
                    instance.last_health_check = timezone.now()
            
            instance.save()
        
        return instance


class TenantEmailProviderSerializer(serializers.ModelSerializer):
    """Serializer for tenant email provider configuration"""
    
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    provider_type = serializers.CharField(source='provider.provider_type', read_only=True)
    effective_config = serializers.SerializerMethodField(read_only=True)
    rate_limits = serializers.SerializerMethodField(read_only=True)
    can_send_status = serializers.SerializerMethodField(read_only=True)
    custom_config = serializers.JSONField(write_only=True, required=False)
    
    class Meta:
        model = TenantEmailProvider
        fields = [
            'id', 'organization', 'provider', 'provider_name', 'provider_type',
            'is_enabled', 'is_primary', 'custom_max_emails_per_minute',
            'custom_max_emails_per_hour', 'custom_max_emails_per_day',
            'emails_sent_today', 'emails_sent_this_hour', 'last_used_at',
            'bounce_rate', 'complaint_rate', 'delivery_rate',
            'effective_config', 'rate_limits', 'can_send_status',
            'custom_config', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'custom_encrypted_config', 'emails_sent_today', 'emails_sent_this_hour',
            'last_used_at', 'bounce_rate', 'complaint_rate', 'delivery_rate'
        ]
    
    def get_effective_config(self, obj):
        """Get effective configuration (masked for security)"""
        try:
            config = obj.get_effective_config()
            # Mask sensitive information
            masked_config = {}
            for key, value in config.items():
                if any(sensitive in key.lower() for sensitive in ['password', 'key', 'secret', 'token']):
                    masked_config[key] = '*' * 8 if value else None
                else:
                    masked_config[key] = value
            return masked_config
        except Exception as e:
            return {'error': str(e)}
    
    def get_rate_limits(self, obj):
        """Get effective rate limits"""
        return obj.get_rate_limits()
    
    def get_can_send_status(self, obj):
        """Check if can send email"""
        can_send, reason = obj.can_send_email()
        return {'can_send': can_send, 'reason': reason}
    
    def create(self, validated_data):
        custom_config = validated_data.pop('custom_config', {})
        instance = super().create(validated_data)
        
        if custom_config:
            instance.encrypt_custom_config(custom_config)
            instance.save()
        
        return instance
    
    def update(self, instance, validated_data):
        custom_config = validated_data.pop('custom_config', None)
        instance = super().update(instance, validated_data)
        
        if custom_config is not None:
            instance.encrypt_custom_config(custom_config)
            instance.save()
        
        return instance


class EmailValidationSerializer(serializers.ModelSerializer):
    """Serializer for email validation records"""
    
    class Meta:
        model = EmailValidation
        fields = [
            'id', 'email_address', 'is_valid_format', 'is_disposable',
            'is_role_based', 'domain_mx_valid', 'validation_status',
            'validation_score', 'bounce_count', 'complaint_count',
            'successful_deliveries', 'is_blacklisted', 'blacklist_reason',
            'blacklisted_at', 'last_validated_at', 'validation_provider',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'bounce_count', 'complaint_count', 'successful_deliveries',
            'last_validated_at', 'validation_score'
        ]


class EmailQueueSerializer(serializers.ModelSerializer):
    """Serializer for email queue items"""
    
    automation_rule_name = serializers.CharField(source='campaigns.automation_name', read_only=True)
    provider_name = serializers.CharField(source='assigned_provider.name', read_only=True)
    
    class Meta:
        model = EmailQueue
        fields = [
            'id', 'automation_rule', 'automation_rule_name', 'tenant_id',
            'recipient_email', 'subject', 'html_content', 'text_content',
            'context_data', 'headers', 'status', 'priority', 'scheduled_at',
            'processed_at', 'retry_count', 'max_retries', 'next_retry_at',
            'error_message', 'error_code', 'assigned_provider', 'provider_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'processed_at', 'retry_count', 'next_retry_at',
            'error_message', 'error_code', 'assigned_provider'
        ]


class EmailDeliveryLogSerializer(serializers.ModelSerializer):
    """Serializer for email delivery logs"""
    
    automation_rule_name = serializers.CharField(source='campaigns.automation_name', read_only=True)
    provider_name = serializers.CharField(source='email_provider.name', read_only=True)
    validation_status = serializers.CharField(source='email_validation.validation_status', read_only=True)
    
    class Meta:
        model = EmailDeliveryLog
        fields = [
            'id', 'queue_item', 'automation_rule', 'automation_rule_name',
            'tenant_id', 'email_validation', 'validation_status',
            'email_provider', 'provider_name', 'provider_message_id',
            'recipient_email', 'sender_email', 'subject', 'delivery_status',
            'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'bounced_at',
            'open_count', 'click_count', 'unique_click_count', 'bounce_type',
            'bounce_reason', 'spam_score', 'is_spam', 'is_duplicate',
            'duplicate_of', 'user_agent', 'ip_address', 'event_history',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'bounced_at',
            'open_count', 'click_count', 'unique_click_count', 'spam_score',
            'user_agent', 'ip_address', 'event_history'
        ]


class EmailActionSerializer(serializers.ModelSerializer):
    """Serializer for email actions"""
    
    original_recipient = serializers.CharField(source='original_log.recipient_email', read_only=True)
    performed_by_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = EmailAction
        fields = [
            'id', 'original_log', 'original_recipient', 'action_type',
            'new_recipient', 'new_delivery_log', 'reason', 'performed_by',
            'performed_by_name', 'performed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['performed_at']
    
    def get_performed_by_name(self, obj):
        """Get user name from auth service"""
        if not obj.performed_by:
            return None
        
        try:
            from core.utils.auth_service import AuthServiceAPI
            user_info = AuthServiceAPI.get_user_details(str(obj.performed_by))
            return user_info.get('full_name', 'Unknown User')
        except Exception as e:
            logger.error(f"Error fetching user name: {e}")
            return 'Unknown User'


class EnhancedAutomationRuleSerializer(serializers.ModelSerializer):
    """Enhanced serializer for automation rules with new features"""
    
    tenant_email_config_details = TenantEmailConfigurationSerializer(source='tenant_email_config', read_only=True)
    preferred_provider_details = TenantEmailProviderSerializer(source='preferred_email_provider', read_only=True)
    email_template_details = serializers.SerializerMethodField(read_only=True)
    can_trigger = serializers.SerializerMethodField(read_only=True)
    usage_stats = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = AutomationRule
        fields = [
            'id', 'automation_name', 'tenant_id', 'product_id', 'reason_name',
            'communication_type', 'trigger_type', 'action_name', 'short_description',
            'email_template_id', 'sms_template_id', 'tenant_email_config',
            'preferred_email_provider', 'delay_amount', 'delay_unit',
            'schedule_frequency', 'schedule_interval_amount', 'schedule_interval_unit',
            'schedule_time', 'schedule_day_of_week', 'schedule_day_of_month',
            'max_retries', 'retry_delay_minutes', 'batch_size', 'filter_conditions',
            'activated_by_root', 'activated_by_tmd', 'priority', 'tenant_email_config_details',
            'preferred_provider_details', 'email_template_details', 'can_trigger',
            'usage_stats', 'created_at', 'updated_at'
        ]
        read_only_fields = ['periodic_task']
    
    def get_email_template_details(self, obj):
        """Get email template details"""
        if obj.email_template_id:
            try:
                from .base_serializers import EmailTemplateSerializer  # Avoid circular import
                return EmailTemplateSerializer(obj.email_template_id).data
            except Exception:
                pass
        return None
    
    def get_can_trigger(self, obj):
        """Check if rule can be triggered"""
        try:
            config = obj.get_effective_config()
            can_send, reason = config.can_send_email()
            return {'can_trigger': can_send, 'reason': reason}
        except Exception as e:
            return {'can_trigger': False, 'reason': str(e)}
    
    def get_usage_stats(self, obj):
        """Get usage statistics for this rule"""
        try:
            from django.db.models import Count, Q
            from django.utils import timezone
            from datetime import timedelta
            
            now = timezone.now()
            last_30_days = now - timedelta(days=30)
            
            stats = EmailDeliveryLog.objects.filter(
                automation_rule=obj,
                sent_at__gte=last_30_days
            ).aggregate(
                total_sent=Count('id'),
                delivered=Count('id', filter=Q(delivery_status='DELIVERED')),
                bounced=Count('id', filter=Q(delivery_status='BOUNCED')),
                opened=Count('id', filter=Q(delivery_status='OPENED')),
                clicked=Count('id', filter=Q(delivery_status='CLICKED'))
            )
            
            return stats
        except Exception as e:
            logger.error(f"Error calculating usage stats: {e}")
            return {}
    
    def validate(self, data):
        """Enhanced validation for automation rules"""
        # Call parent validation
        data = super().validate(data) if hasattr(super(), 'validate') else data
        
        # Validate tenant exists and is active (lenient for service unavailability)
        tenant_id = data.get('tenant_id')
        if tenant_id:
            try:
                tenant_active = TenantServiceAPI.is_tenant_active(str(tenant_id))
                # Only fail if tenant is explicitly inactive (False)
                # If None (service unavailable), allow it to proceed
                if tenant_active is False:
                    raise serializers.ValidationError("Tenant is inactive or not found")
                elif tenant_active is None:
                    logger.warning(f"Tenant service unavailable for {tenant_id}, allowing creation to proceed")
            except serializers.ValidationError:
                # Re-raise validation errors
                raise
            except Exception as e:
                # For other errors, log and allow
                logger.warning(f"Error validating tenant {tenant_id}: {e}. Allowing creation to proceed.")
        
        # Validate trigger configuration
        trigger_type = data.get('trigger_type')
        
        if trigger_type == AutomationRule.TriggerType.DELAY:
            if not data.get('delay_amount') or not data.get('delay_unit'):
                raise serializers.ValidationError("Delay amount and unit are required for DELAY trigger type")
        
        elif trigger_type == AutomationRule.TriggerType.SCHEDULE:
            if not data.get('schedule_frequency'):
                raise serializers.ValidationError("Schedule frequency is required for SCHEDULE trigger type")
            
            frequency = data.get('schedule_frequency')
            if frequency == AutomationRule.ScheduleFrequency.INTERVAL:
                if not data.get('schedule_interval_amount') or not data.get('schedule_interval_unit'):
                    raise serializers.ValidationError("Interval amount and unit are required for INTERVAL frequency")
            else:
                if not data.get('schedule_time'):
                    raise serializers.ValidationError("Schedule time is required for DAILY/WEEKLY/MONTHLY frequency")
                
                if frequency == AutomationRule.ScheduleFrequency.WEEKLY and not data.get('schedule_day_of_week'):
                    raise serializers.ValidationError("Day of week is required for WEEKLY frequency")
                
                if frequency == AutomationRule.ScheduleFrequency.MONTHLY and not data.get('schedule_day_of_month'):
                    raise serializers.ValidationError("Day of month is required for MONTHLY frequency")
        
        # Validate communication type specific requirements
        communication_type = data.get('communication_type')
        if communication_type == AutomationRule.CommunicationType.EMAIL:
            if not data.get('email_template_id'):
                raise serializers.ValidationError("Email template is required for EMAIL communication type")
        elif communication_type == AutomationRule.CommunicationType.SMS:
            if not data.get('sms_template_id'):
                raise serializers.ValidationError("SMS template is required for SMS communication type")
        
        return data


class TriggerEmailEnhancedSerializer(serializers.Serializer):
    """Enhanced serializer for triggering emails with new features"""
    
    # Rule identification (one of these is required)
    automation_name = serializers.CharField(max_length=255, required=False)
    rule_id = serializers.UUIDField(required=False)
    reason_name = serializers.ChoiceField(choices=AutomationRule.ReasonName.choices, required=False)
    
    # Tenant and product context
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    product_id = serializers.UUIDField(required=False, allow_null=True)
    
    # Email content and recipients
    email_variables = serializers.JSONField(required=True)
    recipient_emails = serializers.ListField(child=serializers.EmailField(), required=True)
    
    # Optional overrides
    email_template_id = serializers.UUIDField(required=False, allow_null=True)
    preferred_provider_id = serializers.UUIDField(required=False, allow_null=True)
    priority = serializers.IntegerField(min_value=1, max_value=10, required=False)
    
    # Scheduling options
    schedule_at = serializers.DateTimeField(required=False, allow_null=True)
    
    # Advanced options
    skip_validation = serializers.BooleanField(default=False)
    track_opens = serializers.BooleanField(default=True)
    track_clicks = serializers.BooleanField(default=True)
    
    def validate(self, attrs):
        """Validate trigger email request"""
        # Ensure at least one rule identification method is provided
        identifiers = [attrs.get('rule_id'), attrs.get('automation_name'), attrs.get('reason_name')]
        if not any(identifiers):
            raise serializers.ValidationError("Provide rule_id, automation_name, or reason_name")
        
        # Validate tenant if provided
        tenant_id = attrs.get('tenant_id')
        if tenant_id:
            try:
                if not TenantServiceAPI.is_tenant_active(str(tenant_id)):
                    raise serializers.ValidationError("Tenant is inactive")
            except Exception as e:
                raise serializers.ValidationError(f"Error validating tenant: {str(e)}")
        
        # Validate recipient limit based on tenant plan
        recipient_count = len(attrs.get('recipient_emails', []))
        if recipient_count > 1000:  # Basic limit, can be made tenant-specific
            raise serializers.ValidationError("Too many recipients in single request")
        
        return attrs