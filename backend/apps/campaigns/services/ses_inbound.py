"""
AWS SES inbound email handler.

Configured via django-ses setting:
  AWS_SES_INBOUND_HANDLER = 'apps.campaigns.services.ses_inbound.SESInboundHandler'

Receives SNS "Received" notifications (content inline or via S3) and stores
messages in the organization mailbox.
"""
import logging
from email.utils import parseaddr, parsedate_to_datetime

from django.utils import timezone
from django_ses.inbound import BaseHandler, S3Handler, UnprocessableError

logger = logging.getLogger(__name__)


class SESInboundHandler(S3Handler):
    """
    Prefer S3 action (fetch raw MIME from S3). Falls back to inline content
    when present on the SNS notification.
    """

    def check_action_compatibility(self):
        action_type = (self.action or {}).get('type')
        # Allow both S3 and SNS/inline content
        if action_type and action_type.upper() not in {'S3', 'SNS'}:
            # Still try if content was provided inline
            if not getattr(self, '_inline_content', None):
                raise UnprocessableError(
                    f"Unsupported SES receipt action type: {action_type}"
                )

    def prepare_content(self, content):
        # Inline SNS content path
        if content:
            if isinstance(content, str):
                return content.encode('utf-8', errors='replace')
            return content
        # S3Handler path
        return super().prepare_content(content)

    def handle(self, content=None, *args, **kwargs):
        self._inline_content = content
        # If no S3 bucket configured but content present, parse directly
        action_type = (self.action or {}).get('type', '').upper()
        if content and action_type != 'S3':
            self.email = self.parse_email(
                content.encode('utf-8', errors='replace') if isinstance(content, str) else content
            )
            self.process()
            return
        super().handle(content=content, *args, **kwargs)

    def process(self):
        from apps.campaigns.models import EmailAccount, MailboxMessage

        email = self.email
        common = self.mail_obj.get('commonHeaders', {}) if self.mail_obj else {}
        destination = (self.mail_obj or {}).get('destination') or email.get('to') or []
        if isinstance(destination, str):
            destination = [destination]

        # Match destination to a configured SES mailbox account
        account = None
        for dest in destination:
            _, addr = parseaddr(dest)
            addr = (addr or dest or '').lower().strip()
            if not addr:
                continue
            account = EmailAccount.objects.filter(
                email_address__iexact=addr,
                account_type='AWS_SES',
                is_active=True,
                is_deleted=False,
            ).first()
            if account:
                break

        if not account:
            # Fallback: any org SES account that matches destination domain
            for dest in destination:
                _, addr = parseaddr(dest)
                addr = (addr or dest or '').lower().strip()
                if '@' not in addr:
                    continue
                domain = addr.split('@', 1)[1]
                account = EmailAccount.objects.filter(
                    email_address__iendswith=f'@{domain}',
                    account_type='AWS_SES',
                    is_active=True,
                    is_deleted=False,
                ).first()
                if account:
                    break

        if not account:
            logger.warning(
                "SES inbound: no EmailAccount matched destinations %s", destination
            )
            return

        from_raw = common.get('from', [None])
        if isinstance(from_raw, list):
            from_raw = from_raw[0] if from_raw else ''
        from_name, from_addr = parseaddr(from_raw or '')
        if not from_addr:
            source = (self.mail_obj or {}).get('source', '')
            from_name, from_addr = parseaddr(source)

        message_id = (
            email.get('message_id')
            or common.get('messageId')
            or (self.mail_obj or {}).get('messageId')
            or ''
        )
        if message_id and MailboxMessage.objects.filter(
            account=account, message_id=message_id
        ).exists():
            logger.info("SES inbound: duplicate message_id %s, skipping", message_id)
            return

        received_at = timezone.now()
        date_str = email.get('date') or (common.get('date') if isinstance(common.get('date'), str) else None)
        if date_str:
            try:
                received_at = parsedate_to_datetime(date_str)
                if timezone.is_naive(received_at):
                    received_at = timezone.make_aware(received_at, timezone.utc)
            except Exception:
                pass

        to_list = email.get('to') or destination or []
        subject = email.get('subject') or common.get('subject') or '(no subject)'
        text_body = email.get('plain_text') or ''
        html_body = email.get('html_text') or ''
        snippet = (text_body or re_strip_html(html_body))[:250]

        in_reply_to = ''
        references = ''
        if isinstance(common.get('inReplyTo'), list) and common['inReplyTo']:
            in_reply_to = common['inReplyTo'][0]
        elif isinstance(common.get('inReplyTo'), str):
            in_reply_to = common['inReplyTo']
        if isinstance(common.get('references'), list):
            references = ' '.join(common['references'])
        elif isinstance(common.get('references'), str):
            references = common['references']

        thread_key = in_reply_to or message_id or str(account.id)

        attachments_meta = []
        for att in email.get('attachments') or []:
            attachments_meta.append({
                'filename': att.get('filename'),
                'content_type': att.get('content_type'),
                'size': len(att.get('data') or b''),
            })

        MailboxMessage.objects.create(
            organization=account.organization,
            account=account,
            direction='INBOUND',
            folder='INBOX',
            message_id=message_id or '',
            in_reply_to=in_reply_to,
            references=references,
            thread_key=thread_key,
            from_address=from_addr or 'unknown@unknown',
            from_name=from_name or '',
            to_addresses=list(to_list),
            subject=subject[:998],
            text_body=text_body,
            html_body=html_body,
            snippet=snippet,
            provider_message_id=(self.mail_obj or {}).get('messageId', ''),
            raw_headers=common or {},
            attachments_meta=attachments_meta,
            is_read=False,
            received_at=received_at,
        )
        logger.info(
            "SES inbound stored for %s from %s subject=%s",
            account.email_address, from_addr, subject[:80],
        )


def re_strip_html(html: str) -> str:
    import re
    if not html:
        return ''
    return re.sub(r'<[^>]+>', ' ', html).strip()
