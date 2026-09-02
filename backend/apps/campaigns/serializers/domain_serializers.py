"""
Serializers for sending domains, sender emails and packages.

Never serialize provider credentials. DKIM tokens / DNS record values are
public DNS data and safe to expose to the owning organization.
"""
from rest_framework import serializers

from ..models import EmailProvider, Package, SenderEmail, SendingDomain


class PackageSerializer(serializers.ModelSerializer):
    """Full package representation (platform admin CRUD + org-facing read)."""

    organization_count = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = [
            'id', 'name', 'display_name', 'description', 'is_default', 'is_active',
            'sort_order',
            'contacts_limit', 'campaigns_per_month', 'emails_per_day',
            'emails_per_month', 'emails_per_minute', 'batch_size',
            'api_requests_per_minute', 'max_domains', 'max_sender_emails',
            'custom_domain_allowed', 'advanced_analytics', 'priority_support',
            'bulk_email_allowed', 'ab_testing_allowed', 'org_owned_ses_allowed',
            'organization_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'organization_count']

    def get_organization_count(self, obj):
        return getattr(obj, 'organization_count', None)


class SendingDomainSerializer(serializers.ModelSerializer):
    """Read serializer for sending domains."""

    sender_email_count = serializers.SerializerMethodField()
    is_usable = serializers.BooleanField(read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = SendingDomain
        fields = [
            'id', 'organization', 'organization_name', 'domain', 'ownership_mode',
            'region', 'status', 'dns_records', 'mail_from_subdomain',
            'mail_from_status', 'verified_at', 'last_checked_at',
            'verification_error', 'suspension_reason', 'legacy', 'is_usable',
            'sender_email_count', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_sender_email_count(self, obj):
        return obj.sender_emails.count()


class SendingDomainCreateSerializer(serializers.Serializer):
    """Input for registering a new sending domain."""

    domain = serializers.CharField(max_length=253)
    ownership_mode = serializers.ChoiceField(
        choices=SendingDomain.OWNERSHIP_CHOICES,
        default=SendingDomain.OWNERSHIP_PLATFORM,
    )
    provider_id = serializers.UUIDField(required=False, allow_null=True)
    mail_from_subdomain = serializers.CharField(
        max_length=63, required=False, default='mail'
    )

    def validate(self, attrs):
        if attrs.get('ownership_mode') == SendingDomain.OWNERSHIP_ORG:
            provider_id = attrs.get('provider_id')
            if not provider_id:
                raise serializers.ValidationError(
                    {'provider_id': 'Required for org-owned SES domains.'}
                )
            organization = self.context['organization']
            try:
                attrs['provider'] = EmailProvider.objects.get(
                    pk=provider_id,
                    organization=organization,
                    provider_type='AWS_SES',
                )
            except EmailProvider.DoesNotExist:
                raise serializers.ValidationError(
                    {'provider_id': 'No AWS SES provider with this id belongs to your organization.'}
                )
        else:
            attrs['provider'] = None
        return attrs


class SenderEmailSerializer(serializers.ModelSerializer):
    """Read serializer for sender emails."""

    domain_name = serializers.CharField(source='domain.domain', read_only=True)
    receiving_supported = serializers.SerializerMethodField()
    is_usable = serializers.BooleanField(read_only=True)

    class Meta:
        model = SenderEmail
        fields = [
            'id', 'organization', 'domain', 'domain_name', 'local_part',
            'email_address', 'display_name', 'status', 'suspension_reason',
            'mailbox_account', 'receiving_supported', 'is_usable',
            'created_at', 'updated_at',
        ]
        read_only_fields = [f for f in fields if f != 'display_name']

    def get_receiving_supported(self, obj):
        # v1: inbound receiving works only for platform-managed domains
        return obj.domain.ownership_mode == SendingDomain.OWNERSHIP_PLATFORM


class SenderEmailCreateSerializer(serializers.Serializer):
    """Input for creating a sender email under a verified domain."""

    domain_id = serializers.UUIDField()
    local_part = serializers.CharField(max_length=64)
    display_name = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')

    def validate_domain_id(self, value):
        organization = self.context['organization']
        try:
            self.context['domain'] = SendingDomain.objects.get(
                pk=value, organization=organization
            )
        except SendingDomain.DoesNotExist:
            raise serializers.ValidationError('No such domain in your organization.')
        return value
