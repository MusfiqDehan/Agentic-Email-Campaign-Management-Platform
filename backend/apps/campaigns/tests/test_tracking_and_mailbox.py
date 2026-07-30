"""
Tests for first-party email tracking and mailbox APIs.
Uses apps.campaigns imports (compatible with INSTALLED_APPS).
"""
import uuid
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.authentication.models import Organization
from apps.campaigns.models import (
    Campaign,
    Contact,
    ContactList,
    EmailAccount,
    EmailDeliveryLog,
    MailboxMessage,
)
from apps.campaigns.utils.email_tracking import (
    apply_tracking,
    decode_click_token,
    decode_open_token,
    inject_open_pixel,
    make_click_token,
    make_open_token,
    rewrite_click_links,
)
from apps.campaigns.utils.email_providers import AWSSESProvider

User = get_user_model()


class EmailTrackingUtilsTests(TestCase):
    def test_open_token_roundtrip(self):
        log_id = str(uuid.uuid4())
        token = make_open_token(log_id)
        self.assertEqual(decode_open_token(token), log_id)

    def test_click_token_roundtrip(self):
        log_id = str(uuid.uuid4())
        url = 'https://example.com/offer?x=1'
        token = make_click_token(log_id, url)
        decoded_id, decoded_url = decode_click_token(token)
        self.assertEqual(decoded_id, log_id)
        self.assertEqual(decoded_url, url)

    def test_inject_pixel_and_rewrite_links(self):
        log_id = str(uuid.uuid4())
        html = '<html><body><a href="https://example.com/a">A</a><a href="mailto:x@y.com">M</a></body></html>'
        tracked = apply_tracking(html, log_id, track_opens=True, track_clicks=True)
        self.assertIn('/api/v1/campaigns/track/open/', tracked)
        self.assertIn('/api/v1/campaigns/track/click/', tracked)
        self.assertIn('mailto:x@y.com', tracked)
        self.assertIn('.gif', tracked)

    def test_rewrite_skips_tracking_urls(self):
        log_id = str(uuid.uuid4())
        already = f'<a href="http://localhost:8001/api/v1/campaigns/track/click/abc/">x</a>'
        result = rewrite_click_links(already, log_id)
        self.assertEqual(result.count('/track/click/'), 1)


@override_settings(
    PUBLIC_API_BASE_URL='http://testserver',
    BACKEND_URL='http://testserver',
)
class TrackingEndpointTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username=f'owner-{uuid.uuid4().hex[:6]}',
            email=f'owner-{uuid.uuid4().hex[:6]}@example.com',
            password='changeme123',
        )
        self.org = Organization.objects.create(
            name='Track Org',
            slug=f'track-{uuid.uuid4().hex[:8]}',
            owner=self.owner,
        )
        self.owner.organization = self.org
        self.owner.save(update_fields=['organization'])
        self.log = EmailDeliveryLog.objects.create(
            organization=self.org,
            recipient_email='reader@example.com',
            sender_email='sender@example.com',
            subject='Hello',
            delivery_status='SENT',
        )
        self.client = APIClient()

    def test_open_pixel_marks_opened(self):
        token = make_open_token(str(self.log.id))
        url = f'/api/v1/campaigns/track/open/{token}.gif'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/gif')
        self.log.refresh_from_db()
        self.assertEqual(self.log.delivery_status, 'OPENED')
        self.assertEqual(self.log.open_count, 1)
        self.assertIsNotNone(self.log.opened_at)

    def test_click_redirect_marks_clicked(self):
        dest = 'https://example.com/landing'
        token = make_click_token(str(self.log.id), dest)
        url = f'/api/v1/campaigns/track/click/{token}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], dest)
        self.log.refresh_from_db()
        self.assertEqual(self.log.delivery_status, 'CLICKED')
        self.assertEqual(self.log.click_count, 1)

    def test_invalid_click_token_404(self):
        response = self.client.get('/api/v1/campaigns/track/click/not-a-valid-token/')
        self.assertEqual(response.status_code, 404)


class AWSSESProviderConfigSetTests(TestCase):
    @patch('apps.campaigns.utils.email_providers.boto3.client')
    def test_send_uses_configuration_set_and_raw_email(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.send_raw_email.return_value = {'MessageId': 'ses-msg-1'}
        mock_client_factory.return_value = mock_client

        provider = AWSSESProvider({
            'aws_access_key_id': 'AKIATEST',
            'aws_secret_access_key': 'secret',
            'region_name': 'us-east-1',
            'from_email': 'noreply@example.com',
            'configuration_set': 'marketing-events',
        })
        ok, message_id, data = provider.send_email(
            recipient_email='user@example.com',
            subject='Subj',
            html_content='<p>Hi</p>',
            text_content='Hi',
            headers={'Reply-To': 'reply@example.com'},
        )
        self.assertTrue(ok)
        self.assertEqual(message_id, 'ses-msg-1')
        self.assertEqual(data.get('configuration_set'), 'marketing-events')
        kwargs = mock_client.send_raw_email.call_args.kwargs
        self.assertEqual(kwargs['ConfigurationSetName'], 'marketing-events')
        self.assertIn('Reply-To: reply@example.com', kwargs['RawMessage']['Data'])


class MailboxAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=f'mailbox-{uuid.uuid4().hex[:6]}',
            email=f'admin-{uuid.uuid4().hex[:6]}@mailorg.test',
            password='changeme123',
        )
        self.org = Organization.objects.create(
            name='Mail Org',
            slug=f'mail-{uuid.uuid4().hex[:8]}',
            owner=self.user,
        )
        self.user.organization = self.org
        self.user.save(update_fields=['organization'])
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.account = EmailAccount(
            organization=self.org,
            name='Test Gmail',
            email_address='box@example.com',
            account_type='GMAIL',
            display_name='Box',
            is_default=True,
        )
        self.account.encrypt_config({
            'app_password': 'fake-app-password',
            'password': 'fake-app-password',
            'username': 'box@example.com',
            'from_email': 'box@example.com',
        })
        self.account.save()

    def test_list_accounts(self):
        if not getattr(self.user, 'organization', None):
            self.skipTest('User model has no organization relation in this environment')
        response = self.client.get('/api/v1/campaigns/mailbox/accounts/')
        self.assertEqual(response.status_code, 200)
        data = response.data.get('data', response.data)
        self.assertTrue(isinstance(data, list))
        self.assertGreaterEqual(len(data), 1)

    def test_mailbox_stats(self):
        if not getattr(self.user, 'organization', None):
            self.skipTest('User model has no organization relation in this environment')
        MailboxMessage.objects.create(
            organization=self.org,
            account=self.account,
            direction='INBOUND',
            folder='INBOX',
            from_address='friend@example.com',
            to_addresses=['box@example.com'],
            subject='Hello',
            snippet='Hi there',
            text_body='Hi there',
            message_id=f'<{uuid.uuid4()}@example.com>',
            is_read=False,
        )
        response = self.client.get('/api/v1/campaigns/mailbox/stats/')
        self.assertEqual(response.status_code, 200)
        data = response.data.get('data', response.data)
        self.assertEqual(data['inbox'], 1)
        self.assertEqual(data['unread'], 1)

    @patch('apps.campaigns.views.mailbox_views._provider_for_account')
    def test_compose_sends_and_stores_sent(self, mock_provider_factory):
        if not getattr(self.user, 'organization', None):
            self.skipTest('User model has no organization relation in this environment')
        mock_provider = MagicMock()
        mock_provider.send_email.return_value = (True, 'msg-123', {'provider': 'SMTP'})
        mock_provider_factory.return_value = mock_provider

        response = self.client.post('/api/v1/campaigns/mailbox/compose/', {
            'account_id': str(self.account.id),
            'to': ['friend@example.com'],
            'subject': 'Ping',
            'text_body': 'Hello friend',
            'html_body': '<p>Hello friend</p>',
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(
            MailboxMessage.objects.filter(
                account=self.account, direction='OUTBOUND', folder='SENT', subject='Ping'
            ).exists()
        )
        mock_provider.send_email.assert_called()
