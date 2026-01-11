from rest_framework import serializers
from apps.authentication.models import Organization, OrganizationMembership
from ..models import EmailTemplate, Campaign, OrganizationEmailConfiguration
from .base_serializers import EmailTemplateSerializer


class AdminEmailTemplateSerializer(EmailTemplateSerializer):
    """
    Admin-specific serializer for email templates.
    Allows platform admins to update approval_status and other admin-only fields.
    """
    approval_status = serializers.ChoiceField(
        choices=EmailTemplate.ApprovalStatus.choices,
        required=False
    )
    
    class Meta(EmailTemplateSerializer.Meta):
        # Inherit all fields from parent
        pass
    
    def create(self, validated_data):
        """Set DRAFT status by default for new global templates."""
        is_global = validated_data.get('is_global', False)
        
        # Global templates start as DRAFT by default unless explicitly set to something else
        if is_global and 'approval_status' not in validated_data:
            validated_data['approval_status'] = EmailTemplate.ApprovalStatus.DRAFT
            validated_data['is_draft'] = True
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Handle admin updates including approval status changes."""
        # If approval status is changing to APPROVED, set approved_by
        if 'approval_status' in validated_data:
            new_status = validated_data['approval_status']
            if new_status == EmailTemplate.ApprovalStatus.APPROVED:
                request = self.context.get('request')
                if request and request.user:
                    instance.approved_by = request.user
                    from django.utils import timezone
                    instance.approved_at = timezone.now()
                # Also mark as not draft when approved
                validated_data['is_draft'] = False
            elif new_status == EmailTemplate.ApprovalStatus.DRAFT:
                validated_data['is_draft'] = True
        
        return super().update(instance, validated_data)


class AdminOrganizationSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    template_count = serializers.SerializerMethodField()
    campaign_count = serializers.SerializerMethodField()
    deactivation_reason = serializers.CharField(read_only=True)
    deactivated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'owner', 'member_count', 'template_count', 
            'campaign_count', 'created_at', 'is_active', 'deactivation_reason',
            'deactivated_at'
        ]

    def get_owner(self, obj):
        if obj.owner:
            return {
                'name': f"{obj.owner.first_name} {obj.owner.last_name}".strip() or obj.owner.username,
                'email': obj.owner.email
            }
        return None

    def get_member_count(self, obj):
        return OrganizationMembership.objects.filter(organization=obj).count()

    def get_template_count(self, obj):
        return EmailTemplate.objects.filter(organization=obj, is_deleted=False).count()

    def get_campaign_count(self, obj):
        return Campaign.objects.filter(organization=obj, is_deleted=False).count()
