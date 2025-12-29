"""
Serializers for Campaign, Contact, and ContactList models.
"""
import csv
import io
import json
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction

from ..models import (
    Campaign,
    Contact,
    ContactList,
    EmailTemplate,
    EmailProvider,
    OrganizationEmailProvider,
)
from ..constants import BULK_OPERATION_ASYNC_THRESHOLD

# Try to import openpyxl for XLSX support
try:
    import openpyxl
    XLSX_SUPPORTED = True
except ImportError:
    XLSX_SUPPORTED = False


class OrganizationScopedProviderField(serializers.PrimaryKeyRelatedField):
    """Resolve email providers scoped to the requester's organization."""

    def _get_request(self):
        if hasattr(self, 'context') and self.context.get('request'):
            return self.context['request']
        parent = getattr(self, 'parent', None)
        if parent and parent.context.get('request'):
            return parent.context['request']
        root = getattr(self, 'root', None)
        if root and getattr(root, 'context', None):
            return root.context.get('request')
        return None

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            request = self._get_request()
            organization = getattr(getattr(request, 'user', None), 'organization', None)
            if not organization:
                raise exc

            provider_id = str(data)
            provider = EmailProvider.objects.filter(
                id=provider_id,
                organization=organization,
                is_shared=False,
                is_deleted=False,
            ).first()

            if not provider:
                raise serializers.ValidationError("Email provider not available for this organization.")

            org_provider, _ = OrganizationEmailProvider.objects.get_or_create(
                organization=organization,
                provider=provider,
                defaults={'is_enabled': True, 'is_primary': provider.is_default},
            )

            return org_provider


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
        # Organization should be passed via save(organization=...) from the view
        # If not present in validated_data, get it from context
        if 'organization' not in validated_data:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                validated_data['organization'] = request.user.organization
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
    
    def to_internal_value(self, data):
        """Allow clients to send `lists` (UUIDs or objects) instead of list_ids."""
        mutable_data = data.copy()
        if 'lists' in mutable_data and 'list_ids' not in mutable_data:
            lists_value = mutable_data.pop('lists')
            extracted_ids = []
            if isinstance(lists_value, list):
                for item in lists_value:
                    if isinstance(item, str):
                        extracted_ids.append(item)
                    elif isinstance(item, dict):
                        item_id = item.get('id') or item.get('pk')
                        if item_id:
                            extracted_ids.append(item_id)
            mutable_data['list_ids'] = extracted_ids
        return super().to_internal_value(mutable_data)
    
    def create(self, validated_data):
        list_ids = validated_data.pop('list_ids', [])
        
        # Organization should be passed via save(organization=...) from the view
        # If not present in validated_data, get it from context
        if 'organization' not in validated_data:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                validated_data['organization'] = request.user.organization
        
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
    """
    Serializer for bulk contact creation from CSV, XLSX, or JSON.
    
    Supports three methods of import:
    1. JSON array of contacts in 'contacts' field
    2. CSV string data in 'csv_data' field
    3. File upload (CSV or XLSX) in 'file' field
    
    Expected file/data format:
    - Required column: email
    - Optional columns: first_name, last_name, phone, tags, metadata/custom_fields
    - Any additional columns will be stored in custom_fields/metadata
    
    Example CSV:
        email,first_name,last_name,phone,company,role
        john@example.com,John,Doe,+1234567890,Acme Inc,Developer
        jane@example.com,Jane,Smith,+0987654321,Tech Corp,Manager
    
    Example JSON:
        {
            "list_id": "uuid-here",
            "contacts": [
                {"email": "john@example.com", "first_name": "John", "metadata": {"company": "Acme"}}
            ],
            "tags": ["imported"],
            "update_existing": true
        }
    """
    
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
    file = serializers.FileField(
        required=False,
        help_text="CSV or XLSX file upload. Must have 'email' column."
    )
    update_existing = serializers.BooleanField(
        default=False,
        help_text="Update existing contacts instead of skipping"
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
        help_text="Tags to apply to all imported contacts"
    )
    
    def validate(self, attrs):
        has_contacts = bool(attrs.get('contacts'))
        has_csv_data = bool(attrs.get('csv_data'))
        has_file = bool(attrs.get('file'))
        
        if not has_contacts and not has_csv_data and not has_file:
            raise serializers.ValidationError(
                "One of 'contacts', 'csv_data', or 'file' must be provided"
            )
        
        # Parse file if provided
        if has_file:
            file_obj = attrs['file']
            filename = file_obj.name.lower()
            
            if filename.endswith('.csv'):
                attrs['_parsed_file_contacts'] = self._parse_csv_file(file_obj)
                attrs['_import_source'] = 'CSV_IMPORT'
            elif filename.endswith('.xlsx') or filename.endswith('.xls'):
                attrs['_parsed_file_contacts'] = self._parse_xlsx_file(file_obj)
                attrs['_import_source'] = 'XLSX_IMPORT'
            else:
                raise serializers.ValidationError({
                    'file': "Unsupported file format. Please upload a CSV or XLSX file."
                })
        
        return attrs
    
    def _parse_csv_file(self, file_obj):
        """Parse CSV file and return list of contact dictionaries."""
        try:
            # Read file content
            content = file_obj.read()
            
            # Try to decode with different encodings
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    text = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise serializers.ValidationError({
                    'file': "Unable to decode file. Please ensure it's a valid CSV with UTF-8 encoding."
                })
            
            reader = csv.DictReader(io.StringIO(text))
            contacts = []
            
            # Normalize headers (lowercase, strip whitespace)
            if reader.fieldnames is None:
                raise serializers.ValidationError({
                    'file': "CSV file appears to be empty or has no headers."
                })
            
            # Check for email column
            fieldnames_lower = [f.lower().strip() for f in reader.fieldnames]
            if 'email' not in fieldnames_lower:
                raise serializers.ValidationError({
                    'file': f"CSV must have an 'email' column. Found columns: {', '.join(reader.fieldnames)}"
                })
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                # Normalize row keys
                normalized_row = {}
                for key, value in row.items():
                    if key:
                        normalized_key = key.lower().strip()
                        normalized_row[normalized_key] = value.strip() if value else ''
                
                if normalized_row.get('email'):
                    contacts.append(normalized_row)
            
            if not contacts:
                raise serializers.ValidationError({
                    'file': "No valid contacts found in CSV file."
                })
            
            return contacts
            
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError({
                'file': f"Error parsing CSV file: {str(e)}"
            })
    
    def _parse_xlsx_file(self, file_obj):
        """Parse XLSX file and return list of contact dictionaries."""
        if not XLSX_SUPPORTED:
            raise serializers.ValidationError({
                'file': "XLSX support is not available. Please install openpyxl or use CSV format."
            })
        
        try:
            workbook = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
            sheet = workbook.active
            
            if sheet is None:
                raise serializers.ValidationError({
                    'file': "XLSX file has no active worksheet."
                })
            
            rows = list(sheet.iter_rows(values_only=True))
            
            if len(rows) < 2:  # Need at least header + 1 data row
                raise serializers.ValidationError({
                    'file': "XLSX file must have a header row and at least one data row."
                })
            
            # Get headers from first row and normalize
            headers = [str(h).lower().strip() if h else f'column_{i}' for i, h in enumerate(rows[0])]
            
            if 'email' not in headers:
                raise serializers.ValidationError({
                    'file': f"XLSX must have an 'email' column. Found columns: {', '.join(headers)}"
                })
            
            contacts = []
            for row_num, row in enumerate(rows[1:], start=2):
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        # Convert value to string, handle None and numbers
                        if value is None:
                            str_value = ''
                        elif isinstance(value, (int, float)):
                            str_value = str(value)
                        else:
                            str_value = str(value).strip()
                        row_dict[headers[i]] = str_value
                
                if row_dict.get('email'):
                    contacts.append(row_dict)
            
            workbook.close()
            
            if not contacts:
                raise serializers.ValidationError({
                    'file': "No valid contacts found in XLSX file."
                })
            
            return contacts
            
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError({
                'file': f"Error parsing XLSX file: {str(e)}"
            })
    
    def validate_csv_data(self, value):
        """Parse and validate CSV data string."""
        if not value:
            return []
        
        try:
            reader = csv.DictReader(io.StringIO(value))
            contacts = []
            
            if reader.fieldnames is None:
                raise serializers.ValidationError("CSV data appears to be empty.")
            
            # Normalize headers
            fieldnames_lower = [f.lower().strip() for f in reader.fieldnames]
            if 'email' not in fieldnames_lower:
                raise serializers.ValidationError("CSV must have 'email' column")
            
            for row in reader:
                # Normalize row keys
                normalized_row = {}
                for key, value in row.items():
                    if key:
                        normalized_key = key.lower().strip()
                        normalized_row[normalized_key] = value.strip() if value else ''
                
                if normalized_row.get('email'):
                    contacts.append(normalized_row)
            
            return contacts
        except serializers.ValidationError:
            raise
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
        global_tags = validated_data.get('tags', [])
        
        # Collect contacts from all sources
        contacts = []
        source = 'API_IMPORT'
        
        # From JSON contacts array
        if validated_data.get('contacts'):
            contacts.extend(validated_data['contacts'])
            source = 'JSON_IMPORT'
        
        # From CSV data string
        if validated_data.get('csv_data'):
            contacts.extend(validated_data['csv_data'])
            source = 'CSV_IMPORT'
        
        # From file upload
        if validated_data.get('_parsed_file_contacts'):
            contacts.extend(validated_data['_parsed_file_contacts'])
            source = validated_data.get('_import_source', 'FILE_IMPORT')
        
        # Check if async processing is needed
        if len(contacts) > BULK_OPERATION_ASYNC_THRESHOLD:
            from ..tasks import bulk_create_contacts_task
            task = bulk_create_contacts_task.delay(
                organization_id=str(organization.id),
                contacts=contacts,
                list_id=str(list_id) if list_id else None,
                update_existing=update_existing,
                source=source,
                tags=global_tags
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
        skipped = 0
        errors = []
        
        with transaction.atomic():
            for idx, contact_data in enumerate(contacts):
                try:
                    email = contact_data.get('email', '').strip().lower()
                    if not email:
                        errors.append({'row': idx + 1, 'error': 'Missing email'})
                        continue
                    
                    # Extract standard fields
                    first_name = contact_data.get('first_name', '') or contact_data.get('firstname', '')
                    last_name = contact_data.get('last_name', '') or contact_data.get('lastname', '')
                    phone = contact_data.get('phone', '') or contact_data.get('phone_number', '')
                    
                    # Extract tags from contact data or use global tags
                    contact_tags = contact_data.get('tags', [])
                    if isinstance(contact_tags, str):
                        contact_tags = [t.strip() for t in contact_tags.split(',') if t.strip()]
                    all_tags = list(set(global_tags + contact_tags))
                    
                    # Extract metadata/custom_fields
                    metadata = contact_data.get('metadata', {})
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            metadata = {}
                    
                    # Build custom_fields from remaining data
                    standard_fields = {'email', 'first_name', 'firstname', 'last_name', 'lastname', 
                                       'phone', 'phone_number', 'tags', 'metadata', 'custom_fields'}
                    custom_fields = {
                        k: v for k, v in contact_data.items()
                        if k.lower() not in standard_fields and v
                    }
                    custom_fields.update(metadata)
                    
                    contact = Contact.all_objects.filter(
                        organization=organization,
                        email=email
                    ).first()
                    
                    was_created = False
                    if not contact:
                        contact = Contact.objects.create(
                            organization=organization,
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                            phone=phone,
                            source=source,
                            tags=all_tags,
                            custom_fields=custom_fields
                        )
                        was_created = True
                    else:
                        # Existing contact found (could be soft-deleted)
                        if contact.is_deleted:
                            contact.is_deleted = False
                            # Mark as created in terms of stats/UI if it was restored? 
                            # Actually was_created=True might be misleading but fits the logic of adding it back.
                            # But let's stay accurate to DB: was_created = False.
                    
                    if was_created:
                        created += 1
                    elif update_existing:
                        if first_name:
                            contact.first_name = first_name
                        if last_name:
                            contact.last_name = last_name
                        if phone:
                            contact.phone = phone
                        if all_tags:
                            contact.tags = list(set(contact.tags or [] + all_tags))
                        if custom_fields:
                            contact.custom_fields = {**(contact.custom_fields or {}), **custom_fields}
                        contact.save()
                        updated += 1
                    else:
                        skipped += 1
                    
                    if contact_list:
                        contact.lists.add(contact_list)
                        
                except Exception as e:
                    errors.append({
                        'row': idx + 1, 
                        'email': contact_data.get('email', 'unknown'), 
                        'error': str(e)
                    })
        
        # Update list stats
        if contact_list:
            contact_list.update_stats()
        
        return {
            'async': False,
            'created': created,
            'updated': updated,
            'skipped': skipped,
            'errors': errors,
            'total': len(contacts),
            'source': source
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
    email_provider = OrganizationScopedProviderField(
        queryset=OrganizationEmailProvider.objects.none(),
        required=False,
        allow_null=True
    )
    email_provider_name = serializers.CharField(
        source='email_provider.provider.name',
        read_only=True
    )
    
    # Make these fields optional - they can be derived from email_template or provider
    html_content = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="HTML email body. If not provided, will use email_template content."
    )
    from_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        help_text="Sender name. If not provided, will use email_template or provider default."
    )
    from_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="Sender email. If not provided, will use email_template or provider default."
    )
    subject = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text="Email subject. If not provided, will use email_template subject."
    )
    
    # Settings as a nested object for cleaner API
    settings = serializers.DictField(
        required=False,
        write_only=True,
        help_text="Campaign settings: track_opens, track_clicks, batch_size, etc."
    )
    
    # Email variables for template personalization
    email_variables = serializers.DictField(
        required=False,
        write_only=True,
        help_text="Variables to use for template personalization"
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
            'settings', 'email_variables',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request') if hasattr(self, 'context') else None
        organization = getattr(getattr(request, 'user', None), 'organization', None)
        if organization and 'email_provider' in self.fields:
            self.fields['email_provider'].queryset = OrganizationEmailProvider.objects.filter(
                organization=organization
            )
    
    def to_internal_value(self, data):
        """
        Handle both 'contact_lists' and 'contact_list_ids' in input.
        Also extract UUIDs from list of objects if provided.
        """
        mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)
        
        # Handle contact_lists input - convert to contact_list_ids
        if 'contact_lists' in mutable_data and 'contact_list_ids' not in mutable_data:
            contact_lists_value = mutable_data.pop('contact_lists')
            extracted_ids = []
            if isinstance(contact_lists_value, list):
                for item in contact_lists_value:
                    if isinstance(item, str):
                        extracted_ids.append(item)
                    elif isinstance(item, dict):
                        item_id = item.get('id') or item.get('pk')
                        if item_id:
                            extracted_ids.append(str(item_id))
            mutable_data['contact_list_ids'] = extracted_ids
        
        return super().to_internal_value(mutable_data)
    
    def _get_provider_config(self, email_provider):
        """Extract from_email and from_name from provider config."""
        if not email_provider:
            return None, None
        
        try:
            # For OrganizationEmailProvider, get the underlying provider config
            if hasattr(email_provider, 'provider'):
                config = email_provider.get_effective_config()
            else:
                config = email_provider.decrypt_config()

            raw_from_email = (
                config.get('from_email')
                or config.get('default_from_email')
                or config.get('sender_email')
                or ''
            )
            from_name = (
                config.get('from_name')
                or config.get('default_from_name')
                or config.get('sender_name')
                or ''
            )

            email_address = raw_from_email.strip()
            parsed_name = None

            # Parse "Name <email>" format if present
            if raw_from_email and '<' in raw_from_email and '>' in raw_from_email:
                import re
                match = re.match(r'^(.+?)\s*<(.+?)>$', raw_from_email.strip())
                if match:
                    parsed_name = match.group(1).strip()
                    email_address = match.group(2).strip()

            if not from_name:
                from_name = parsed_name or ''

            if not from_name and email_address:
                local_part = email_address.split('@', 1)[0]
                friendly_name = local_part.replace('.', ' ').replace('_', ' ').strip()
                from_name = friendly_name.title() if friendly_name else ''
            
            return (from_name or None), (email_address or None)
        except Exception:
            return None, None
    
    def validate(self, attrs):
        """
        Validate that we have all required content, either directly, via template, or via provider.
        """
        email_template = attrs.get('email_template')
        email_provider = attrs.get('email_provider')
        html_content = attrs.get('html_content')
        from_name = attrs.get('from_name')
        from_email = attrs.get('from_email')
        subject = attrs.get('subject')
        
        # If updating existing campaign, get current values
        if self.instance:
            email_template = email_template if 'email_template' in attrs else self.instance.email_template
            email_provider = email_provider if 'email_provider' in attrs else self.instance.email_provider
            html_content = html_content if 'html_content' in attrs else self.instance.html_content
            from_name = from_name if 'from_name' in attrs else self.instance.from_name
            from_email = from_email if 'from_email' in attrs else self.instance.from_email
            subject = subject if 'subject' in attrs else self.instance.subject
        
        # Get template + provider fallback values
        provider_from_name, provider_from_email = self._get_provider_config(email_provider)
        template_from_name = getattr(email_template, 'default_from_name', None)
        template_from_email = getattr(email_template, 'default_from_email', None)
        
        # Check if we have HTML content either directly or from template
        has_html = bool(html_content)
        has_template_html = email_template and email_template.email_body
        if not has_html and not has_template_html:
            raise serializers.ValidationError({
                'html_content': "Either 'html_content' or a valid 'email_template' with content is required."
            })
        
        # Check if we have from_name (direct > template > provider)
        has_from_name = bool(from_name)
        has_template_from_name = bool(template_from_name)
        has_provider_from_name = bool(provider_from_name)
        if not has_from_name and not has_template_from_name and not has_provider_from_name:
            raise serializers.ValidationError({
                'from_name': "Either 'from_name', a valid 'email_template' with default_from_name, or 'email_provider' with from_name in config is required."
            })
        
        # Check if we have from_email (direct > template > provider)
        has_from_email = bool(from_email)
        has_template_from_email = bool(template_from_email)
        has_provider_from_email = bool(provider_from_email)
        if not has_from_email and not has_template_from_email and not has_provider_from_email:
            raise serializers.ValidationError({
                'from_email': "Either 'from_email', a valid 'email_template' with default_from_email, or 'email_provider' with from_email in config is required."
            })
        
        # Check if we have subject (direct > template)
        has_subject = bool(subject)
        has_template_subject = email_template and email_template.email_subject
        if not has_subject and not has_template_subject:
            raise serializers.ValidationError({
                'subject': "Either 'subject' or a valid 'email_template' with email_subject is required."
            })
        
        return attrs
    
    def _apply_settings(self, validated_data):
        """Extract and apply settings from the nested settings object."""
        settings = validated_data.pop('settings', None)
        if settings:
            # Map settings to model fields
            if 'track_opens' in settings:
                validated_data['track_opens'] = settings['track_opens']
            if 'track_clicks' in settings:
                validated_data['track_clicks'] = settings['track_clicks']
            if 'batch_size' in settings:
                validated_data['batch_size'] = settings['batch_size']
            if 'batch_delay_seconds' in settings:
                validated_data['batch_delay_seconds'] = settings['batch_delay_seconds']
            if 'include_unsubscribe' in settings:
                # Store in segment_filters or handle as needed
                if not validated_data.get('segment_filters'):
                    validated_data['segment_filters'] = {}
                validated_data['segment_filters']['include_unsubscribe'] = settings['include_unsubscribe']
        return validated_data
    
    def _populate_from_template_and_provider(self, validated_data):
        """Populate missing fields from email template and provider config."""
        email_template = validated_data.get('email_template')
        email_provider = validated_data.get('email_provider')
        
        # Get provider config for fallback
        provider_from_name, provider_from_email = self._get_provider_config(email_provider)
        template_from_name = getattr(email_template, 'default_from_name', None)
        template_from_email = getattr(email_template, 'default_from_email', None)
        template_reply_to = getattr(email_template, 'default_reply_to', None)
        
        # Populate HTML content if not provided (from template)
        if not validated_data.get('html_content') and email_template:
            validated_data['html_content'] = email_template.email_body
        
        # Populate text content if not provided (from template)
        if not validated_data.get('text_content') and email_template:
            validated_data['text_content'] = email_template.text_body or ''
        
        # Populate subject if not provided (from template)
        if not validated_data.get('subject') and email_template:
            validated_data['subject'] = email_template.email_subject
        
        # Populate preview text if not provided (from template)
        if not validated_data.get('preview_text') and email_template:
            validated_data['preview_text'] = email_template.preview_text or ''
        
        # Populate from_name if not provided (template > provider)
        if not validated_data.get('from_name'):
            if template_from_name:
                validated_data['from_name'] = template_from_name
            elif provider_from_name:
                validated_data['from_name'] = provider_from_name
        
        # Populate from_email if not provided (template > provider)
        if not validated_data.get('from_email'):
            if template_from_email:
                validated_data['from_email'] = template_from_email
            elif provider_from_email:
                validated_data['from_email'] = provider_from_email
        
        # Populate reply_to if not provided (from template)
        if not validated_data.get('reply_to') and template_reply_to is not None:
            validated_data['reply_to'] = template_reply_to or ''
        
        return validated_data
    
    def create(self, validated_data):
        contact_list_ids = validated_data.pop('contact_list_ids', [])
        validated_data.pop('email_variables', None)  # Handle separately if needed
        
        # Apply settings
        validated_data = self._apply_settings(validated_data)
        
        # Populate from template and provider
        validated_data = self._populate_from_template_and_provider(validated_data)
        
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
        validated_data.pop('email_variables', None)  # Handle separately if needed
        
        # Apply settings
        validated_data = self._apply_settings(validated_data)
        
        # Populate from template and provider if template or provider is being set/changed
        if 'email_template' in validated_data or 'email_provider' in validated_data:
            validated_data = self._populate_from_template_and_provider(validated_data)
        
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
