"""
Org-facing API for sending domains and sender email addresses.

All endpoints are scoped to request.user.organization and gated by
IsOrganizationAdmin; package limits and feature toggles are enforced in
services.domain_service so the platform-admin on-behalf endpoints share the
exact same validation.
"""
import logging

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.authentication.permissions import IsOrganizationAdmin
from apps.utils.view_mixins import ResponseMixin
from ..models import SenderEmail, SendingDomain
from ..serializers.domain_serializers import (
    SenderEmailCreateSerializer,
    SenderEmailSerializer,
    SendingDomainCreateSerializer,
    SendingDomainSerializer,
)
from ..services import domain_service
from ..utils.ses_identity_service import SESIdentityError

logger = logging.getLogger(__name__)


class OrganizationScopedView(ResponseMixin, APIView):
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    @property
    def organization(self):
        return self.request.user.organization


# ---------------------------------------------------------------------------
# Domains
# ---------------------------------------------------------------------------

class SendingDomainListCreateView(OrganizationScopedView):
    """GET /campaigns/domains/  |  POST /campaigns/domains/"""

    def get(self, request):
        domains = SendingDomain.objects.filter(organization=self.organization)
        config = domain_service.get_org_config(self.organization)
        return self.success(data={
            'domains': SendingDomainSerializer(domains, many=True).data,
            'limits': {
                'max_domains': config.max_domains,
                'used': domains.count(),
                'feature_enabled': config.domain_feature_enabled,
                'custom_domain_allowed': config.is_custom_domain_allowed,
                'org_owned_ses_allowed': config.is_org_owned_ses_allowed,
            },
        })

    def post(self, request):
        serializer = SendingDomainCreateSerializer(
            data=request.data, context={'organization': self.organization}
        )
        if not serializer.is_valid():
            return self.error(message="Invalid domain data", errors=serializer.errors)
        data = serializer.validated_data
        try:
            domain = domain_service.register_domain(
                organization=self.organization,
                domain_name=data['domain'],
                ownership_mode=data['ownership_mode'],
                provider=data.get('provider'),
                mail_from_subdomain=data.get('mail_from_subdomain') or 'mail',
                actor=request.user,
            )
        except ValidationError as exc:
            return self.error(message='; '.join(exc.messages))
        return self.success(
            data=SendingDomainSerializer(domain).data,
            message="Domain registered. Add the DNS records to complete verification.",
            status_code=status.HTTP_201_CREATED,
        )


class SendingDomainDetailView(OrganizationScopedView):
    """GET/DELETE /campaigns/domains/<uuid:pk>/"""

    def get_object(self, pk):
        return get_object_or_404(SendingDomain, pk=pk, organization=self.organization)

    def get(self, request, pk):
        return self.success(data=SendingDomainSerializer(self.get_object(pk)).data)

    def delete(self, request, pk):
        domain = self.get_object(pk)
        domain_service.delete_domain(domain, actor=request.user)
        return self.success(message=f"Domain {domain.domain} deleted")


class SendingDomainDNSRecordsView(OrganizationScopedView):
    """GET /campaigns/domains/<uuid:pk>/dns-records/"""

    def get(self, request, pk):
        domain = get_object_or_404(SendingDomain, pk=pk, organization=self.organization)
        return self.success(data={
            'domain': domain.domain,
            'status': domain.status,
            'dns_records': domain.dns_records,
        })


class SendingDomainVerifyNowView(OrganizationScopedView):
    """POST /campaigns/domains/<uuid:pk>/verify/ — manual 'check now' (throttled)."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'domain_verify'

    def post(self, request, pk):
        domain = get_object_or_404(SendingDomain, pk=pk, organization=self.organization)
        if domain.status == SendingDomain.STATUS_SUSPENDED:
            return self.error(
                message="This domain is suspended by the platform.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        try:
            verified, detail = domain_service.retry_domain_verification(domain, actor=request.user)
        except SESIdentityError as exc:
            return self.error(
                message=f"Verification check failed: {exc}",
                status_code=status.HTTP_502_BAD_GATEWAY,
            )
        return self.success(data={
            'domain': SendingDomainSerializer(domain).data,
            'verified': verified,
            'detail': detail,
        })


# ---------------------------------------------------------------------------
# Sender emails
# ---------------------------------------------------------------------------

class SenderEmailListCreateView(OrganizationScopedView):
    """GET /campaigns/sender-emails/  |  POST /campaigns/sender-emails/"""

    def get(self, request):
        senders = SenderEmail.objects.filter(organization=self.organization)
        domain_id = request.query_params.get('domain')
        if domain_id:
            senders = senders.filter(domain_id=domain_id)
        config = domain_service.get_org_config(self.organization)
        return self.success(data={
            'sender_emails': SenderEmailSerializer(senders, many=True).data,
            'limits': {
                'max_sender_emails': config.max_sender_emails,
                'used': SenderEmail.objects.filter(organization=self.organization).count(),
            },
        })

    def post(self, request):
        serializer = SenderEmailCreateSerializer(
            data=request.data, context={'organization': self.organization}
        )
        if not serializer.is_valid():
            return self.error(message="Invalid sender email data", errors=serializer.errors)
        data = serializer.validated_data
        try:
            sender = domain_service.create_sender_email(
                organization=self.organization,
                domain=serializer.context['domain'],
                local_part=data['local_part'],
                display_name=data.get('display_name', ''),
                actor=request.user,
            )
        except ValidationError as exc:
            return self.error(message='; '.join(exc.messages))
        return self.success(
            data=SenderEmailSerializer(sender).data,
            message=f"Sender email {sender.email_address} created",
            status_code=status.HTTP_201_CREATED,
        )


class SenderEmailDetailView(OrganizationScopedView):
    """GET/PATCH/DELETE /campaigns/sender-emails/<uuid:pk>/"""

    def get_object(self, pk):
        return get_object_or_404(SenderEmail, pk=pk, organization=self.organization)

    def get(self, request, pk):
        return self.success(data=SenderEmailSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        sender = self.get_object(pk)
        serializer = SenderEmailSerializer(sender, data=request.data, partial=True)
        if not serializer.is_valid():
            return self.error(message="Invalid data", errors=serializer.errors)
        serializer.save()
        return self.success(data=serializer.data, message="Sender email updated")

    def delete(self, request, pk):
        sender = self.get_object(pk)
        domain_service.delete_sender_email(sender, actor=request.user)
        return self.success(message=f"Sender email {sender.email_address} deleted")
