from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.authentication.models import Organization
from apps.campaigns.models import (
    AutomationRule,
    EmailAction,
    EmailDeliveryLog,
    EmailQueue,
    EmailTemplate,
)

User = get_user_model()


def make_organization(name='Acme'):
    email = f'owner@{name.lower()}.test'
    owner = User.objects.create_user(username=email, email=email, password='x')
    return Organization.objects.create(name=name, slug=name.lower(), owner=owner)


class EmailDeliveryLogViewTests(TestCase):
    def setUp(self):
        self.organization = make_organization('Acme')
        self.other_organization = make_organization('Rival')

        self.template = EmailTemplate.objects.create(
            template_name="Welcome",
            organization=self.organization,
            category=EmailTemplate.TemplateCategory.OTHER,
            email_subject="Hello {{ name }}",
            email_body="<p>Hello {{ name }}</p>",
        )
        self.rule = AutomationRule.objects.create(
            automation_name="Welcome",
            organization=self.organization,
            email_template=self.template,
            reason_name=AutomationRule.ReasonName.OTHER,
            trigger_type=AutomationRule.TriggerType.IMMEDIATE,
        )
        self.log = EmailDeliveryLog.objects.create(
            automation_rule=self.rule,
            organization=self.organization,
            reason_name=self.rule.reason_name,
            trigger_type=self.rule.trigger_type,
            email_template=self.template,
            recipient_email="member@example.com",
            sender_email="support@example.com",
            subject="Acme Subject",
            delivery_status='SENT',
            context_data={'name': 'Acme User'},
        )
        EmailDeliveryLog.objects.create(
            organization=self.other_organization,
            email_template=self.template,
            recipient_email="outsider@example.com",
            sender_email="support@rival.test",
            subject="Rival Subject",
            delivery_status='FAILED',
            context_data={'name': 'Rival User'},
        )

    def test_list_filters_by_organization_query_param(self):
        url = reverse('email-delivery-log-list')
        response = self.client.get(url, {'organization_id': str(self.organization.id)})
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['recipient_email'], 'member@example.com')

    def test_list_legacy_tenant_id_param_still_filters(self):
        url = reverse('email-delivery-log-list')
        response = self.client.get(url, {'tenant_id': str(self.organization.id)})
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(len(data), 1)

    def test_list_scoped_to_authenticated_users_organization(self):
        member = User.objects.create_user(
            username='member@acme.test', email='member@acme.test', password='x'
        )
        member.organization = self.organization
        member.save(update_fields=['organization'])
        client = APIClient()
        client.force_authenticate(user=member)

        url = reverse('email-delivery-log-list')
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['recipient_email'], 'member@example.com')

    def test_detail_includes_template_body_from_queue(self):
        queue_item = EmailQueue.objects.create(
            automation_rule=self.rule,
            organization=self.organization,
            recipient_email=self.log.recipient_email,
            subject=self.log.subject,
            html_content="<p>Rendered Body</p>",
            text_content="Rendered Body",
            context_data={'name': 'Acme User'},
            headers={},
            status='SENT',
            priority=1,
            scheduled_at=timezone.now(),
        )
        self.log.queue_item = queue_item
        self.log.save(update_fields=['queue_item'])

        url = reverse('email-delivery-log-detail', kwargs={'pk': self.log.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['id'], str(self.log.id))
        self.assertEqual(data['email_template_body'], "<p>Rendered Body</p>")
        self.assertEqual(data['email_template_text_body'], "Rendered Body")

    def test_detail_renders_template_when_queue_missing(self):
        url = reverse('email-delivery-log-detail', kwargs={'pk': self.log.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertTrue(data['email_template_body'])
        self.assertIn('Acme', data['subject'])


class EmailDeliveryLogActionTests(TestCase):
    def setUp(self):
        self.organization = make_organization('Acme')
        self.template = EmailTemplate.objects.create(
            template_name="Alert",
            organization=self.organization,
            category=EmailTemplate.TemplateCategory.OTHER,
            email_subject="Alert {{ code }}",
            email_body="<p>Alert {{ code }}</p>",
        )
        self.rule = AutomationRule.objects.create(
            automation_name="Alert",
            organization=self.organization,
            email_template=self.template,
            reason_name=AutomationRule.ReasonName.OTHER,
            trigger_type=AutomationRule.TriggerType.IMMEDIATE,
        )
        self.log = EmailDeliveryLog.objects.create(
            automation_rule=self.rule,
            organization=self.organization,
            reason_name=self.rule.reason_name,
            trigger_type=self.rule.trigger_type,
            email_template=self.template,
            recipient_email="recipient@example.com",
            sender_email="alerts@example.com",
            subject="Alert 123",
            delivery_status='FAILED',
            context_data={'code': '123'},
        )

    @patch('apps.campaigns.views.enhanced_views.submit_email_queue_task')
    def test_resend_creates_queue_item(self, mock_submit):
        url = reverse('email-delivery-log-resend', kwargs={'pk': self.log.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        queue_item = EmailQueue.objects.latest('created_at')
        self.assertEqual(queue_item.recipient_email, 'recipient@example.com')
        self.assertEqual(queue_item.organization_id, self.organization.id)
        self.assertIn('Alert', queue_item.subject)
        self.assertIn('123', queue_item.html_content)

        action = EmailAction.objects.get(original_log=self.log, action_type='RESEND')
        self.assertIsNone(action.new_recipient)
        mock_submit.assert_called_once_with(queue_item.id, priority=1)

    @patch('apps.campaigns.views.enhanced_views.submit_email_queue_task')
    def test_forward_creates_queue_item_for_new_recipient(self, mock_submit):
        url = reverse('email-delivery-log-forward', kwargs={'pk': self.log.pk})
        payload = {'new_recipient': 'other@example.com'}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)

        queue_item = EmailQueue.objects.latest('created_at')
        self.assertEqual(queue_item.recipient_email, 'other@example.com')
        self.assertTrue(queue_item.subject.startswith('Fwd:'))
        self.assertIn('123', queue_item.html_content)
        action = EmailAction.objects.get(original_log=self.log, action_type='FORWARD')
        self.assertEqual(action.new_recipient, 'other@example.com')
        mock_submit.assert_called_once_with(queue_item.id, priority=3)
