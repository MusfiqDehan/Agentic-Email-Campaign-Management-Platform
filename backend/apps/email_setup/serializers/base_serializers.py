from rest_framework import serializers
from ..models import (
    EmailTemplate, AutomationRule, SMSConfigurationModel, 
    SMSTemplate, TenantEmailConfiguration, EmailProvider, EmailDeliveryLog
)
from ..utils import encrypt_data
from ..utils.tenant_service import TenantServiceAPI
import logging

logger = logging.getLogger(__name__)


class EmailTemplateSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    template_type = serializers.ChoiceField(
        choices=EmailTemplate.TemplateType.choices,
        required=False,
        default=EmailTemplate.TemplateType.TENANT
    )
    category = serializers.ChoiceField(
        choices=EmailTemplate.TemplateCategory.choices,
        required=False,
        default=EmailTemplate.TemplateCategory.OTHER
    )

    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'template_name', 'tenant_id', 'template_type', 'category', 'email_subject',
            'email_body', 'recipient_emails_list', 'activated_by_tmd', 'activated_by_td', 'activated_by_root', 'updated_at'
        ]
        read_only_fields = ('id', 'updated_at')

    def validate(self, data):
        """Validate and auto-adjust template_type consistency with tenant_id"""
        template_type = data.get('template_type')
        tenant_id = data.get('tenant_id')
        
        # Auto-detect template type based on tenant_id if not explicitly set
        if template_type is None:
            if tenant_id is None:
                template_type = EmailTemplate.TemplateType.GLOBAL
                data['template_type'] = template_type
            else:
                template_type = EmailTemplate.TemplateType.TENANT
                data['template_type'] = template_type
        
        # Validate consistency after auto-detection
        if template_type == EmailTemplate.TemplateType.GLOBAL and tenant_id is not None:
            raise serializers.ValidationError({
                'template_type': 'Global templates cannot have a tenant_id. Set tenant_id to null for global templates.'
            })
        if template_type == EmailTemplate.TemplateType.TENANT and tenant_id is None:
            raise serializers.ValidationError({
                'tenant_id': 'Tenant-specific templates must have a tenant_id. Provide tenant_id or set template_type to GLOBAL.'
            })
            
        return data


class AutomationRuleSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    product_id = serializers.UUIDField(required=False, allow_null=True)
    rule_scope = serializers.ChoiceField(
        choices=AutomationRule.RuleScope.choices, 
        required=False, 
        default=AutomationRule.RuleScope.TENANT
    )

    class Meta:
        model = AutomationRule
        fields = [
            'id', 'automation_name', 'tenant_id', 'product_id', 'rule_scope', 'reason_name', 'trigger_type', 'schedule_frequency',
            'communication_type', 'short_description', 'email_template_id', 'sms_template_id',
            'sms_config_id', 'delay_amount', 'delay_unit',
            'schedule_interval_amount', 'schedule_interval_unit', 'schedule_time',
            'schedule_day_of_week', 'schedule_day_of_month', 'activated_by_tmd', 'activated_by_td', 'activated_by_root', 'updated_at'
        ]
        read_only_fields = ('id', 'periodic_task', 'updated_at')

    def validate(self, data):
        """
        Add custom validation based on the trigger_type and schedule_frequency,
        rule_scope validation, and for unique_together with nullable fields.
        """
        # Validate and auto-adjust rule_scope consistency
        rule_scope = data.get('rule_scope')
        tenant_id = data.get('tenant_id')
        
        # Auto-detect rule scope based on tenant_id if not explicitly set
        if rule_scope is None:
            if tenant_id is None:
                rule_scope = AutomationRule.RuleScope.GLOBAL
                data['rule_scope'] = rule_scope
            else:
                rule_scope = AutomationRule.RuleScope.TENANT
                data['rule_scope'] = rule_scope
        
        # Validate consistency after auto-detection
        if rule_scope == AutomationRule.RuleScope.GLOBAL and tenant_id is not None:
            raise serializers.ValidationError({
                'rule_scope': 'Global rules cannot have a tenant_id. Set tenant_id to null for global rules.'
            })
        if rule_scope == AutomationRule.RuleScope.TENANT and tenant_id is None:
            raise serializers.ValidationError({
                'tenant_id': 'Tenant-specific rules must have a tenant_id. Provide tenant_id or set rule_scope to GLOBAL.'
            })

        # Existing trigger type validation
        trigger_type = data.get('trigger_type')

        if trigger_type == AutomationRule.TriggerType.DELAY:
            if not data.get('delay_amount') or not data.get('delay_unit'):
                raise serializers.ValidationError("For a 'DELAY' trigger, 'delay_amount' and 'delay_unit' are required.")

        elif trigger_type == AutomationRule.TriggerType.SCHEDULE:
            frequency = data.get('schedule_frequency')
            if not frequency:
                raise serializers.ValidationError("For a 'SCHEDULE' trigger, 'schedule_frequency' is required.")
            
            if frequency == AutomationRule.ScheduleFrequency.INTERVAL:
                if not data.get('schedule_interval_amount') or not data.get('schedule_interval_unit'):
                    raise serializers.ValidationError("For 'INTERVAL' frequency, 'schedule_interval_amount' and 'schedule_interval_unit' are required.")
            else: # DAILY, WEEKLY, MONTHLY
                if not data.get('schedule_time'):
                    raise serializers.ValidationError("For 'DAILY', 'WEEKLY', or 'MONTHLY' frequency, 'schedule_time' is required.")
                if frequency == AutomationRule.ScheduleFrequency.WEEKLY and not data.get('schedule_day_of_week'):
                    raise serializers.ValidationError("For 'WEEKLY' frequency, 'schedule_day_of_week' is required.")
                if frequency == AutomationRule.ScheduleFrequency.MONTHLY and not data.get('schedule_day_of_month'):
                    raise serializers.ValidationError("For 'MONTHLY' frequency, 'schedule_day_of_month' is required.")

        # Custom unique_together validation with rule_scope consideration
        # Note: Database constraint validation will be handled by the database itself
        # This is just for additional validation during API usage
            
        return data


class TriggerEmailSerializer(serializers.Serializer):
    """
    Serializer for validating the trigger email request.
    """
    automation_name = serializers.CharField(max_length=255, required=False)
    rule_id = serializers.UUIDField(required=False)
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    product_id = serializers.UUIDField(required=False, allow_null=True)
    email_template_id = serializers.UUIDField(required=False, allow_null=True)
    reason_name = serializers.ChoiceField(choices=AutomationRule.ReasonName.choices)
    email_variables = serializers.JSONField()
    recipient_emails = serializers.ListField(
        child=serializers.EmailField()
    )

    def validate(self, attrs):
        # Allow direct rule targeting OR reason-based lookup
        if not attrs.get('rule_id') and not attrs.get('automation_name') and not attrs.get('reason_name'):
            raise serializers.ValidationError("Provide rule_id, automation_name, or reason_name.")
        return attrs


class GlobalEmailTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for global email templates.
    Tenant_id is not required and will be automatically set to null for global templates.
    """
    tenant_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    template_type = serializers.ChoiceField(
        choices=EmailTemplate.TemplateType.choices,
        required=False,
        default=EmailTemplate.TemplateType.GLOBAL
    )
    category = serializers.ChoiceField(
        choices=EmailTemplate.TemplateCategory.choices,
        required=False,
        default=EmailTemplate.TemplateCategory.OTHER
    )

    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'template_name', 'tenant_id', 'template_type', 'category', 'email_subject',
            'email_body', 'recipient_emails_list', 'activated_by_tmd', 'activated_by_td', 'activated_by_root', 'updated_at'
        ]
        read_only_fields = ('id', 'updated_at')
    def validate(self, data):
        """Validate and auto-adjust for global templates"""
        # Force global template settings
        data['template_type'] = EmailTemplate.TemplateType.GLOBAL
        data['tenant_id'] = None
        
        return data


class GlobalAutomationRuleSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for global automation rules.
    Tenant_id is not required and will be automatically set to null for global rules.
    Product_id is optional for global rules.
    """
    tenant_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    product_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    rule_scope = serializers.ChoiceField(
        choices=AutomationRule.RuleScope.choices,
        required=False,
        default=AutomationRule.RuleScope.GLOBAL
    )

    class Meta:
        model = AutomationRule
        fields = [
            'id', 'automation_name', 'tenant_id', 'product_id', 'rule_scope', 'reason_name', 'trigger_type', 'schedule_frequency',
            'communication_type', 'short_description', 'email_template_id', 'sms_template_id', 'sms_config_id', 'delay_amount', 'delay_unit',
            'schedule_interval_amount', 'schedule_interval_unit', 'schedule_time', 'schedule_day_of_week', 'schedule_day_of_month', 
            'activated_by_tmd', 'activated_by_td', 'activated_by_root', 'updated_at'
        ]
        read_only_fields = ('id', 'periodic_task', 'updated_at')

    def validate(self, data):
        """Validate and auto-adjust for global rules"""
        # Force global rule settings
        data['rule_scope'] = AutomationRule.RuleScope.GLOBAL
        data['tenant_id'] = None
        
        # Set product_id to None if not provided (allows null for global rules)
        if 'product_id' not in data or data.get('product_id') is None:
            data['product_id'] = None

        # Existing trigger type validation from parent class
        trigger_type = data.get('trigger_type')

        if trigger_type == AutomationRule.TriggerType.DELAY:
            if not data.get('delay_amount') or not data.get('delay_unit'):
                raise serializers.ValidationError("For a 'DELAY' trigger, 'delay_amount' and 'delay_unit' are required.")

        elif trigger_type == AutomationRule.TriggerType.SCHEDULE:
            frequency = data.get('schedule_frequency')
            if not frequency:
                raise serializers.ValidationError("For a 'SCHEDULE' trigger, 'schedule_frequency' is required.")
            
            if frequency == AutomationRule.ScheduleFrequency.INTERVAL:
                if not data.get('schedule_interval_amount') or not data.get('schedule_interval_unit'):
                    raise serializers.ValidationError("For 'INTERVAL' frequency, 'schedule_interval_amount' and 'schedule_interval_unit' are required.")
            else: # DAILY, WEEKLY, MONTHLY
                if not data.get('schedule_time'):
                    raise serializers.ValidationError("For 'DAILY', 'WEEKLY', or 'MONTHLY' frequency, 'schedule_time' is required.")
                if frequency == AutomationRule.ScheduleFrequency.WEEKLY and not data.get('schedule_day_of_week'):
                    raise serializers.ValidationError("For 'WEEKLY' frequency, 'schedule_day_of_week' is required.")
                if frequency == AutomationRule.ScheduleFrequency.MONTHLY and not data.get('schedule_day_of_month'):
                    raise serializers.ValidationError("For 'MONTHLY' frequency, 'schedule_day_of_month' is required.")

        return data


class GlobalTriggerEmailSerializer(serializers.Serializer):
    """
    Serializer specifically for triggering global email automation.
    Tenant_id is not required and will be ignored for global rules.
    """
    automation_name = serializers.CharField(max_length=255, required=False)
    rule_id = serializers.UUIDField(required=False)
    product_id = serializers.UUIDField(required=False, allow_null=True)
    email_template_id = serializers.UUIDField(required=False, allow_null=True)
    reason_name = serializers.ChoiceField(choices=AutomationRule.ReasonName.choices)
    email_variables = serializers.JSONField()
    recipient_emails = serializers.ListField(
        child=serializers.EmailField()
    )

    def validate(self, attrs):
        # Allow direct rule targeting OR reason-based lookup for global rules
        if not attrs.get('rule_id') and not attrs.get('automation_name') and not attrs.get('reason_name'):
            raise serializers.ValidationError("Provide rule_id, automation_name, or reason_name.")
        return attrs


class SMSConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for SMS configuration settings (Twilio integration).
    """
    class Meta:
        model = SMSConfigurationModel
        fields = [
            'id', 'name_or_type', 'tenant_id', 'endpoint_url', 'account_ssid',
            'auth_token', 'verified_service_id', 'default_from_number',
            'whatsapp_from_number', 'whatsapp_enabled', 'activated_by_tmd', 'activated_by_td',
            'updated_at'
        ]
        extra_kwargs = {
            'auth_token': {'write_only': True, 'style': {'input_type': 'password'}}
        }

    def create(self, validated_data):
        token = validated_data.get('auth_token')
        if token:
            validated_data['auth_token'] = encrypt_data(token)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        token = validated_data.get('auth_token')
        if token:
            validated_data['auth_token'] = encrypt_data(token)
        return super().update(instance, validated_data)


class SMSTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for SMS templates with dynamic variables.
    """
    class Meta:
        model = SMSTemplate
        fields = ['id', 'template_name', 'sms_body', 'recipient_numbers_list',
                  'activated_by_tmd', 'activated_by_td', 'updated_at']


class TriggerSMSSerializer(serializers.Serializer):
    """
    Serializer for validating the trigger SMS request.
    """
    reason_name = serializers.CharField(max_length=255, required=False)
    rule_id = serializers.UUIDField(required=False)
    sms_variables = serializers.JSONField(required=False)
    recipient_numbers = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    product_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        """
        Validate that either reason_name or rule_id is provided.
        """
        if not attrs.get('reason_name') and not attrs.get('rule_id'):
            raise serializers.ValidationError("Either 'reason_name' or 'rule_id' must be provided.")
        return attrs

# Enhanced serializers for new functionality
class TenantEmailConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for tenant email configuration"""
    
    tenant_name = serializers.SerializerMethodField(read_only=True)
    usage_percentage_daily = serializers.SerializerMethodField(read_only=True)
    usage_percentage_monthly = serializers.SerializerMethodField(read_only=True)
    can_send_email_status = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = TenantEmailConfiguration
        fields = [
            'id', 'tenant_id', 'plan_type', 'emails_per_day', 'emails_per_month',
            'emails_per_minute', 'custom_domain_allowed', 'advanced_analytics',
            'priority_support', 'bulk_email_allowed', 'default_from_domain',
            'custom_domain', 'custom_domain_verified', 'emails_sent_today',
            'emails_sent_this_month', 'last_email_sent_at', 'activated_by_root', 'activated_by_tmd',
            'is_suspended', 'suspension_reason', 'bounce_rate', 'complaint_rate',
            'reputation_score', 'tenant_name', 'usage_percentage_daily',
            'usage_percentage_monthly', 'can_send_email_status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'emails_sent_today', 'emails_sent_this_month', 'last_email_sent_at',
            'bounce_rate', 'complaint_rate', 'reputation_score'
        ]
    
    def get_tenant_name(self, obj):
        try:
            tenant_info = TenantServiceAPI.get_tenant_details(str(obj.tenant_id))
            return tenant_info.get('name', 'Unknown')
        except Exception as e:
            logger.error(f"Error fetching tenant name: {e}")
            return 'Unknown'
    
    def get_usage_percentage_daily(self, obj):
        if obj.emails_per_day == 0:
            return 0
        return round((obj.emails_sent_today / obj.emails_per_day) * 100, 2)
    
    def get_usage_percentage_monthly(self, obj):
        if obj.emails_per_month == 0:
            return 0
        return round((obj.emails_sent_this_month / obj.emails_per_month) * 100, 2)
    
    def get_can_send_email_status(self, obj):
        can_send, reason = obj.can_send_email()
        return {'can_send': can_send, 'reason': reason}


class EmailProviderSerializer(serializers.ModelSerializer):
    """Serializer for email providers"""
    
    config = serializers.JSONField(write_only=True, required=False)
    config_status = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = EmailProvider
        fields = [
            'id', 'name', 'provider_type', 'max_emails_per_minute',
            'max_emails_per_hour', 'max_emails_per_day', 'activated_by_root', 
            'activated_by_tmd', 'activated_by_td',
            'is_default', 'priority', 'health_status', 'config', 'config_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['encrypted_config', 'health_status', 'last_health_check']
    
    def get_config_status(self, obj):
        try:
            from ..utils.email_providers import EmailProviderFactory
            config = obj.decrypt_config()
            provider = EmailProviderFactory.create_provider(obj.provider_type, config)
            is_valid, message = provider.validate_config(config)
            return {'is_valid': is_valid, 'message': message}
        except Exception as e:
            return {'is_valid': False, 'message': str(e)}
    
    def create(self, validated_data):
        config = validated_data.pop('config', {})
        instance = super().create(validated_data)
        if config:
            instance.encrypt_config(config)
            instance.save()
        return instance
    
    def update(self, instance, validated_data):
        config = validated_data.pop('config', None)
        instance = super().update(instance, validated_data)
        if config is not None:
            instance.encrypt_config(config)
            instance.save()
        return instance


class EnhancedEmailDeliveryLogSerializer(serializers.ModelSerializer):
    """Enhanced serializer for email delivery logs"""
    
    automation_rule_name = serializers.CharField(source='automation_rule.automation_name', read_only=True)
    provider_name = serializers.CharField(source='email_provider.name', read_only=True)
    email_template_id = serializers.UUIDField(source='email_template.id', allow_null=True, read_only=True)
    queue_item_id = serializers.UUIDField(source='queue_item.id', allow_null=True, read_only=True)
    log_source = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailDeliveryLog
        fields = [
            'id', 'automation_rule', 'automation_rule_name', 'tenant_id', 'product_id',
            'reason_name', 'trigger_type', 'log_scope', 'recipient_email', 'sender_email',
            'subject', 'delivery_status', 'planned_delivery_at', 'queue_item_id', 'log_source',
            'email_template_id', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at',
            'bounced_at', 'open_count', 'click_count', 'unique_click_count', 'bounce_type',
            'bounce_reason', 'error_message', 'spam_score', 'is_spam', 'is_duplicate',
            'email_provider', 'provider_name', 'provider_message_id', 'user_agent',
            'ip_address', 'event_history', 'context_data', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'bounced_at',
            'open_count', 'click_count', 'unique_click_count', 'spam_score',
            'user_agent', 'ip_address', 'event_history', 'context_data'
        ]

    def get_log_source(self, obj):
        return 'EmailDeliveryLog'


class EnhancedTriggerEmailSerializer(serializers.Serializer):
    """Enhanced serializer for triggering emails with provider support"""
    
    # Rule identification (one required)
    automation_name = serializers.CharField(max_length=255, required=False)
    rule_id = serializers.UUIDField(required=False)
    reason_name = serializers.ChoiceField(choices=AutomationRule.ReasonName.choices, required=False)
    
    # Context
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    product_id = serializers.UUIDField(required=False, allow_null=True)
    
    # Content
    email_variables = serializers.JSONField(required=True)
    recipient_emails = serializers.ListField(child=serializers.EmailField(), required=True)
    
    # Overrides
    email_template_id = serializers.UUIDField(required=False, allow_null=True)
    preferred_provider_id = serializers.UUIDField(required=False, allow_null=True)
    priority = serializers.IntegerField(min_value=1, max_value=10, required=False)
    
    # Options
    schedule_at = serializers.DateTimeField(required=False, allow_null=True)
    skip_validation = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        # Ensure at least one rule identification method
        identifiers = [attrs.get('rule_id'), attrs.get('automation_name'), attrs.get('reason_name')]
        if not any(identifiers):
            raise serializers.ValidationError("Provide rule_id, automation_name, or reason_name")
        
        # Validate tenant if provided (lenient - only fail if explicitly inactive, not on connection errors)
        tenant_id = attrs.get('tenant_id')
        if tenant_id:
            try:
                tenant_active = TenantServiceAPI.is_tenant_active(str(tenant_id))
                # Only raise error if we got a definitive "inactive" response
                # If service is unavailable (returns None), allow it to proceed
                if tenant_active is False:
                    raise serializers.ValidationError("Tenant is inactive")
                elif tenant_active is None:
                    # Service unavailable - log warning but allow
                    logger.warning(f"Tenant service unavailable for {tenant_id}, allowing request to proceed")
            except serializers.ValidationError:
                # Re-raise validation errors
                raise
            except Exception as e:
                # For any other errors (connection issues), log and allow
                logger.warning(f"Could not validate tenant {tenant_id}: {e}. Allowing request to proceed.")
        
        return attrs