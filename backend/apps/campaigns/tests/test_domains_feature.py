"""
Tests for the multi-domain / multi-sender-email feature: packages and
effective limits, domain + sender-email lifecycle, send-path enforcement,
org isolation, and the platform-admin control API.

SES calls are mocked at the domain_service.SESIdentityService seam.
"""
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.authentication.models import Organization, OrganizationMembership
from apps.campaigns.models import (
    EmailAccount,
    OrganizationEmailConfiguration,
    Package,
    SenderEmail,
    SendingDomain,
)
from apps.campaigns.services import domain_service
from apps.campaigns.utils.sender_validation import validate_sender

User = get_user_model()

SERVICE_PATH = 'apps.campaigns.services.domain_service.SESIdentityService'


def make_org(name, plan_kwargs=None):
    email = f'owner@{name.lower()}.test'
    owner = User.objects.create_user(username=email, email=email, password='x')
    org = Organization.objects.create(name=name, slug=name.lower(), owner=owner)
    owner.organization = org
    owner.save(update_fields=['organization'])
    OrganizationMembership.objects.create(user=owner, organization=org, role='owner')

    package = Package.objects.create(
        name=f'{name.lower()}-pkg',
        display_name=f'{name} package',
        custom_domain_allowed=True,
        max_domains=2,
        max_sender_emails=3,
        emails_per_day=100,
        emails_per_month=1000,
        emails_per_minute=10,
        **(plan_kwargs or {}),
    )
    config = OrganizationEmailConfiguration.objects.create(organization=org, package=package)
    return org, owner, config


def mock_ses_service():
    """A mocked SESIdentityService instance factory."""
    instance = MagicMock()
    instance.create_identity.return_value = {}
    instance.get_verification_status.return_value = (True, {'dkim_status': 'SUCCESS'})
    instance.delete_identity.return_value = None
    return instance


class EffectiveLimitsTests(TestCase):
    def setUp(self):
        self.org, self.owner, self.config = make_org('Acme')

    def test_package_limits_flow_through(self):
        limits = self.config.get_effective_limits()
        self.assertEqual(limits['max_domains'], 2)
        self.assertTrue(limits['custom_domain_allowed'])

    def test_overrides_win_and_survive_save(self):
        self.config.limit_overrides = {'max_domains': 10, 'emails_per_day': 5}
        self.config.save()
        self.config.refresh_from_db()
        limits = self.config.get_effective_limits()
        self.assertEqual(limits['max_domains'], 10)
        # Denormalized field refreshed from effective limits
        self.assertEqual(self.config.emails_per_day, 5)
        # A later save must not clobber the override
        self.config.save()
        self.assertEqual(self.config.get_effective_limits()['max_domains'], 10)

    def test_unlimited_becomes_sentinel_on_denormalized_fields(self):
        self.config.package.emails_per_day = None
        self.config.package.save()
        self.config.save()
        self.assertEqual(
            self.config.emails_per_day, OrganizationEmailConfiguration.UNLIMITED_SENTINEL
        )

    def test_legacy_org_without_package_uses_plan_limits(self):
        self.config.package = None
        self.config.save()
        limits = self.config.get_effective_limits()
        self.assertIn('emails_per_day', limits)


@patch(SERVICE_PATH)
class DomainLifecycleTests(TestCase):
    def setUp(self):
        self.org, self.owner, self.config = make_org('Acme')

    def test_register_verify_and_sender_email_flow(self, service_cls):
        service_cls.return_value = mock_ses_service()

        domain = domain_service.register_domain(self.org, 'Example.COM.')
        self.assertEqual(domain.domain, 'example.com')
        self.assertEqual(domain.status, SendingDomain.STATUS_PENDING_VERIFICATION)

        verified, _ = domain_service.check_domain_verification(domain)
        self.assertTrue(verified)
        domain.refresh_from_db()
        self.assertEqual(domain.status, SendingDomain.STATUS_VERIFIED)
        self.assertIsNotNone(domain.verified_at)

        sender = domain_service.create_sender_email(self.org, domain, 'Support', 'Acme Support')
        self.assertEqual(sender.email_address, 'support@example.com')
        # Platform-managed domains get a linked mailbox account for receiving
        self.assertIsNotNone(sender.mailbox_account)
        self.assertEqual(sender.mailbox_account.account_type, 'AWS_SES')
        self.assertFalse(sender.mailbox_account.sync_enabled)

    def test_domain_limit_enforced(self, service_cls):
        service_cls.return_value = mock_ses_service()
        domain_service.register_domain(self.org, 'one.com')
        domain_service.register_domain(self.org, 'two.com')
        with self.assertRaises(ValidationError):
            domain_service.register_domain(self.org, 'three.com')

    def test_global_domain_uniqueness_across_orgs(self, service_cls):
        service_cls.return_value = mock_ses_service()
        other_org, _, _ = make_org('Rival')
        domain_service.register_domain(self.org, 'shared.com')
        with self.assertRaises(ValidationError):
            domain_service.register_domain(other_org, 'shared.com')

    def test_feature_kill_switch(self, service_cls):
        service_cls.return_value = mock_ses_service()
        self.config.domain_feature_enabled = False
        self.config.save()
        with self.assertRaises(ValidationError):
            domain_service.register_domain(self.org, 'blocked.com')

    def test_package_without_custom_domain_blocked(self, service_cls):
        service_cls.return_value = mock_ses_service()
        self.config.package.custom_domain_allowed = False
        self.config.package.save()
        with self.assertRaises(ValidationError):
            domain_service.register_domain(self.org, 'nope.com')

    def test_platform_admin_bypasses_package_domain_gate(self, service_cls):
        service_cls.return_value = mock_ses_service()
        self.config.package.custom_domain_allowed = False
        self.config.package.max_domains = 0
        self.config.package.save()
        self.owner.is_platform_admin = True
        self.owner.save(update_fields=['is_platform_admin'])
        domain = domain_service.register_domain(self.org, 'admin-ok.com', actor=self.owner)
        self.assertEqual(domain.domain, 'admin-ok.com')
        payload = domain_service.get_domain_limits_payload(self.config, user=self.owner)
        self.assertTrue(payload['custom_domain_allowed'])
        self.assertTrue(payload['feature_enabled'])
        self.assertIsNone(payload['max_domains'])

    def test_sender_email_requires_verified_domain(self, service_cls):
        service_cls.return_value = mock_ses_service()
        domain = domain_service.register_domain(self.org, 'pending.com')
        with self.assertRaises(ValidationError):
            domain_service.create_sender_email(self.org, domain, 'hello')

    def test_sender_email_limit_enforced(self, service_cls):
        service_cls.return_value = mock_ses_service()
        domain = domain_service.register_domain(self.org, 'verified.com')
        domain_service.check_domain_verification(domain)
        domain.refresh_from_db()
        for local in ('a', 'b', 'c'):
            domain_service.create_sender_email(self.org, domain, local)
        with self.assertRaises(ValidationError):
            domain_service.create_sender_email(self.org, domain, 'd')

    def test_delete_sender_email_deactivates_mailbox(self, service_cls):
        service_cls.return_value = mock_ses_service()
        domain = domain_service.register_domain(self.org, 'del.com')
        domain_service.check_domain_verification(domain)
        domain.refresh_from_db()
        sender = domain_service.create_sender_email(self.org, domain, 'gone')
        account_id = sender.mailbox_account_id
        domain_service.delete_sender_email(sender)
        self.assertFalse(SenderEmail.objects.filter(pk=sender.pk).exists())
        self.assertFalse(EmailAccount.all_objects.get(pk=account_id).is_active)
        # Address becomes reusable after soft delete
        recreated = domain_service.create_sender_email(self.org, domain, 'gone')
        self.assertEqual(recreated.email_address, 'gone@del.com')

    def test_delete_domain_suspends_children(self, service_cls):
        service_cls.return_value = mock_ses_service()
        domain = domain_service.register_domain(self.org, 'bye.com')
        domain_service.check_domain_verification(domain)
        domain.refresh_from_db()
        domain_service.create_sender_email(self.org, domain, 'x')
        domain_service.delete_domain(domain)
        self.assertFalse(SendingDomain.objects.filter(pk=domain.pk).exists())
        self.assertFalse(SenderEmail.objects.filter(domain=domain).exists())


@patch(SERVICE_PATH)
class SenderValidationTests(TestCase):
    def setUp(self):
        self.org, self.owner, self.config = make_org('Acme')

    def _verified_domain(self, service_cls, name='valid.com'):
        service_cls.return_value = mock_ses_service()
        domain = domain_service.register_domain(self.org, name)
        domain_service.check_domain_verification(domain)
        domain.refresh_from_db()
        return domain

    def test_unregistered_domain_is_grandfathered(self, service_cls):
        self.assertIsNone(validate_sender(self.org, 'anything@gmail.com'))

    def test_valid_sender_passes(self, service_cls):
        domain = self._verified_domain(service_cls)
        domain_service.create_sender_email(self.org, domain, 'ok')
        sender = validate_sender(self.org, 'Acme <ok@valid.com>')
        self.assertIsNotNone(sender)

    def test_unknown_address_on_registered_domain_rejected(self, service_cls):
        self._verified_domain(service_cls)
        with self.assertRaises(ValidationError):
            validate_sender(self.org, 'ghost@valid.com')

    def test_other_orgs_domain_rejected(self, service_cls):
        self._verified_domain(service_cls)
        other_org, _, _ = make_org('Rival')
        with self.assertRaises(ValidationError):
            validate_sender(other_org, 'spoof@valid.com')

    def test_suspended_domain_blocks_sending(self, service_cls):
        domain = self._verified_domain(service_cls)
        sender = domain_service.create_sender_email(self.org, domain, 'ok')
        domain_service.suspend_domain(domain, reason='abuse')
        with self.assertRaises(ValidationError):
            validate_sender(self.org, sender.email_address)
        domain_service.reactivate_domain(domain)
        self.assertIsNotNone(validate_sender(self.org, sender.email_address))

    def test_suspended_sender_email_blocks_sending(self, service_cls):
        domain = self._verified_domain(service_cls)
        sender = domain_service.create_sender_email(self.org, domain, 'ok')
        domain_service.suspend_sender_email(sender, reason='abuse')
        with self.assertRaises(ValidationError):
            validate_sender(self.org, sender.email_address)


class DomainAPITests(TestCase):
    def setUp(self):
        self.org, self.owner, self.config = make_org('Acme')
        self.other_org, self.other_owner, _ = make_org('Rival')
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    @patch(SERVICE_PATH)
    def test_create_and_list_domains(self, service_cls):
        service_cls.return_value = mock_ses_service()
        response = self.client.post(
            '/api/v1/campaigns/domains/', {'domain': 'api.com'}, format='json'
        )
        self.assertEqual(response.status_code, 201, response.content)

        response = self.client.get('/api/v1/campaigns/domains/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(len(data['domains']), 1)
        self.assertEqual(data['limits']['max_domains'], 2)

    @patch(SERVICE_PATH)
    def test_org_isolation(self, service_cls):
        service_cls.return_value = mock_ses_service()
        domain = domain_service.register_domain(self.other_org, 'theirs.com')

        # Other org's domain is invisible and unverifiable
        response = self.client.get(f'/api/v1/campaigns/domains/{domain.pk}/')
        self.assertEqual(response.status_code, 404)
        response = self.client.post(f'/api/v1/campaigns/domains/{domain.pk}/verify/')
        self.assertEqual(response.status_code, 404)

    @patch(SERVICE_PATH)
    def test_org_owned_mode_requires_package_flag(self, service_cls):
        service_cls.return_value = mock_ses_service()
        response = self.client.post(
            '/api/v1/campaigns/domains/',
            {'domain': 'own.com', 'ownership_mode': 'ORG', 'provider_id': None},
            format='json',
        )
        # provider_id required -> serializer error
        self.assertEqual(response.status_code, 400)

    def test_non_admin_member_cannot_manage_domains(self):
        email = 'member@acme.test'
        member = User.objects.create_user(username=email, email=email, password='x')
        member.organization = self.org
        member.save(update_fields=['organization'])
        OrganizationMembership.objects.create(user=member, organization=self.org, role='member')
        client = APIClient()
        client.force_authenticate(user=member)
        response = client.get('/api/v1/campaigns/domains/')
        self.assertEqual(response.status_code, 403)


class AdminAPITests(TestCase):
    def setUp(self):
        self.org, self.owner, self.config = make_org('Acme')
        admin_email = 'root@platform.test'
        self.admin = User.objects.create_user(
            username=admin_email, email=admin_email, password='x'
        )
        self.admin.is_platform_admin = True
        self.admin.save(update_fields=['is_platform_admin'])
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_non_platform_admin_gets_403_everywhere(self):
        client = APIClient()
        client.force_authenticate(user=self.owner)
        for url in (
            '/api/v1/campaigns/admin/packages/',
            '/api/v1/campaigns/admin/domains/',
            f'/api/v1/campaigns/admin/organizations/{self.org.pk}/limit-overrides/',
        ):
            response = client.get(url)
            self.assertEqual(response.status_code, 403, url)

    def test_package_crud(self):
        response = self.client.post('/api/v1/campaigns/admin/packages/', {
            'name': 'growth',
            'display_name': 'Growth',
            'max_domains': 5,
            'max_sender_emails': 20,
            'custom_domain_allowed': True,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        package_id = response.json()['data']['id']

        response = self.client.patch(
            f'/api/v1/campaigns/admin/packages/{package_id}/',
            {'max_domains': 7},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['max_domains'], 7)

        response = self.client.delete(f'/api/v1/campaigns/admin/packages/{package_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Package.all_objects.filter(pk=package_id).exists())

    def test_package_delete_blocked_when_assigned(self):
        package = self.config.package
        response = self.client.delete(f'/api/v1/campaigns/admin/packages/{package.pk}/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Package.objects.filter(pk=package.pk).exists())

    def test_assign_package_and_overrides(self):
        new_package = Package.objects.create(
            name='mega', display_name='Mega', max_domains=50, custom_domain_allowed=True
        )
        response = self.client.post(
            f'/api/v1/campaigns/admin/organizations/{self.org.pk}/assign-package/',
            {'package_id': str(new_package.pk)},
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.config.refresh_from_db()
        self.assertEqual(self.config.package, new_package)

        # Sparse override merge; null clears a key
        response = self.client.patch(
            f'/api/v1/campaigns/admin/organizations/{self.org.pk}/limit-overrides/',
            {'max_domains': 99},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['effective_limits']['max_domains'], 99)

        response = self.client.patch(
            f'/api/v1/campaigns/admin/organizations/{self.org.pk}/limit-overrides/',
            {'max_domains': None},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['effective_limits']['max_domains'], 50)

        # Unknown keys rejected
        response = self.client.patch(
            f'/api/v1/campaigns/admin/organizations/{self.org.pk}/limit-overrides/',
            {'not_a_real_limit': 1},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_domain_feature_toggle(self):
        response = self.client.post(
            f'/api/v1/campaigns/admin/organizations/{self.org.pk}/domain-feature/',
            {'enabled': False},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.config.refresh_from_db()
        self.assertFalse(self.config.domain_feature_enabled)

    @patch(SERVICE_PATH)
    def test_admin_suspend_and_reactivate_domain(self, service_cls):
        service_cls.return_value = mock_ses_service()
        domain = domain_service.register_domain(self.org, 'suspend-me.com')
        domain_service.check_domain_verification(domain)
        domain.refresh_from_db()

        response = self.client.post(
            f'/api/v1/campaigns/admin/domains/{domain.pk}/suspend/',
            {'reason': 'spam'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        domain.refresh_from_db()
        self.assertEqual(domain.status, SendingDomain.STATUS_SUSPENDED)

        response = self.client.post(f'/api/v1/campaigns/admin/domains/{domain.pk}/reactivate/')
        self.assertEqual(response.status_code, 200)
        domain.refresh_from_db()
        self.assertEqual(domain.status, SendingDomain.STATUS_VERIFIED)

    @patch(SERVICE_PATH)
    def test_admin_on_behalf_creation(self, service_cls):
        service_cls.return_value = mock_ses_service()
        response = self.client.post(
            f'/api/v1/campaigns/admin/organizations/{self.org.pk}/domains/',
            {'domain': 'concierge.com'},
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.content)
        domain = SendingDomain.objects.get(domain='concierge.com')
        self.assertEqual(domain.organization, self.org)

        domain_service.check_domain_verification(domain)
        response = self.client.post(
            f'/api/v1/campaigns/admin/organizations/{self.org.pk}/sender-emails/',
            {'domain_id': str(domain.pk), 'local_part': 'vip'},
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(
            SenderEmail.objects.filter(email_address='vip@concierge.com', organization=self.org).exists()
        )

        # On-behalf creation still respects org limits
        self.config.limit_overrides = {'max_domains': 1}
        self.config.save()
        response = self.client.post(
            f'/api/v1/campaigns/admin/organizations/{self.org.pk}/domains/',
            {'domain': 'over-limit.com'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)


class SESInboundRoutingTests(TestCase):
    """The domain-suffix fallback that could deliver one org's mail into
    another org's mailbox was removed — routing is exact-address only."""

    def setUp(self):
        self.org, self.owner, self.config = make_org('Acme')
        self.other_org, _, _ = make_org('Rival')

    def _handler(self, destination):
        from apps.campaigns.services.ses_inbound import SESInboundHandler

        handler = SESInboundHandler.__new__(SESInboundHandler)
        handler.email = {
            'to': destination,
            'subject': 'Hello',
            'plain_text': 'body',
            'html_text': '',
            'message_id': '<m1@test>',
            'date': None,
            'attachments': [],
        }
        handler.mail_obj = {
            'destination': destination,
            'source': 'sender@outside.test',
            'messageId': 'ses-1',
            'commonHeaders': {'from': ['sender@outside.test'], 'subject': 'Hello'},
        }
        return handler

    def test_unknown_recipient_is_dropped_not_cross_delivered(self):
        from apps.campaigns.models import MailboxMessage

        EmailAccount.objects.create(
            organization=self.other_org,
            name='rival inbox',
            email_address='sales@shared-domain.com',
            account_type='AWS_SES',
            encrypted_config='',
        )
        # Same domain, different local part -> must NOT land in the rival's inbox
        self._handler(['support@shared-domain.com']).process()
        self.assertEqual(MailboxMessage.objects.count(), 0)

    def test_exact_address_is_delivered(self):
        from apps.campaigns.models import MailboxMessage

        EmailAccount.objects.create(
            organization=self.org,
            name='inbox',
            email_address='support@acme-domain.com',
            account_type='AWS_SES',
            encrypted_config='',
        )
        self._handler(['support@acme-domain.com']).process()
        message = MailboxMessage.objects.get()
        self.assertEqual(message.organization, self.org)
        self.assertEqual(message.direction, 'INBOUND')

    @patch(SERVICE_PATH)
    def test_sender_email_link_resolves_inbox(self, service_cls):
        """Addresses created through the domains feature route via their link."""
        from apps.campaigns.models import MailboxMessage

        service_cls.return_value = mock_ses_service()
        domain = domain_service.register_domain(self.org, 'linked.com')
        domain_service.check_domain_verification(domain)
        domain.refresh_from_db()
        sender = domain_service.create_sender_email(self.org, domain, 'hello')

        self._handler([sender.email_address]).process()
        message = MailboxMessage.objects.get()
        self.assertEqual(message.account_id, sender.mailbox_account_id)
