"""
Serializers for Campaign, Contact, and ContactList models.
"""
import csv
import io
import json
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction

from ..models import Campaign, Contact, ContactList, EmailTemplate, OrganizationEmailProvider
from ..constants import BULK_OPERATION_ASYNC_THRESHOLD


class ContactListSerializer(serializers.ModelSerializer):
    """Serializer for ContactList model."""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = ContactList
        fields = [
            'id', 'organization', 'organization_name', 'name', 'description',
            'double_opt_in', 'total_contacts', 'active_contacts', 
            'unsubscribed_contacts', 'bounced_contacts', 'tags',
            'is_active', 'is_published', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'organization', 'total_contacts', 'active_contacts',
            'unsubscribed_contacts', 'bounced_contacts', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        validated_data['organization'] = self.context['request'].user.organization
        return super().create(validated_data)


class ContactListSummarySerializer(serializers.ModelSerializer):
    """Minimal serializer for ContactList references."""
    
    class Meta:
        model = ContactList
        fields = ['id', 'name', 'total_contacts', 'active_contacts']


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model."""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    lists = ContactListSummarySerializer(many=True, read_only=True)
    list_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of ContactList IDs to add this contact to"
    )
    full_name = serializers.CharField(read_only=True)
    open_rate = serializers.FloatField(read_only=True)
    click_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'organization', 'organization_name', 'email', 'first_name', 
            'last_name', 'full_name', 'phone', 'lists', 'list_ids', 'status',
            'subscribed_at', 'unsubscribed_at', 'confirmed_at', 'source',
            'source_details', 'custom_fields', 'tags',
            'emails_sent', 'emails_opened', 'emails_clicked',
            'open_rate', 'click_rate', 'bounce_count', 'complaint_count',
            'last_email_sent_at', 'last_email_opened_at', 'last_email_clicked_at',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'organization', 'status', 'unsubscribe_token', 
            'subscribed_at', 'unsubscribed_at', 'confirmed_at',
            'emails_sent', 'emails_opened', 'emails_clicked',
            'bounce_count', 'complaint_count',
            'last_email_sent_at', 'last_email_opened_at', 'last_email_clicked_at',
            'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        list_ids = validated_data.pop('list_ids', [])
        validated_data['organization'] = self.context['request'].user.organization
        validated_data['source'] = validated_data.get('source', 'API')
        
        contact = super().create(validated_data)
        
        if list_ids:
            lists = ContactList.objects.filter(
                id__in=list_ids,
                organization=contact.organization
            )
            contact.lists.set(lists)
        
        return contact
    
    def update(self, instance, validated_data):
        list_ids = validated_data.pop('list_ids', None)
        
        instance = super().update(instance, validated_data)
        
        if list_ids is not None:
            lists = ContactList.objects.filter(
                id__in=list_ids,
                organization=instance.organization
            )
            instance.lists.set(lists)
        
        return instance


class ContactMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for Contact references."""
    
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Contact
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'status']


class BulkContactCreateSerializer(serializers.Serializer):
    """Serializer for bulk contact creation from CSV or JSON."""
    
    list_id = serializers.UUIDField(required=False, help_text="ContactList to add contacts to")
    contacts = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="List of contact objects for JSON import"
    )
    csv_data = serializers.CharField(
        required=False,
        help_text="CSV data with header row"
    )
    update_existing = serializers.BooleanField(
        default=False,
        help_text="Update existing contacts instead of skipping"
    )
    
    def validate(self, attrs):
        if not attrs.get('contacts') and not attrs.get('csv_data'):
            raise serializers.ValidationError(
                "Either 'contacts' or 'csv_data' must be provided"
            )
        return attrs
    
    def validate_csv_data(self, value):
        """Parse and validate CSV data."""
        if not value:
            return []
        
        try:
            reader = csv.DictReader(io.StringIO(value))
            contacts = []
            
            for row in reader:
                if 'email' not in row:
                    raise serializers.ValidationError("CSV must have 'email' column")
                contacts.append(dict(row))
            
            return contacts
        except Exception as e:
            raise serializers.ValidationError(f"Invalid CSV data: {str(e)}")
    
    def create(self, validated_data):
        """
        Create contacts from validated data.
        Returns async task ID if count > BULK_OPERATION_ASYNC_THRESHOLD.
        """
        organization = self.context['request'].user.organization
        list_id = validated_data.get('list_id')
        update_existing = validated_data.get('update_existing', False)
        
        # Combine contacts from JSON and CSV
        contacts = validated_data.get('contacts', [])
        if validated_data.get('csv_data'):
            contacts.extend(validated_data['csv_data'])
        
        # Check if async processing is needed
        if len(contacts) > BULK_OPERATION_ASYNC_THRESHOLD:
            from ..tasks import bulk_create_contacts_task
            task = bulk_create_contacts_task.delay(
                organization_id=str(organization.id),
                contacts=contacts,
                list_id=str(list_id) if list_id else None,
                update_existing=update_existing,
                source='CSV_IMPORT' if validated_data.get('csv_data') else 'JSON_IMPORT'
            )
            return {
                'async': True,
                'task_id': task.id,
                'total': len(contacts),
                'message': f"Processing {len(contacts)} contacts asynchronously"
            }
        
        # Synchronous processing for smaller batches
        contact_list = None
        if list_id:
            contact_list = ContactList.objects.filter(
                id=list_id,
                organization=organization
            ).first()
        
        created = 0
        updated = 0
        errors = []
        
        source = 'CSV_IMPORT' if validated_data.get('csv_data') else 'JSON_IMPORT'
        
        with transaction.atomic():
            for idx, contact_data in enumerate(contacts):
                try:
                    email = contact_data.get('email', '').strip().lower()
                    if not email:
                        errors.append({'row': idx, 'error': 'Missing email'})
                        continue
                    
                    contact, was_created = Contact.objects.get_or_create(
                        organization=organization,
                        email=email,
                        defaults={
                            'first_name': contact_data.get('first_name', ''),
                            'last_name': contact_data.get('last_name', ''),
                            'phone': contact_data.get('phone', ''),
                            'source': source,
                            'custom_fields': {
                                k: v for k, v in contact_data.items()
                                if k not in ['email', 'first_name', 'last_name', 'phone']
                            }
                        }
                    )
                    
                    if was_created:
                        created += 1
                    elif update_existing:
                        contact.first_name = contact_data.get('first_name', contact.first_name)
                        contact.last_name = contact_data.get('last_name', contact.last_name)
                        contact.phone = contact_data.get('phone', contact.phone)
                        contact.save()
                        updated += 1
                    
                    if contact_list:
                        contact.lists.add(contact_list)
                        
                except Exception as e:
                    errors.append({'row': idx, 'email': contact_data.get('email'), 'error': str(e)})
        
        # Update list stats
        if contact_list:
            contact_list.update_stats()
        
        return {
            'async': False,
            'created': created,
            'updated': updated,
            'errors': errors,
            'total': len(contacts)
        }


class CampaignSerializer(serializers.ModelSerializer):
    """Serializer for Campaign model."""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    contact_lists = ContactListSummarySerializer(many=True, read_only=True)
    contact_list_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of ContactList IDs to target"
    )
    email_template_name = serializers.CharField(
        source='email_template.template_name', 
        read_only=True
    )
    email_provider_name = serializers.CharField(
        source='email_provider.provider.name',
        read_only=True
    )
    
    # Computed stats
    open_rate = serializers.FloatField(read_only=True)
    click_rate = serializers.FloatField(read_only=True)
    bounce_rate = serializers.FloatField(read_only=True)
    delivery_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'organization', 'organization_name', 'name', 'description',
            'subject', 'preview_text', 'html_content', 'text_content',
            'from_name', 'from_email', 'reply_to',
            'email_template', 'email_template_name',
            'contact_lists', 'contact_list_ids',
            'email_provider', 'email_provider_name',
            'status', 'scheduled_at', 'started_at', 'completed_at',
            'stats_total_recipients', 'stats_sent', 'stats_delivered',
            'stats_opened', 'stats_clicked', 'stats_bounced',
            'stats_complained', 'stats_unsubscribed', 'stats_failed',
            'stats_unique_opens', 'stats_unique_clicks', 'stats_updated_at',
            'open_rate', 'click_rate', 'bounce_rate', 'delivery_rate',
            'batch_size', 'batch_delay_seconds',
            'track_opens', 'track_clicks', 'tags', 'segment_filters',
            'is_active', 'is_published', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'organization', 'status', 'started_at', 'completed_at',
            'stats_total_recipients', 'stats_sent', 'stats_delivered',
            'stats_opened', 'stats_clicked', 'stats_bounced',
            'stats_complained', 'stats_unsubscribed', 'stats_failed',
            'stats_unique_opens', 'stats_unique_clicks', 'stats_updated_at',
            'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        contact_list_ids = validated_data.pop('contact_list_ids', [])
        validated_data['organization'] = self.context['request'].user.organization
        
        campaign = super().create(validated_data)
        
        if contact_list_ids:
            lists = ContactList.objects.filter(
                id__in=contact_list_ids,
                organization=campaign.organization
            )
            campaign.contact_lists.set(lists)
        
        return campaign
    
    def update(self, instance, validated_data):
        contact_list_ids = validated_data.pop('contact_list_ids', None)
        
        # Prevent updating certain fields if campaign is not in draft
        if instance.status not in ['DRAFT', 'SCHEDULED']:
            restricted_fields = [
                'subject', 'html_content', 'text_content', 
                'from_name', 'from_email', 'email_template'
            ]
            for field in restricted_fields:
                if field in validated_data:
                    raise serializers.ValidationError(
                        f"Cannot update {field} for campaign with status {instance.status}"
                    )
        
        instance = super().update(instance, validated_data)
        
        if contact_list_ids is not None:
            lists = ContactList.objects.filter(
                id__in=contact_list_ids,
                organization=instance.organization
            )
            instance.contact_lists.set(lists)
        
        return instance


class CampaignListSerializer(serializers.ModelSerializer):
    """List serializer for campaigns (minimal data)."""
    
    open_rate = serializers.FloatField(read_only=True)
    click_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'status', 'scheduled_at', 'started_at', 'completed_at',
            'stats_total_recipients', 'stats_sent', 'stats_delivered',
            'stats_opened', 'stats_clicked',
            'open_rate', 'click_rate',
            'created_at'
        ]


class CampaignPreviewSerializer(serializers.Serializer):
    """Serializer for campaign preview request."""
    
    contact_id = serializers.UUIDField(
        required=False,
        help_text="Contact ID for personalization preview"
    )
    
    def validate_contact_id(self, value):
        if value:
            organization = self.context['request'].user.organization
            if not Contact.objects.filter(id=value, organization=organization).exists():
                raise serializers.ValidationError("Contact not found")
        return value


class CampaignTestSendSerializer(serializers.Serializer):
    """Serializer for campaign test send request."""
    
    test_emails = serializers.ListField(
        child=serializers.EmailField(),
        min_length=1,
        max_length=5,
        help_text="List of email addresses to send test to (max 5)"
    )
    contact_id = serializers.UUIDField(
        required=False,
        help_text="Contact ID for personalization"
    )


class CampaignDuplicateSerializer(serializers.Serializer):
    """Serializer for campaign duplicate request."""
    
    new_name = serializers.CharField(
        max_length=255,
        required=False,
        help_text="Name for the duplicated campaign"
    )


class CampaignScheduleSerializer(serializers.Serializer):
    """Serializer for scheduling a campaign."""
    
    scheduled_at = serializers.DateTimeField(
        help_text="When to send the campaign (UTC)"
    )
    
    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future")
        return value


class CampaignAnalyticsSerializer(serializers.Serializer):
    """Serializer for campaign analytics response."""
    
    period = serializers.ChoiceField(
        choices=['hour', 'day', 'week', 'month'],
        default='day'
    )
    
    # Time series data would be computed in the view
    timeline = serializers.ListField(read_only=True)
    totals = serializers.DictField(read_only=True)


class UnsubscribeSerializer(serializers.Serializer):
    """Serializer for contact unsubscribe request."""
    
    token = serializers.CharField(help_text="Unsubscribe token from email link")
    reason = serializers.CharField(
        required=False,
        max_length=500,
        help_text="Optional reason for unsubscribing"
    )
    
    def validate_token(self, value):
        contact = Contact.objects.filter(unsubscribe_token=value).first()
        if not contact:
            raise serializers.ValidationError("Invalid unsubscribe token")
        if contact.status == 'UNSUBSCRIBED':
            raise serializers.ValidationError("Already unsubscribed")
        return value


class GDPRForgetSerializer(serializers.Serializer):
    """Serializer for GDPR forget request."""
    
    email = serializers.EmailField(help_text="Email address to forget")
    confirm = serializers.BooleanField(
        help_text="Confirm deletion (must be true)"
    )
    
    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError("Must confirm deletion")
        return value
