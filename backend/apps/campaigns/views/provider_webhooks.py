"""
Third-party provider event webhooks (SendGrid + Brevo).

Wire these in each provider dashboard:
  SendGrid Event Webhook → POST /api/v1/campaigns/webhooks/sendgrid/
  Brevo transactional webhook → POST /api/v1/campaigns/webhooks/brevo/
  SendGrid Inbound Parse → POST /api/v1/campaigns/webhooks/sendgrid/inbound/
"""
import logging
from email.utils import parseaddr
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser

from apps.campaigns.models import EmailDeliveryLog, EmailAccount, MailboxMessage, Contact
from apps.utils.view_mixins import PublicCORSMixin

logger = logging.getLogger(__name__)


def _find_log(message_id: Optional[str], email: Optional[str] = None) -> Optional[EmailDeliveryLog]:
    if not message_id and not email:
        return None
    qs = EmailDeliveryLog.objects.select_related('contact', 'campaign', 'email_validation')
    if message_id:
        # SendGrid message ids often appear as <id> or with suffixes
        candidates = [
            message_id,
            message_id.strip('<>'),
            message_id.split('.')[0] if message_id else message_id,
        ]
        for mid in candidates:
            if not mid:
                continue
            log = qs.filter(provider_message_id=mid).first()
            if log:
                return log
            log = qs.filter(provider_message_id__icontains=mid).order_by('-sent_at').first()
            if log:
                return log
    if email:
        return qs.filter(recipient_email__iexact=email).order_by('-sent_at').first()
    return None


def _apply_open(log: EmailDeliveryLog, payload: Dict[str, Any]):
    ua = payload.get('useragent') or payload.get('user_agent') or ''
    ip = payload.get('ip') or payload.get('ipAddress')
    log.mark_opened(user_agent=ua, ip_address=ip)
    if log.campaign_id:
        try:
            log.campaign.update_stats_from_logs()
        except Exception:
            pass


def _apply_click(log: EmailDeliveryLog, payload: Dict[str, Any]):
    url = payload.get('url') or payload.get('link') or ''
    ua = payload.get('useragent') or payload.get('user_agent') or ''
    ip = payload.get('ip') or payload.get('ipAddress')
    log.mark_clicked(url=url, user_agent=ua, ip_address=ip)
    if log.campaign_id:
        try:
            log.campaign.update_stats_from_logs()
        except Exception:
            pass


def _apply_bounce(log: EmailDeliveryLog, payload: Dict[str, Any], hard: bool = True):
    reason = payload.get('reason') or payload.get('bounce_description') or payload.get('error') or 'Bounced'
    bounce_type = 'HARD' if hard else 'SOFT'
    log.mark_bounced(bounce_type=bounce_type, reason=str(reason)[:2000])
    if log.campaign_id:
        try:
            log.campaign.update_stats_from_logs()
        except Exception:
            pass


def _apply_complaint(log: EmailDeliveryLog, payload: Dict[str, Any]):
    log.delivery_status = 'COMPLAINED'
    log.bounce_type = 'COMPLAINT'
    log.bounce_reason = payload.get('reason') or 'Spam complaint'
    log.is_spam = True
    log.bounced_at = timezone.now()
    log.record_event('complained', payload)
    log.save()
    if log.contact:
        try:
            log.contact.mark_complained()
        except Exception:
            pass


def _apply_unsubscribe(email: Optional[str], reason: str = 'Provider unsubscribe'):
    if not email:
        return
    for contact in Contact.objects.filter(email__iexact=email, status='ACTIVE'):
        contact.unsubscribe(reason)


@method_decorator(csrf_exempt, name='dispatch')
class SendGridEventWebhookView(PublicCORSMixin, APIView):
    """SendGrid Event Webhook (JSON array of events)."""

    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        events = request.data
        if isinstance(events, dict):
            events = [events]
        if not isinstance(events, list):
            return Response({'error': 'Expected JSON array'}, status=400)

        processed = 0
        for event in events:
            try:
                self._handle_event(event)
                processed += 1
            except Exception:
                logger.exception('SendGrid event handling failed: %s', event)
        return Response({'ok': True, 'processed': processed})

    def _handle_event(self, event: Dict[str, Any]):
        event_type = (event.get('event') or '').lower()
        message_id = event.get('sg_message_id') or event.get('smtp-id') or event.get('sg_event_id')
        email = event.get('email')
        log = _find_log(message_id, email)
        if not log and event_type not in {'unsubscribe', 'group_unsubscribe'}:
            logger.debug('SendGrid event %s: no matching log for %s', event_type, message_id)
            return

        if event_type in {'delivered'}:
            if log and log.delivery_status in {'QUEUED', 'SENT', 'FAILED'}:
                log.delivery_status = 'DELIVERED'
                log.delivered_at = timezone.now()
                log.record_event('delivered', event)
                log.save()
        elif event_type in {'open'}:
            if log:
                _apply_open(log, event)
        elif event_type in {'click'}:
            if log:
                _apply_click(log, event)
        elif event_type in {'bounce', 'blocked'}:
            if log:
                hard = event.get('type') == 'bounce' or event_type == 'bounce'
                _apply_bounce(log, event, hard=hard)
        elif event_type in {'dropped'}:
            if log:
                _apply_bounce(log, event, hard=True)
        elif event_type in {'spamreport'}:
            if log:
                _apply_complaint(log, event)
        elif event_type in {'unsubscribe', 'group_unsubscribe'}:
            _apply_unsubscribe(email, 'SendGrid unsubscribe')
            if log:
                log.delivery_status = 'UNSUBSCRIBED'
                log.record_event('unsubscribed', event)
                log.save()


@method_decorator(csrf_exempt, name='dispatch')
class BrevoEventWebhookView(PublicCORSMixin, APIView):
    """Brevo / Sendinblue transactional & marketing webhooks."""

    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        event_type = (
            payload.get('event')
            or payload.get('type')
            or (payload.get('email') or {}).get('event')
            or ''
        )
        event_type = str(event_type).lower()

        # Brevo wraps differently for marketing vs transactional
        email = (
            payload.get('email')
            if isinstance(payload.get('email'), str)
            else payload.get('email', {}).get('email') if isinstance(payload.get('email'), dict) else None
        )
        message_id = (
            payload.get('message-id')
            or payload.get('messageId')
            or payload.get('tag')
            or ''
        )

        try:
            self._handle(event_type, email, message_id, payload)
        except Exception:
            logger.exception('Brevo event handling failed')
            return Response({'ok': False}, status=500)
        return Response({'ok': True})

    def _handle(self, event_type: str, email: Optional[str], message_id: str, payload: Dict[str, Any]):
        log = _find_log(message_id, email)

        if event_type in {'delivered', 'delivery'}:
            if log and log.delivery_status in {'QUEUED', 'SENT', 'FAILED'}:
                log.delivery_status = 'DELIVERED'
                log.delivered_at = timezone.now()
                log.record_event('delivered', payload)
                log.save()
        elif event_type in {'opened', 'unique_opened', 'open'}:
            if log:
                _apply_open(log, payload)
        elif event_type in {'click', 'clicked', 'unique_click'}:
            if log:
                _apply_click(log, payload)
        elif event_type in {'hard_bounce', 'soft_bounce', 'bounce', 'blocked', 'invalid_email', 'error'}:
            if log:
                hard = 'hard' in event_type or event_type in {'invalid_email', 'blocked'}
                _apply_bounce(log, payload, hard=hard)
        elif event_type in {'spam', 'complaint', 'spamreport'}:
            if log:
                _apply_complaint(log, payload)
        elif event_type in {'unsubscribed', 'unsubscribe'}:
            _apply_unsubscribe(email, 'Brevo unsubscribe')
            if log:
                log.delivery_status = 'UNSUBSCRIBED'
                log.record_event('unsubscribed', payload)
                log.save()
        else:
            logger.debug('Unhandled Brevo event type: %s', event_type)


@method_decorator(csrf_exempt, name='dispatch')
class SendGridInboundParseView(PublicCORSMixin, APIView):
    """
    SendGrid Inbound Parse webhook.
    Configure MX → SendGrid and POST to this URL to store inbound mailbox messages.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    def post(self, request):
        data = request.data
        to_raw = data.get('to') or data.get('envelope') or ''
        from_raw = data.get('from') or ''
        subject = data.get('subject') or '(no subject)'
        text_body = data.get('text') or ''
        html_body = data.get('html') or ''
        message_id = data.get('headers', '')
        # Try extract Message-ID from headers blob
        rfc_id = ''
        headers_blob = data.get('headers') or ''
        for line in str(headers_blob).splitlines():
            if line.lower().startswith('message-id:'):
                rfc_id = line.split(':', 1)[1].strip()
                break

        from_name, from_addr = parseaddr(from_raw)
        # Resolve destination mailbox
        destinations = []
        if isinstance(to_raw, str):
            for part in to_raw.replace(';', ',').split(','):
                _, addr = parseaddr(part.strip())
                if addr:
                    destinations.append(addr.lower())

        account = None
        for addr in destinations:
            account = EmailAccount.objects.filter(
                email_address__iexact=addr,
                account_type__in=['SENDGRID', 'CUSTOM', 'GMAIL'],
                is_active=True,
                is_deleted=False,
            ).first()
            if account:
                break
        if not account and destinations:
            # Fall back to any SendGrid account in orgs that match domain
            domain = destinations[0].split('@')[-1]
            account = EmailAccount.objects.filter(
                account_type='SENDGRID',
                email_address__iendswith=f'@{domain}',
                is_active=True,
                is_deleted=False,
            ).first()

        if not account:
            logger.warning('SendGrid inbound: no mailbox for %s', destinations)
            return Response({'ok': True, 'stored': False, 'reason': 'no_mailbox'})

        if rfc_id and MailboxMessage.objects.filter(account=account, message_id=rfc_id).exists():
            return Response({'ok': True, 'stored': False, 'reason': 'duplicate'})

        snippet_src = text_body or html_body
        MailboxMessage.objects.create(
            organization=account.organization,
            account=account,
            direction='INBOUND',
            folder='INBOX',
            message_id=rfc_id or '',
            from_address=from_addr or 'unknown@unknown',
            from_name=from_name or '',
            to_addresses=destinations,
            subject=str(subject)[:998],
            text_body=text_body,
            html_body=html_body,
            snippet=' '.join(str(snippet_src).split())[:250],
            received_at=timezone.now(),
            is_read=False,
            raw_headers={'to': to_raw, 'from': from_raw},
        )
        return Response({'ok': True, 'stored': True})
