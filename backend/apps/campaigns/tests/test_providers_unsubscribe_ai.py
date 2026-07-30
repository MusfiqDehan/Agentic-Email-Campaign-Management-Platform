"""
Tests for unsubscribe flow, SendGrid/Brevo webhooks, and AI prompt helpers.
"""
import uuid
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.authentication.models import Organization
from apps.campaigns.models import Contact, EmailDeliveryLog, EmailAccount, MailboxMessage
from apps.campaigns.utils.email_tracking import (
    unsubscribe_url_for_contact,
    api_unsubscribe_url_for_contact,
    ensure_unsubscribe_footer,
)
from apps.campaigns.views.ai_gen import _build_prompt, _postprocess

User = get_user_model()


@override_settings(
    FRONTEND_URL='http://localhost:3001',
    PUBLIC_API_BASE_URL='http://testserver',
    BACKEND_URL='http://testserver',
)
class UnsubscribeFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=f'u-{uuid.uuid4().hex[:6]}',
            email=f'u-{uuid.uuid4().hex[:6]}@example.com',
            password='changeme123',
        )
        self.org = Organization.objects.create(
            name='Acme Mail',
            slug=f'acme-{uuid.uuid4().hex[:8]}',
            owner=self.user,
        )
        self.user.organization = self.org
        self.user.save(update_fields=['organization'])
        self.contact = Contact.objects.create(
            organization=self.org,
            email=f'reader-{uuid.uuid4().hex[:6]}@example.com',
            first_name='Alex',
            status='ACTIVE',
        )
        self.client = APIClient()

    def test_unsubscribe_urls_are_absolute(self):
        page = unsubscribe_url_for_contact(self.contact.unsubscribe_token)
        api = api_unsubscribe_url_for_contact(self.contact.unsubscribe_token)
        self.assertTrue(page.startswith('http://localhost:3001/unsubscribe?token='))
        self.assertIn('/api/v1/campaigns/unsubscribe/?token=', api)

    def test_get_unsubscribe_info(self):
        res = self.client.get(
            f'/api/v1/campaigns/unsubscribe/?token={self.contact.unsubscribe_token}'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['email'], self.contact.email)
        self.assertEqual(res.data['organization_name'], 'Acme Mail')
        self.assertFalse(res.data['already_unsubscribed'])

    def test_post_unsubscribe_json(self):
        res = self.client.post(
            '/api/v1/campaigns/unsubscribe/',
            {'token': self.contact.unsubscribe_token, 'reason': 'Too many emails'},
            format='json',
        )
        self.assertEqual(res.status_code, 200)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.status, 'UNSUBSCRIBED')
        self.assertIsNotNone(self.contact.unsubscribed_at)

    def test_one_click_rfc8058(self):
        res = self.client.post(
            f'/api/v1/campaigns/unsubscribe/?token={self.contact.unsubscribe_token}',
            'List-Unsubscribe=One-Click',
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.status, 'UNSUBSCRIBED')

    def test_idempotent_unsubscribe(self):
        self.contact.unsubscribe('first')
        res = self.client.post(
            '/api/v1/campaigns/unsubscribe/',
            {'token': self.contact.unsubscribe_token},
            format='json',
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data.get('already_unsubscribed'))

    def test_footer_injection(self):
        html = '<html><body><p>Hello</p></body></html>'
        out = ensure_unsubscribe_footer(html, 'http://localhost:3001/unsubscribe?token=abc', 'Acme')
        self.assertIn('Unsubscribe', out)
        self.assertIn('token=abc', out)


class ProviderWebhookTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=f'w-{uuid.uuid4().hex[:6]}',
            email=f'w-{uuid.uuid4().hex[:6]}@example.com',
            password='changeme123',
        )
        self.org = Organization.objects.create(
            name='Webhook Org',
            slug=f'wh-{uuid.uuid4().hex[:8]}',
            owner=self.user,
        )
        self.log = EmailDeliveryLog.objects.create(
            organization=self.org,
            recipient_email='buyer@example.com',
            sender_email='sales@example.com',
            subject='Offer',
            delivery_status='SENT',
            provider_message_id='sg-msg-abc123',
        )
        self.client = APIClient()

    def test_sendgrid_open_event(self):
        res = self.client.post(
            '/api/v1/campaigns/webhooks/sendgrid/',
            [{
                'event': 'open',
                'email': 'buyer@example.com',
                'sg_message_id': 'sg-msg-abc123',
                'useragent': 'Mozilla/5.0',
            }],
            format='json',
        )
        self.assertEqual(res.status_code, 200)
        self.log.refresh_from_db()
        self.assertEqual(self.log.delivery_status, 'OPENED')
        self.assertGreaterEqual(self.log.open_count, 1)

    def test_sendgrid_bounce_event(self):
        res = self.client.post(
            '/api/v1/campaigns/webhooks/sendgrid/',
            [{
                'event': 'bounce',
                'type': 'bounce',
                'email': 'buyer@example.com',
                'sg_message_id': 'sg-msg-abc123',
                'reason': '550 user unknown',
            }],
            format='json',
        )
        self.assertEqual(res.status_code, 200)
        self.log.refresh_from_db()
        self.assertEqual(self.log.delivery_status, 'BOUNCED')

    def test_brevo_click_event(self):
        self.log.provider_message_id = '<brevo-xyz@smtp-relay.mailin.fr>'
        self.log.save(update_fields=['provider_message_id'])
        res = self.client.post(
            '/api/v1/campaigns/webhooks/brevo/',
            {
                'event': 'click',
                'email': 'buyer@example.com',
                'message-id': '<brevo-xyz@smtp-relay.mailin.fr>',
                'link': 'https://example.com/cta',
            },
            format='json',
        )
        self.assertEqual(res.status_code, 200)
        self.log.refresh_from_db()
        self.assertEqual(self.log.delivery_status, 'CLICKED')

    def test_sendgrid_inbound_parse(self):
        account = EmailAccount(
            organization=self.org,
            name='SG Box',
            email_address='inbox@example.com',
            account_type='SENDGRID',
        )
        account.encrypt_config({'api_key': 'SG.fake', 'from_email': 'inbox@example.com'})
        account.save()

        res = self.client.post(
            '/api/v1/campaigns/webhooks/sendgrid/inbound/',
            {
                'to': 'Inbox <inbox@example.com>',
                'from': 'Friend <friend@example.com>',
                'subject': 'Hello inbound',
                'text': 'Plain body',
                'html': '<p>Plain body</p>',
                'headers': 'Message-ID: <inbound-1@example.com>\nSubject: Hello inbound\n',
            },
            format='multipart',
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.assertTrue(
            MailboxMessage.objects.filter(
                account=account, subject='Hello inbound', direction='INBOUND'
            ).exists()
        )


class AIPromptTests(TestCase):
    def test_prompt_includes_unsubscribe_and_org_vars(self):
        prompt = _build_prompt(
            'Welcome Series',
            'Welcome aboard',
            category='WELCOME',
            tone='friendly',
            audience='new signups',
            cta_text='Open dashboard',
            brand_name='Acme',
        )
        self.assertIn('{{unsubscribe_url}}', prompt)
        self.assertIn('{{organization_name}}', prompt)
        self.assertIn('WELCOME', prompt)
        self.assertIn('Do NOT use {{company_name}}', prompt)

    def test_postprocess_adds_unsubscribe(self):
        data = _postprocess({
            'email_body': '<html><body><p>Hi {{first_name}}</p></body></html>',
            'text_body': 'Hi',
            'tags': 'x',
        })
        self.assertIn('{{unsubscribe_url}}', data['email_body'])
        self.assertIn('{{unsubscribe_url}}', data['text_body'])
        self.assertIsInstance(data['tags'], list)


class SendGridProviderFixTests(TestCase):
    @patch('sendgrid.SendGridAPIClient')
    def test_sendgrid_uses_from_email_config(self, mock_client_cls):
        from apps.campaigns.utils.email_providers import SendGridProvider

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'sg-1'}
        mock_client.send.return_value = mock_response
        mock_client_cls.return_value = mock_client

        provider = SendGridProvider({
            'api_key': 'SG.xxxxx',
            'from_email': 'noreply@example.com',
        })
        ok, mid, data = provider.send_email(
            recipient_email='a@b.com',
            subject='Hi',
            html_content='<p>Hi</p>',
            headers={'List-Unsubscribe': '<https://example.com/u>'},
        )
        self.assertTrue(ok)
        self.assertEqual(mid, 'sg-1')
        mock_client.send.assert_called_once()
