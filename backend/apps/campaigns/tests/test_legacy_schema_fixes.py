"""
Regression tests for code paths that were written against a removed schema
(tenant_id / activated_by_root / activated_by_tmd / is_global / rule_scope /
product_id / log_scope) and therefore raised FieldError or AttributeError at
runtime, plus the cross-tenant settings race in the SES backend resolver.
"""
import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.authentication.models import Organization
from apps.campaigns.backends import ProviderBackendResolver
from apps.campaigns.models import (
    AutomationRule,
    EmailDeliveryLog,
    EmailProvider,
    EmailQueue,
    EmailTemplate,
    OrganizationEmailConfiguration,
)
from apps.campaigns.tasks import process_email_queue_item
from apps.campaigns.utils.hierarchy_resolver import (
    HierarchicalResolver,
    is_email_service_active,
)
from apps.campaigns.utils.sync_utils import (
    ConfigurationHierarchy,
    ConfigurationValidator,
    RateLimitChecker,
)

User = get_user_model()


def make_organization(name='Acme'):
    email = f'owner@{name.lower()}.test'
    owner = User.objects.create_user(username=email, email=email, password='x')
    return Organization.objects.create(name=name, slug=name.lower(), owner=owner)


class EmailQueuePathTests(TestCase):
    """The queue path previously died on queue_item.tenant_id / .campaigns."""

    def setUp(self):
        self.organization = make_organization('Acme')
        self.template = EmailTemplate.objects.create(
            template_name='Welcome',
            organization=self.organization,
            category=EmailTemplate.TemplateCategory.OTHER,
            email_subject='Hi',
            email_body='<p>Hi</p>',
        )
        self.rule = AutomationRule.objects.create(
            automation_name='Welcome',
            organization=self.organization,
            email_template=self.template,
            reason_name=AutomationRule.ReasonName.OTHER,
            trigger_type=AutomationRule.TriggerType.IMMEDIATE,
        )
        self.provider = EmailProvider.objects.create(
            name='Shared SES',
            provider_type='AWS_SES',
            is_shared=True,
            is_default=True,
            encrypted_config=json.dumps({'from_email': 'noreply@example.com'}),
        )

    def _queue_item(self):
        return EmailQueue.objects.create(
            automation_rule=self.rule,
            organization=self.organization,
            recipient_email='recipient@example.com',
            subject='Hi',
            html_content='<p>Hi</p>',
            text_content='Hi',
            context_data={},
            headers={},
            status='PENDING',
            priority=1,
            scheduled_at=timezone.now(),
        )

    @patch('apps.campaigns.utils.email_providers.EmailProviderFactory.create_provider')
    def test_process_queue_item_sends_and_logs(self, mock_create_provider):
        provider_instance = MagicMock()
        provider_instance.send_email.return_value = (
            True, 'ses-message-1', {'provider_name': 'Shared SES'}
        )
        mock_create_provider.return_value = provider_instance

        queue_item = self._queue_item()
        result = process_email_queue_item(queue_item)

        self.assertTrue(result['success'], result)
        queue_item.refresh_from_db()
        self.assertEqual(queue_item.status, 'SENT')

        log = EmailDeliveryLog.objects.get(queue_item=queue_item)
        self.assertEqual(log.organization, self.organization)
        self.assertEqual(log.delivery_status, 'SENT')
        self.assertEqual(log.provider_message_id, 'ses-message-1')
        self.assertEqual(log.recipient_email, 'recipient@example.com')

    @patch('apps.campaigns.utils.email_providers.EmailProviderFactory.create_provider')
    def test_process_queue_item_records_failure(self, mock_create_provider):
        provider_instance = MagicMock()
        provider_instance.send_email.return_value = (
            False, '', {'error_message': 'rejected', 'error_code': 'BAD'}
        )
        mock_create_provider.return_value = provider_instance

        queue_item = self._queue_item()
        result = process_email_queue_item(queue_item)

        self.assertFalse(result['success'])
        queue_item.refresh_from_db()
        self.assertEqual(queue_item.status, 'FAILED')
        log = EmailDeliveryLog.objects.get(queue_item=queue_item)
        self.assertEqual(log.delivery_status, 'FAILED')

    @patch('apps.campaigns.utils.email_providers.EmailProviderFactory.create_provider')
    def test_preferred_provider_is_used_first(self, mock_create_provider):
        preferred = EmailProvider.objects.create(
            name='Preferred SES',
            provider_type='AWS_SES',
            is_shared=True,
            encrypted_config=json.dumps({'from_email': 'preferred@example.com'}),
        )
        provider_instance = MagicMock()
        provider_instance.send_email.return_value = (True, 'msg', {})
        mock_create_provider.return_value = provider_instance

        queue_item = self._queue_item()
        queue_item.context_data = {'preferred_provider_id': str(preferred.id)}
        queue_item.save(update_fields=['context_data'])

        result = process_email_queue_item(queue_item)

        self.assertTrue(result['success'], result)
        log = EmailDeliveryLog.objects.get(queue_item=queue_item)
        self.assertEqual(log.email_provider_id, preferred.id)


class SyncUtilsSchemaTests(TestCase):
    """These helpers previously queried fields that do not exist."""

    def setUp(self):
        self.organization = make_organization('Acme')
        self.config = OrganizationEmailConfiguration.objects.get(
            organization=self.organization
        )

    def test_rate_limit_checker_reads_organization_config(self):
        can_send, reason = RateLimitChecker.can_send_email(
            organization_id=self.organization.id
        )
        self.assertTrue(can_send, reason)

        self.config.is_suspended = True
        self.config.save()
        can_send, reason = RateLimitChecker.can_send_email(
            organization_id=self.organization.id
        )
        self.assertFalse(can_send)
        self.assertIn('Organization', reason)

    def test_increment_usage_counters_updates_config(self):
        RateLimitChecker.increment_usage_counters(organization_id=self.organization.id)
        self.config.refresh_from_db()
        self.assertEqual(self.config.emails_sent_today, 1)
        self.assertEqual(self.config.emails_sent_this_month, 1)

    def test_effective_rate_limits_merge(self):
        provider = EmailProvider.objects.create(
            name='Shared', provider_type='AWS_SES', is_shared=True,
            max_emails_per_minute=5, max_emails_per_hour=50, max_emails_per_day=500,
            encrypted_config='{}',
        )
        limits = ConfigurationHierarchy.get_effective_rate_limits(
            organization_id=self.organization.id, provider=provider
        )
        # Most restrictive of provider vs organization config wins
        self.assertEqual(limits['emails_per_minute'], 5)
        self.assertEqual(limits['emails_per_hour'], 50)

    def test_from_email_prefers_registered_sender_email(self):
        from apps.campaigns.models import SenderEmail, SendingDomain

        domain = SendingDomain.objects.create(
            organization=self.organization,
            domain='acme-mail.test',
            status=SendingDomain.STATUS_VERIFIED,
        )
        SenderEmail.objects.create(
            organization=self.organization,
            domain=domain,
            local_part='support',
            email_address='support@acme-mail.test',
        )

        resolved = ConfigurationHierarchy.get_effective_from_email(
            organization_id=self.organization.id,
            provider_config={'from_email': 'provider@example.com'},
        )
        self.assertEqual(resolved, 'support@acme-mail.test')

    @override_settings(DEFAULT_FROM_EMAIL='fallback@example.com')
    def test_from_email_falls_back_to_settings_not_hardcoded_domain(self):
        resolved = ConfigurationHierarchy.get_effective_from_email(
            organization_id=self.organization.id
        )
        self.assertEqual(resolved, 'fallback@example.com')

    def test_validator_runs_against_real_schema(self):
        result = ConfigurationValidator.validate_tenant_configuration(self.organization.id)
        self.assertEqual(result['organization_id'], str(self.organization.id))
        self.assertTrue(result['info']['organization_config']['exists'])


class HierarchicalResolverTests(TestCase):
    def setUp(self):
        self.organization = make_organization('Acme')

    def test_template_resolution_prefers_organization_then_global(self):
        global_template = EmailTemplate.objects.create(
            template_name='Global Welcome',
            is_global=True,
            category=EmailTemplate.TemplateCategory.OTHER,
            email_subject='Hi',
            email_body='<p>Hi</p>',
        )
        found = HierarchicalResolver.get_email_template(
            category=EmailTemplate.TemplateCategory.OTHER,
            organization_id=self.organization.id,
        )
        self.assertEqual(found, global_template)

        org_template = EmailTemplate.objects.create(
            template_name='Org Welcome',
            organization=self.organization,
            category=EmailTemplate.TemplateCategory.OTHER,
            email_subject='Hi',
            email_body='<p>Hi</p>',
        )
        found = HierarchicalResolver.get_email_template(
            category=EmailTemplate.TemplateCategory.OTHER,
            organization_id=self.organization.id,
        )
        self.assertEqual(found, org_template)

    def test_automation_rule_lookup_is_organization_scoped(self):
        template = EmailTemplate.objects.create(
            template_name='T', organization=self.organization,
            category=EmailTemplate.TemplateCategory.OTHER,
            email_subject='s', email_body='b',
        )
        rule = AutomationRule.objects.create(
            automation_name='Welcome',
            organization=self.organization,
            email_template=template,
            reason_name=AutomationRule.ReasonName.OTHER,
            trigger_type=AutomationRule.TriggerType.IMMEDIATE,
        )
        found = HierarchicalResolver.get_automation_rule(
            reason_name=AutomationRule.ReasonName.OTHER,
            organization_id=self.organization.id,
        )
        self.assertEqual(found, rule)

        # Another organization must not see it
        other = make_organization('Rival')
        self.assertIsNone(
            HierarchicalResolver.get_automation_rule(
                reason_name=AutomationRule.ReasonName.OTHER,
                organization_id=other.id,
            )
        )

    def test_email_service_active_respects_suspension(self):
        config = OrganizationEmailConfiguration.objects.get(
            organization=self.organization
        )
        self.assertTrue(is_email_service_active(organization_id=self.organization.id))

        config.is_suspended = True
        config.save()
        self.assertFalse(is_email_service_active(organization_id=self.organization.id))


class SESBackendIsolationTests(TestCase):
    """The resolver must not mutate process-wide settings (cross-tenant race)."""

    def test_resolve_does_not_mutate_global_settings(self):
        from django.conf import settings as django_settings
        from django_ses import settings as django_ses_settings

        before = (
            getattr(django_ses_settings, 'AWS_SES_REGION_NAME', None),
            getattr(django_ses_settings, 'AWS_SES_REGION_ENDPOINT_URL', None),
            getattr(django_settings, 'AWS_SES_FROM_EMAIL', None),
        )

        ProviderBackendResolver.resolve("AWS_SES", {
            'aws_access_key_id': 'A', 'aws_secret_access_key': 'S',
            'region_name': 'eu-west-1', 'from_email': 'a@example.com',
        })
        ProviderBackendResolver.resolve("AWS_SES", {
            'aws_access_key_id': 'B', 'aws_secret_access_key': 'S2',
            'region_name': 'us-west-2', 'from_email': 'b@example.com',
        })

        after = (
            getattr(django_ses_settings, 'AWS_SES_REGION_NAME', None),
            getattr(django_ses_settings, 'AWS_SES_REGION_ENDPOINT_URL', None),
            getattr(django_settings, 'AWS_SES_FROM_EMAIL', None),
        )
        self.assertEqual(before, after)

    def test_per_provider_region_is_passed_as_kwargs(self):
        _, kwargs_a, meta_a = ProviderBackendResolver.resolve("AWS_SES", {
            'aws_access_key_id': 'A', 'aws_secret_access_key': 'S',
            'region_name': 'eu-west-1', 'from_email': 'a@example.com',
            'return_path': 'bounce@example.com',
        })
        _, kwargs_b, meta_b = ProviderBackendResolver.resolve("AWS_SES", {
            'aws_access_key_id': 'B', 'aws_secret_access_key': 'S2',
            'region_name': 'us-west-2',
        })

        self.assertEqual(kwargs_a['aws_region_name'], 'eu-west-1')
        self.assertEqual(kwargs_b['aws_region_name'], 'us-west-2')
        # Endpoint is always fully resolved so the backend never reads globals
        self.assertEqual(kwargs_a['aws_region_endpoint'], 'https://email.eu-west-1.amazonaws.com')
        self.assertEqual(kwargs_b['aws_region_endpoint'], 'https://email.us-west-2.amazonaws.com')
        self.assertEqual(meta_a['from_email'], 'a@example.com')
        self.assertEqual(meta_a['return_path'], 'bounce@example.com')
