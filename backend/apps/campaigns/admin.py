from django.contrib import admin
from .models import Campaign, CampaignContact


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'status', 'created_at', 'sent_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'subject', 'from_email']


@admin.register(CampaignContact)
class CampaignContactAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'contact', 'sent', 'opened', 'clicked', 'bounced']
    list_filter = ['sent', 'opened', 'clicked', 'bounced']
