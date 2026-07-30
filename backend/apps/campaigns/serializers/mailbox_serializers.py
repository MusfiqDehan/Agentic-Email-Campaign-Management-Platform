"""Serializers for mailbox accounts and messages."""
from rest_framework import serializers

from apps.campaigns.models import EmailAccount, MailboxMessage
from apps.campaigns.utils.email_providers import EmailProviderFactory, SMTPProvider


class EmailAccountSerializer(serializers.ModelSerializer):
    config = serializers.DictField(write_only=True, required=False)
    config_summary = serializers.SerializerMethodField(read_only=True)
    unread_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EmailAccount
        fields = [
            'id', 'name', 'email_address', 'account_type', 'display_name',
            'email_provider', 'sync_enabled', 'sync_status', 'last_synced_at',
            'last_sync_error', 'is_default', 'is_active', 'config',
            'config_summary', 'unread_count', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'sync_status', 'last_synced_at', 'last_sync_error',
            'created_at', 'updated_at', 'config_summary', 'unread_count',
        ]

    def get_config_summary(self, obj):
        try:
            cfg = obj.decrypt_config()
        except Exception:
            return {}
        # Never expose secrets
        safe_keys = [
            'smtp_server', 'smtp_port', 'imap_server', 'imap_port',
            'use_tls', 'use_ssl', 'region', 'region_name', 'from_email',
            'default_from_email', 'configuration_set', 'username',
        ]
        return {k: cfg[k] for k in safe_keys if k in cfg}

    def get_unread_count(self, obj):
        return obj.messages.filter(
            folder='INBOX', direction='INBOUND', is_read=False, is_deleted=False
        ).count()

    def _normalize_config(self, account_type, email_address, config):
        config = dict(config or {})
        if account_type == 'GMAIL':
            config.setdefault('smtp_server', 'smtp.gmail.com')
            config.setdefault('smtp_port', 587)
            config.setdefault('use_tls', True)
            config.setdefault('use_ssl', False)
            config.setdefault('imap_server', 'imap.gmail.com')
            config.setdefault('imap_port', 993)
            config.setdefault('username', email_address)
            config.setdefault('imap_username', email_address)
            config.setdefault('from_email', email_address)
            # Prefer app_password field
            if config.get('app_password') and not config.get('password'):
                config['password'] = config['app_password']
            if config.get('password') and not config.get('imap_password'):
                config['imap_password'] = config['password']
        elif account_type == 'AWS_SES':
            config.setdefault('from_email', email_address)
            config.setdefault('default_from_email', email_address)
        else:
            config.setdefault('from_email', email_address)
            config.setdefault('username', email_address)
        return config

    def validate(self, attrs):
        account_type = attrs.get('account_type') or getattr(self.instance, 'account_type', None)
        email_address = attrs.get('email_address') or getattr(self.instance, 'email_address', None)
        config = attrs.get('config')
        if config is not None and account_type and email_address:
            attrs['config'] = self._normalize_config(account_type, email_address, config)
        return attrs

    def create(self, validated_data):
        config = validated_data.pop('config', {})
        org = self.context['organization']
        account = EmailAccount(organization=org, **validated_data)
        account.encrypt_config(config)
        account.save()
        return account

    def update(self, instance, validated_data):
        config = validated_data.pop('config', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if config is not None:
            # Merge with existing so partial updates don't wipe secrets
            try:
                existing = instance.decrypt_config()
            except Exception:
                existing = {}
            existing.update({k: v for k, v in config.items() if v not in (None, '')})
            instance.encrypt_config(existing)
        instance.save()
        return instance


class MailboxMessageListSerializer(serializers.ModelSerializer):
    account_email = serializers.EmailField(source='account.email_address', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = MailboxMessage
        fields = [
            'id', 'account', 'account_email', 'account_name', 'direction', 'folder',
            'from_address', 'from_name', 'to_addresses', 'cc_addresses',
            'subject', 'snippet', 'is_read', 'is_starred', 'is_draft',
            'sent_at', 'received_at', 'thread_key', 'has_attachments',
            'created_at',
        ]

    has_attachments = serializers.SerializerMethodField()

    def get_has_attachments(self, obj):
        return bool(obj.attachments_meta)


class MailboxMessageDetailSerializer(serializers.ModelSerializer):
    account_email = serializers.EmailField(source='account.email_address', read_only=True)

    class Meta:
        model = MailboxMessage
        fields = [
            'id', 'account', 'account_email', 'direction', 'folder',
            'message_id', 'in_reply_to', 'references', 'thread_key',
            'from_address', 'from_name', 'to_addresses', 'cc_addresses',
            'bcc_addresses', 'reply_to', 'subject', 'text_body', 'html_body',
            'snippet', 'attachments_meta', 'is_read', 'is_starred', 'is_draft',
            'sent_at', 'received_at', 'parent_message', 'delivery_log',
            'provider_message_id', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'message_id', 'provider_message_id', 'delivery_log',
            'created_at', 'updated_at',
        ]


class ComposeMessageSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    to = serializers.ListField(child=serializers.EmailField(), min_length=1)
    cc = serializers.ListField(child=serializers.EmailField(), required=False, default=list)
    bcc = serializers.ListField(child=serializers.EmailField(), required=False, default=list)
    subject = serializers.CharField(max_length=998)
    text_body = serializers.CharField(required=False, allow_blank=True, default='')
    html_body = serializers.CharField(required=False, allow_blank=True, default='')
    reply_to_message_id = serializers.UUIDField(required=False, allow_null=True)
    track_opens = serializers.BooleanField(default=False)
    track_clicks = serializers.BooleanField(default=False)


class MailboxMessageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailboxMessage
        fields = ['is_read', 'is_starred', 'folder']
