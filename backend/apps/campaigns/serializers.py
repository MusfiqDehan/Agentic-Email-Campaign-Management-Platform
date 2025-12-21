from rest_framework import serializers
from .models import Campaign, CampaignContact


class CampaignSerializer(serializers.ModelSerializer):
    total_contacts = serializers.SerializerMethodField()
    sent_count = serializers.SerializerMethodField()
    opened_count = serializers.SerializerMethodField()
    clicked_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'subject', 'from_email', 'from_name', 
            'template', 'status', 'scheduled_at', 'sent_at',
            'created_at', 'updated_at', 'total_contacts', 
            'sent_count', 'opened_count', 'clicked_count'
        ]
        read_only_fields = ['created_at', 'updated_at', 'sent_at']
    
    def get_total_contacts(self, obj):
        return obj.campaign_contacts.count()
    
    def get_sent_count(self, obj):
        return obj.campaign_contacts.filter(sent=True).count()
    
    def get_opened_count(self, obj):
        return obj.campaign_contacts.filter(opened=True).count()
    
    def get_clicked_count(self, obj):
        return obj.campaign_contacts.filter(clicked=True).count()


class CampaignContactSerializer(serializers.ModelSerializer):
    contact_email = serializers.EmailField(source='contact.email', read_only=True)
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    
    class Meta:
        model = CampaignContact
        fields = [
            'id', 'campaign', 'contact', 'contact_email', 'contact_name',
            'sent', 'opened', 'clicked', 'bounced', 'created_at'
        ]
        read_only_fields = ['created_at']
