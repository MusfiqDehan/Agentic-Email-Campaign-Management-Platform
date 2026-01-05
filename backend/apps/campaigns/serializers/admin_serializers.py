from rest_framework import serializers
from apps.authentication.models import Organization, OrganizationMembership
from ..models import EmailTemplate, Campaign, OrganizationEmailConfiguration

class AdminOrganizationSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    template_count = serializers.SerializerMethodField()
    campaign_count = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'owner', 'member_count', 'template_count', 
            'campaign_count', 'created_at', 'is_active'
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

    def get_is_active(self, obj):
        # Check if the organization's email configuration is suspended
        config = OrganizationEmailConfiguration.objects.filter(organization=obj).first()
        if config:
            return not config.is_suspended
        return True
