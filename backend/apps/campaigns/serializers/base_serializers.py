"""
Base Serializers for Campaigns Application

Simplified serializers with organization-based scoping.
Removed deprecated fields: template_type, rule_scope, product_id, activated_by_*
"""

from rest_framework import serializers
from ..models import (
    EmailTemplate, AutomationRule, SMSConfigurationModel, 
    SMSTemplate, OrganizationEmailConfiguration, EmailProvider, EmailDeliveryLog,
    TemplateUsageLog, TemplateUpdateNotification, OrganizationTemplateNotification,
    TemplateApprovalRequest, Notification
)
from ..utils import encrypt_data
import logging

logger = logging.getLogger(__name__)


class EmailTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for email templates.
    Supports both global templates and organization-scoped templates.
    """
    organization_id = serializers.UUIDField(write_only=True, required=False)
    category = serializers.ChoiceField(
        choices=EmailTemplate.TemplateCategory.choices,
        required=False,
        default=EmailTemplate.TemplateCategory.OTHER
    )
    approval_status = serializers.ChoiceField(
        choices=EmailTemplate.ApprovalStatus.choices,
        read_only=True
    )
    
    # Computed fields
    source_template_name = serializers.SerializerMethodField()
    source_template_version = serializers.SerializerMethodField()
    has_newer_version = serializers.SerializerMethodField()
    
    # Read-only tracking fields
    usage_count = serializers.IntegerField(read_only=True)
    duplicated_by = serializers.StringRelatedField(read_only=True)
    approved_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'organization', 'organization_id', 'template_name', 'category', 
            'email_subject', 'preview_text', 'email_body', 'text_body',
            'description', 'tags',
            # Global template fields
            'is_global', 'source_template', 'source_template_name', 'source_template_version',
            'usage_count', 'duplicated_by',
            # Versioning fields
            'version', 'version_notes', 'parent_version', 'has_newer_version',
            # Approval workflow fields
            'is_draft', 'approval_status', 'submitted_for_approval_at',
            'approved_by', 'approved_at',
            # Standard fields
            'is_active', 'is_published', 'created_at', 'updated_at'
        ]
        read_only_fields = (
            'id', 'organization', 'created_at', 'updated_at', 'usage_count',
            'duplicated_by', 'approved_by', 'approved_at', 'submitted_for_approval_at'
        )
    
    def get_source_template_name(self, obj):
        """Get the name of the source global template if this was duplicated."""
        if obj.source_template:
            return obj.source_template.template_name
        return None
    
    def get_source_template_version(self, obj):
        """Get the version of the source global template."""
        if obj.source_template:
            return obj.source_template.version
        return None
    
    def get_has_newer_version(self, obj):
        """Check if the source global template has a newer version available."""
        if not obj.source_template or obj.is_global:
            return False
        
        # Get the latest approved version of the source template
        latest = EmailTemplate.objects.filter(
            id=obj.source_template.id,
            is_global=True,
            approval_status=EmailTemplate.ApprovalStatus.APPROVED,
            is_deleted=False
        ).first()
        
        if latest and latest.version > obj.version:
            return True
        return False
    
    def validate(self, data):
        """Validate template data based on global/organization scope."""
        request = self.context.get('request')
        is_global = data.get('is_global', False)
        
        # Only platform admins can create/edit global templates
        if is_global:
            if not request or not request.user.is_platform_admin:
                raise serializers.ValidationError({
                    'is_global': 'Only platform administrators can create global templates.'
                })
            # Global templates should not have an organization
            if 'organization_id' in data or data.get('organization'):
                raise serializers.ValidationError({
                    'organization': 'Global templates cannot be associated with an organization.'
                })
        else:
            # Organization templates must have an organization
            if not data.get('organization_id') and not self.instance:
                raise serializers.ValidationError({
                    'organization_id': 'Organization-specific templates require an organization_id.'
                })
        
        return data
    
    def create(self, validated_data):
        # Get organization_id from validated_data or context
        organization_id = validated_data.pop('organization_id', None)
        is_global = validated_data.get('is_global', False)
        
        if not is_global:
            if not organization_id and 'request' in self.context:
                # Try to get from request user
                request = self.context['request']
                if hasattr(request.user, 'organization_id'):
                    organization_id = request.user.organization_id
            
            if not organization_id:
                raise serializers.ValidationError({
                    'organization_id': 'Organization ID is required for non-global templates.'
                })
            
            validated_data['organization_id'] = organization_id
        
        return super().create(validated_data)


class AutomationRuleSerializer(serializers.ModelSerializer):
    """
    Serializer for automation rules.
    All rules are organization-scoped.
    """
    organization_id = serializers.UUIDField(source='organization.id', read_only=True)
    campaign_id = serializers.UUIDField(source='campaign.id', read_only=True, allow_null=True)
    contact_list_id = serializers.UUIDField(source='contact_list.id', read_only=True, allow_null=True)

    class Meta:
        model = AutomationRule
        fields = [
            'id', 'automation_name', 'organization_id', 'campaign_id', 'contact_list_id',
            'reason_name', 'trigger_type', 'schedule_frequency',
            'communication_type', 'short_description', 'email_template_id', 'sms_template_id',
            'sms_config_id', 'delay_amount', 'delay_unit',
            'schedule_interval_amount', 'schedule_interval_unit', 'schedule_time',
            'schedule_day_of_week', 'schedule_day_of_month', 'is_active', 'is_published',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'organization_id', 'periodic_task', 'created_at', 'updated_at')

    def validate(self, data):
        """
        Add custom validation based on the trigger_type and schedule_frequency.
        """
        trigger_type = data.get('trigger_type')

        if trigger_type == AutomationRule.TriggerType.DELAY:
            if not data.get('delay_amount') or not data.get('delay_unit'):
                raise serializers.ValidationError(
                    "For a 'DELAY' trigger, 'delay_amount' and 'delay_unit' are required."
                )

        elif trigger_type == AutomationRule.TriggerType.SCHEDULE:
            frequency = data.get('schedule_frequency')
            if not frequency:
                raise serializers.ValidationError(
                    "For a 'SCHEDULE' trigger, 'schedule_frequency' is required."
                )
            
            if frequency == AutomationRule.ScheduleFrequency.INTERVAL:
                if not data.get('schedule_interval_amount') or not data.get('schedule_interval_unit'):
                    raise serializers.ValidationError(
                        "For 'INTERVAL' frequency, 'schedule_interval_amount' and "
                        "'schedule_interval_unit' are required."
                    )
            else:  # DAILY, WEEKLY, MONTHLY
                if not data.get('schedule_time'):
                    raise serializers.ValidationError(
                        "For 'DAILY', 'WEEKLY', or 'MONTHLY' frequency, 'schedule_time' is required."
                    )
                if frequency == AutomationRule.ScheduleFrequency.WEEKLY and not data.get('schedule_day_of_week'):
                    raise serializers.ValidationError(
                        "For 'WEEKLY' frequency, 'schedule_day_of_week' is required."
                    )
                if frequency == AutomationRule.ScheduleFrequency.MONTHLY and not data.get('schedule_day_of_month'):
                    raise serializers.ValidationError(
                        "For 'MONTHLY' frequency, 'schedule_day_of_month' is required."
                    )
            
        return data


class TriggerEmailSerializer(serializers.Serializer):
    """
    Serializer for validating the trigger email request.
    Organization is determined from the authenticated user.
    """
    automation_name = serializers.CharField(max_length=255, required=False)
    rule_id = serializers.UUIDField(required=False)
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


class SMSConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for SMS configuration settings (Twilio integration).
    """
    organization_id = serializers.UUIDField(source='organization.id', read_only=True)

    class Meta:
        model = SMSConfigurationModel
        fields = [
            'id', 'name_or_type', 'organization_id', 'endpoint_url', 'account_ssid',
            'auth_token', 'verified_service_id', 'default_from_number',
            'whatsapp_from_number', 'whatsapp_enabled', 'is_active', 'is_published',
            'created_at', 'updated_at'
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
    organization_id = serializers.UUIDField(source='organization.id', read_only=True)

    class Meta:
        model = SMSTemplate
        fields = [
            'id', 'template_name', 'organization_id', 'sms_body', 'recipient_numbers_list',
            'is_active', 'is_published', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'organization_id', 'created_at', 'updated_at')


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

    def validate(self, attrs):
        """
        Validate that either reason_name or rule_id is provided.
        """
        if not attrs.get('reason_name') and not attrs.get('rule_id'):
            raise serializers.ValidationError("Either 'reason_name' or 'rule_id' must be provided.")
        return attrs


# Enhanced serializers for organization configuration
class OrganizationEmailConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for organization email configuration"""
    
    organization_id = serializers.UUIDField(source='organization.id', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    usage_percentage_daily = serializers.SerializerMethodField(read_only=True)
    usage_percentage_monthly = serializers.SerializerMethodField(read_only=True)
    can_send_email_status = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = OrganizationEmailConfiguration
        fields = [
            'id', 'organization_id', 'organization_name', 'plan_type', 'plan_limits',
            'default_from_domain', 'custom_domain', 'custom_domain_verified', 'timezone',
            'emails_sent_today', 'emails_sent_this_month', 'last_email_sent_at',
            'is_suspended', 'suspension_reason', 'bounce_rate', 'complaint_rate',
            'reputation_score', 'usage_percentage_daily', 'usage_percentage_monthly',
            'can_send_email_status', 'is_active', 'is_published',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'organization_id', 'organization_name',
            'emails_sent_today', 'emails_sent_this_month', 'last_email_sent_at',
            'bounce_rate', 'complaint_rate', 'reputation_score',
            'created_at', 'updated_at'
        ]
    
    def get_usage_percentage_daily(self, obj):
        daily_limit = obj.get_daily_limit()
        if daily_limit == 0:
            return 0
        return round((obj.emails_sent_today / daily_limit) * 100, 2)
    
    def get_usage_percentage_monthly(self, obj):
        monthly_limit = obj.get_monthly_limit()
        if monthly_limit == 0:
            return 0
        return round((obj.emails_sent_this_month / monthly_limit) * 100, 2)
    
    def get_can_send_email_status(self, obj):
        can_send, reason = obj.can_send_email()
        return {'can_send': can_send, 'reason': reason}


class EmailProviderSerializer(serializers.ModelSerializer):
    """Serializer for email providers"""
    
    organization_id = serializers.UUIDField(source='organization.id', read_only=True, allow_null=True)
    config = serializers.JSONField(required=False)
    config_status = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = EmailProvider
        fields = [
            'id', 'name', 'organization_id', 'provider_type', 'is_shared',
            'max_emails_per_minute', 'max_emails_per_hour', 'max_emails_per_day',
            'is_active', 'is_published', 'is_default', 'priority',
            'health_status', 'config', 'config_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['organization_id', 'encrypted_config', 'health_status', 'last_health_check']
    
    def to_representation(self, instance):
        """Decrypt and mask sensitive configuration fields for display."""
        data = super().to_representation(instance)
        try:
            config = instance.decrypt_config()
            # Mask sensitive fields
            sensitive_keys = [
                'password', 'smtp_password', 'aws_secret_access_key', 
                'api_key', 'aws_session_token', 'secret_key'
            ]
            for key in sensitive_keys:
                if key in config and config[key]:
                    config[key] = '********'
            data['config'] = config
        except Exception:
            data['config'] = {}
        return data

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
            # Merge with existing config to avoid losing fields not sent by frontend
            current_config = instance.decrypt_config()
            for key, value in config.items():
                # Only update if value is not the mask
                if value != '********':
                    current_config[key] = value
            instance.encrypt_config(current_config)
            instance.save()
        return instance


class EnhancedEmailDeliveryLogSerializer(serializers.ModelSerializer):
    """Enhanced serializer for email delivery logs"""
    
    automation_rule_name = serializers.CharField(source='campaigns.automation_name', read_only=True)
    provider_name = serializers.CharField(source='email_provider.name', read_only=True)
    organization_id = serializers.UUIDField(source='organization.id', read_only=True, allow_null=True)
    campaign_id = serializers.UUIDField(source='campaign.id', read_only=True, allow_null=True)
    email_template_id = serializers.UUIDField(source='email_template.id', allow_null=True, read_only=True)
    queue_item_id = serializers.UUIDField(source='queue_item.id', allow_null=True, read_only=True)
    
    class Meta:
        model = EmailDeliveryLog
        fields = [
            'id', 'automation_rule', 'automation_rule_name', 'organization_id', 'campaign_id',
            'reason_name', 'trigger_type', 'recipient_email', 'sender_email',
            'subject', 'delivery_status', 'planned_delivery_at', 'queue_item_id',
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


class EnhancedTriggerEmailSerializer(serializers.Serializer):
    """Enhanced serializer for triggering emails with provider support"""
    
    # Rule identification (one required)
    automation_name = serializers.CharField(max_length=255, required=False)
    rule_id = serializers.UUIDField(required=False)
    reason_name = serializers.ChoiceField(choices=AutomationRule.ReasonName.choices, required=False)
    
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
        return attrs

class TemplateUsageLogSerializer(serializers.ModelSerializer):
    """Serializer for template usage logs."""
    template_name = serializers.CharField(source='template.template_name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    user_name = serializers.SerializerMethodField()
    duplicated_template_name = serializers.CharField(source='duplicated_template.template_name', read_only=True)
    
    class Meta:
        model = TemplateUsageLog
        fields = [
            'id', 'template', 'template_name', 'organization', 'organization_name',
            'user', 'user_name', 'duplicated_template', 'duplicated_template_name',
            'duplicated_at', 'template_name_at_duplication', 'template_version_at_duplication'
        ]
        read_only_fields = ['id', 'duplicated_at']
    
    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None


class TemplateUpdateNotificationSerializer(serializers.ModelSerializer):
    """Serializer for template update notifications."""
    global_template_name = serializers.CharField(source='global_template.template_name', read_only=True)
    global_template_category = serializers.CharField(source='global_template.category', read_only=True)
    
    class Meta:
        model = TemplateUpdateNotification
        fields = [
            'id', 'global_template', 'global_template_name', 'global_template_category',
            'old_version', 'new_version', 'update_summary', 'created_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at']


class OrganizationTemplateNotificationSerializer(serializers.ModelSerializer):
    """Serializer for organization-specific template notifications."""
    notification = TemplateUpdateNotificationSerializer(read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    read_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OrganizationTemplateNotification
        fields = [
            'id', 'notification', 'organization', 'organization_name',
            'is_read', 'read_at', 'read_by', 'read_by_name',
            'template_updated'
        ]
        read_only_fields = ['id', 'read_at']
    
    def get_read_by_name(self, obj):
        if obj.read_by:
            return obj.read_by.get_full_name() or obj.read_by.username
        return None


class TemplateApprovalRequestSerializer(serializers.ModelSerializer):
    """Serializer for template approval requests."""
    template_name = serializers.CharField(source='template.template_name', read_only=True)
    template_details = EmailTemplateSerializer(source='template', read_only=True)
    requested_by_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    status = serializers.ChoiceField(
        choices=TemplateApprovalRequest.ApprovalStatus.choices,
        read_only=True
    )
    
    class Meta:
        model = TemplateApprovalRequest
        fields = [
            'id', 'template', 'template_name', 'template_details',
            'requested_by', 'requested_by_name', 'requested_at', 'approval_notes',
            'reviewed_by', 'reviewed_by_name', 'reviewed_at',
            'status', 'reviewer_notes', 'version_before_approval', 'changes_summary'
        ]
        read_only_fields = ['id', 'requested_at', 'reviewed_at', 'status']
    
    def get_requested_by_name(self, obj):
        if obj.requested_by:
            return obj.requested_by.get_full_name() or obj.requested_by.username
        return None
    
    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name() or obj.reviewed_by.username
        return None


class TemplatePreviewSerializer(serializers.Serializer):
    """Serializer for template preview requests."""
    template_id = serializers.UUIDField(required=True)
    test_email = serializers.EmailField(required=True)
    variables = serializers.JSONField(required=False, default=dict)
    
    def validate_variables(self, value):
        """Ensure variables is a dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Variables must be a dictionary.")
        return value


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for campaign and system notifications."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'organization', 'user', 'notification_type', 'title', 'message',
            'related_object_type', 'related_object_id', 'metadata',
            'is_read', 'read_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'read_at']
