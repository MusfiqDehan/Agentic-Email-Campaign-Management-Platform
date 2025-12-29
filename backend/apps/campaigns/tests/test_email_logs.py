import uuid
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from campaigns.models import (
    AutomationRule,
    EmailDeliveryLog,
    EmailQueue,
    EmailTemplate,
    EmailAction,
)


class EmailDeliveryLogViewTests(TestCase):
    def setUp(self):
        self.tenant_rule = AutomationRule.objects.create(
            automation_name="Tenant Welcome",
            tenant_id=uuid.uuid4(),
            rule_scope=AutomationRule.RuleScope.TENANT,
            product_id=uuid.uuid4(),
            reason_name=AutomationRule.ReasonName.TENANT_REGISTRATION_CONFIRMATION,
            trigger_type=AutomationRule.TriggerType.IMMEDIATE,
        )
        self.global_rule = AutomationRule.objects.create(
            automation_name="Global Alert",
            rule_scope=AutomationRule.RuleScope.GLOBAL,
            product_id=uuid.uuid4(),
            reason_name=AutomationRule.ReasonName.OTHER,
            trigger_type=AutomationRule.TriggerType.DELAY,
        )
        template = EmailTemplate.objects.create(
            template_name="Welcome",
            tenant_id=self.tenant_rule.tenant_id,
            template_type=EmailTemplate.TemplateType.TENANT,
            category=EmailTemplate.TemplateCategory.OTHER,
            email_subject="Hello {{ name }}",
            email_body="<p>Hello {{ name }}</p>",
            recipient_emails_list="user@example.com",
        )
        EmailDeliveryLog.objects.create(
            automation_rule=self.tenant_rule,
            tenant_id=self.tenant_rule.tenant_id,
            product_id=self.tenant_rule.product_id,
            reason_name=self.tenant_rule.reason_name,
            trigger_type=self.tenant_rule.trigger_type,
            email_template=template,
            recipient_email="tenant@example.com",
            sender_email="support@example.com",
            subject="Tenant Subject",
            delivery_status='SENT',
            log_scope='TENANT',
            context_data={'name': 'Tenant User'},
        )
        EmailDeliveryLog.objects.create(
            automation_rule=self.global_rule,
            tenant_id=None,
            product_id=self.global_rule.product_id,
            reason_name=self.global_rule.reason_name,
            trigger_type=self.global_rule.trigger_type,
            email_template=template,
            recipient_email="global@example.com",
            sender_email="support@example.com",
            subject="Global Subject",
            delivery_status='FAILED',
            log_scope='GLOBAL',
            context_data={'name': 'Global User'},
        )

    def test_list_defaults_to_tenant_scope(self):
        url = reverse('email-delivery-log-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['scope'], 'TENANT')
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['log_scope'], 'TENANT')

    def test_list_includes_global_when_requested(self):
        url = reverse('email-delivery-log-list')
        response = self.client.get(url, {'include_global': 'true'})
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        scopes = {item['log_scope'] for item in data['results']}
        self.assertEqual(data['scope'], 'COMBINED')
        self.assertEqual(data['count'], 2)
        self.assertEqual(scopes, {'TENANT', 'GLOBAL'})

    def test_list_global_scope_only(self):
        url = reverse('email-delivery-log-list')
        response = self.client.get(url, {'scope': 'global'})
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['scope'], 'GLOBAL')
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['log_scope'], 'GLOBAL')

    def test_detail_includes_template_body_from_queue(self):
        log = EmailDeliveryLog.objects.get(recipient_email="tenant@example.com")
        queue_item = EmailQueue.objects.create(
            automation_rule=log.automation_rule,
            tenant_id=log.tenant_id,
            recipient_email=log.recipient_email,
            subject=log.subject,
            html_content="<p>Rendered Body</p>",
            text_content="Rendered Body",
            context_data={'name': 'Tenant User'},
            headers={},
            status='SENT',
            priority=1,
            scheduled_at=timezone.now(),
        )
        log.queue_item = queue_item
        log.save(update_fields=['queue_item'])

        url = reverse('email-delivery-log-detail', kwargs={'pk': log.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['id'], str(log.id))
        self.assertEqual(data['email_template_body'], "<p>Rendered Body</p>")
        self.assertEqual(data['email_template_text_body'], "Rendered Body")

    def test_detail_renders_template_when_queue_missing(self):
        log = EmailDeliveryLog.objects.get(recipient_email="global@example.com")
        url = reverse('email-delivery-log-detail', kwargs={'pk': log.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertTrue(data['email_template_body'])
        self.assertIn('Global', data['subject'])


class EmailDeliveryLogActionTests(TestCase):
    def setUp(self):
        self.rule = AutomationRule.objects.create(
            automation_name="Global Alert",
            rule_scope=AutomationRule.RuleScope.GLOBAL,
            product_id=uuid.uuid4(),
            reason_name=AutomationRule.ReasonName.OTHER,
            trigger_type=AutomationRule.TriggerType.IMMEDIATE,
        )
        self.template = EmailTemplate.objects.create(
            template_name="Alert",
            template_type=EmailTemplate.TemplateType.GLOBAL,
            category=EmailTemplate.TemplateCategory.OTHER,
            email_subject="Alert {{ code }}",
            email_body="<p>Alert {{ code }}</p>",
            recipient_emails_list="global@example.com",
        )
        self.log = EmailDeliveryLog.objects.create(
            automation_rule=self.rule,
            product_id=self.rule.product_id,
            reason_name=self.rule.reason_name,
            trigger_type=self.rule.trigger_type,
            email_template=self.template,
            recipient_email="recipient@example.com",
            sender_email="alerts@example.com",
            subject="Alert 123",
            delivery_status='FAILED',
            log_scope='GLOBAL',
            context_data={'code': '123'},
        )

    @patch('campaigns.views.enhanced_views.process_email_queue_task.delay')
    def test_resend_creates_queue_item(self, mock_delay):
        url = reverse('email-delivery-log-resend', kwargs={'pk': self.log.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        queue_item = EmailQueue.objects.latest('created_at')
        self.assertEqual(queue_item.recipient_email, 'recipient@example.com')
        self.assertIsNone(queue_item.tenant_id)
        self.assertIn('Alert', queue_item.subject)
        self.assertIn('123', queue_item.html_content)

        action = EmailAction.objects.get(original_log=self.log, action_type='RESEND')
        self.assertIsNone(action.new_recipient)
        mock_delay.assert_called_once_with(str(queue_item.id))

    @patch('campaigns.views.enhanced_views.process_email_queue_task.delay')
    def test_forward_creates_queue_item_for_new_recipient(self, mock_delay):
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
        mock_delay.assert_called_once_with(str(queue_item.id))