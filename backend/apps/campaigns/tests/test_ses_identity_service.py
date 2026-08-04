"""Tests for SESIdentityService (boto3 mocked at the _client seam)."""
import json
from unittest.mock import MagicMock

from botocore.exceptions import ClientError
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.authentication.models import Organization
from apps.campaigns.models import EmailProvider, SendingDomain
from apps.campaigns.utils.ses_identity_service import (
    SESIdentityError,
    SESIdentityService,
)

User = get_user_model()


def client_error(code, message='boom'):
    return ClientError({'Error': {'Code': code, 'Message': message}}, 'op')


@override_settings(
    AWS_ACCESS_KEY_ID='platform-key',
    AWS_SECRET_ACCESS_KEY='platform-secret',
    AWS_SES_REGION_NAME='eu-west-1',
)
class SESIdentityServiceTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user(username='o@x.test', email='o@x.test', password='x')
        self.org = Organization.objects.create(name='Org', slug='org', owner=owner)
        self.domain = SendingDomain.objects.create(
            organization=self.org,
            domain='example.com',
            ownership_mode=SendingDomain.OWNERSHIP_PLATFORM,
        )

    def test_platform_credential_resolution(self):
        service = SESIdentityService(self.domain)
        access, secret, region = service._resolve_credentials()
        self.assertEqual((access, secret, region), ('platform-key', 'platform-secret', 'eu-west-1'))

    def test_org_credential_resolution_decrypts_provider(self):
        provider = EmailProvider(
            name='org ses', provider_type='AWS_SES', organization=self.org
        )
        provider.encrypt_config({
            'aws_access_key': 'org-key',
            'aws_secret_key': 'org-secret',
            'aws_region_name': 'us-west-2',
        })
        provider.save()
        domain = SendingDomain.objects.create(
            organization=self.org,
            domain='org-owned.com',
            ownership_mode=SendingDomain.OWNERSHIP_ORG,
            provider=provider,
        )
        access, secret, region = SESIdentityService(domain)._resolve_credentials()
        self.assertEqual((access, secret, region), ('org-key', 'org-secret', 'us-west-2'))

    @override_settings(AWS_ACCESS_KEY_ID='', AWS_SECRET_ACCESS_KEY='')
    def test_missing_platform_credentials_raise(self):
        with self.assertRaises(SESIdentityError):
            SESIdentityService(self.domain)._resolve_credentials()

    def _service_with_mock_client(self, mock_client):
        service = SESIdentityService(self.domain)
        service._client_instance = mock_client
        return service

    def test_create_identity_stores_tokens_and_dns_records(self):
        mock = MagicMock()
        mock.get_email_identity.return_value = {
            'DkimAttributes': {'Tokens': ['t1', 't2', 't3'], 'Status': 'PENDING'},
        }
        service = self._service_with_mock_client(mock)
        service.create_identity()

        self.assertEqual(self.domain.dkim_tokens, ['t1', 't2', 't3'])
        types = [record['type'] for record in self.domain.dns_records]
        self.assertEqual(types.count('CNAME'), 3)
        # Platform-managed domains include the inbound MX record
        values = json.dumps(self.domain.dns_records)
        self.assertIn('inbound-smtp', values)
        self.assertIn('feedback-smtp', values)

    def test_create_identity_adopts_existing(self):
        mock = MagicMock()
        mock.create_email_identity.side_effect = client_error('AlreadyExistsException')
        mock.get_email_identity.return_value = {'DkimAttributes': {'Tokens': ['a']}}
        service = self._service_with_mock_client(mock)
        service.create_identity()  # must not raise
        self.assertEqual(self.domain.dkim_tokens, ['a'])

    def test_verification_status_mapping(self):
        mock = MagicMock()
        mock.get_email_identity.return_value = {
            'VerifiedForSendingStatus': True,
            'DkimAttributes': {'Status': 'SUCCESS'},
            'MailFromAttributes': {'MailFromDomainStatus': 'SUCCESS'},
        }
        verified, detail = self._service_with_mock_client(mock).get_verification_status()
        self.assertTrue(verified)
        self.assertEqual(detail['dkim_status'], 'SUCCESS')

        mock.get_email_identity.return_value = {
            'VerifiedForSendingStatus': False,
            'DkimAttributes': {'Status': 'PENDING'},
        }
        verified, _ = self._service_with_mock_client(mock).get_verification_status()
        self.assertFalse(verified)

    def test_client_error_wrapped_with_retryable_flag(self):
        mock = MagicMock()
        mock.get_email_identity.side_effect = client_error('TooManyRequestsException')
        with self.assertRaises(SESIdentityError) as ctx:
            self._service_with_mock_client(mock).get_verification_status()
        self.assertTrue(ctx.exception.retryable)

        mock.get_email_identity.side_effect = client_error('BadRequestException')
        with self.assertRaises(SESIdentityError) as ctx:
            self._service_with_mock_client(mock).get_verification_status()
        self.assertFalse(ctx.exception.retryable)

    def test_delete_identity_tolerates_missing(self):
        mock = MagicMock()
        mock.delete_email_identity.side_effect = client_error('NotFoundException')
        self._service_with_mock_client(mock).delete_identity()  # must not raise
