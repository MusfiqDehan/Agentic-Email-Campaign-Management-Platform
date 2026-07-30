"""
IMAP mailbox sync for Gmail / custom IMAP accounts.
"""
import email
import imaplib
import logging
import re
from email.header import decode_header, make_header
from email.utils import parseaddr, parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple

from django.utils import timezone

logger = logging.getLogger(__name__)


def _decode_header_value(value: Optional[str]) -> str:
    if not value:
        return ''
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _get_body(msg: email.message.Message) -> Tuple[str, str]:
    text_body = ''
    html_body = ''
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get('Content-Disposition', ''))
            if 'attachment' in disposition:
                continue
            try:
                payload = part.get_payload(decode=True) or b''
                charset = part.get_content_charset() or 'utf-8'
                decoded = payload.decode(charset, errors='replace')
            except Exception:
                continue
            if content_type == 'text/plain' and not text_body:
                text_body = decoded
            elif content_type == 'text/html' and not html_body:
                html_body = decoded
    else:
        try:
            payload = msg.get_payload(decode=True) or b''
            charset = msg.get_content_charset() or 'utf-8'
            decoded = payload.decode(charset, errors='replace')
        except Exception:
            decoded = ''
        if msg.get_content_type() == 'text/html':
            html_body = decoded
        else:
            text_body = decoded
    return text_body, html_body


def _attachment_meta(msg: email.message.Message) -> List[Dict[str, Any]]:
    attachments = []
    for part in msg.walk():
        disposition = str(part.get('Content-Disposition', ''))
        if 'attachment' in disposition or part.get_filename():
            payload = part.get_payload(decode=True) or b''
            attachments.append({
                'filename': part.get_filename(),
                'content_type': part.get_content_type(),
                'size': len(payload),
            })
    return attachments


def _connect_imap(config: Dict[str, Any]) -> imaplib.IMAP4_SSL:
    host = config.get('imap_server') or config.get('imap_host') or 'imap.gmail.com'
    port = int(config.get('imap_port') or 993)
    username = config.get('imap_username') or config.get('username') or config.get('email')
    password = config.get('imap_password') or config.get('password') or config.get('app_password')
    if not username or not password:
        raise ValueError('IMAP username and password are required')
    client = imaplib.IMAP4_SSL(host, port)
    client.login(username, password)
    return client


def sync_account_inbox(account, folder: str = 'INBOX', limit: int = 50) -> Dict[str, Any]:
    """
    Fetch new messages for an EmailAccount via IMAP and store as MailboxMessage.
    Returns sync stats dict.
    """
    from apps.campaigns.models import MailboxMessage

    config = account.decrypt_config()
    defaults = account.get_smtp_defaults()
    merged = {**defaults, **config}

    account.sync_status = 'SYNCING'
    account.last_sync_error = ''
    account.save(update_fields=['sync_status', 'last_sync_error', 'updated_at'])

    fetched = 0
    skipped = 0
    errors = []

    try:
        client = _connect_imap(merged)
        status, _ = client.select(folder)
        if status != 'OK':
            raise RuntimeError(f'Failed to select folder {folder}')

        # Prefer UID-based incremental sync
        last_uid = account.imap_last_uid or 0
        if last_uid > 0:
            typ, data = client.uid('search', None, f'UID {last_uid + 1}:*')
        else:
            typ, data = client.uid('search', None, 'ALL')

        if typ != 'OK':
            raise RuntimeError('IMAP search failed')

        uids = data[0].split() if data and data[0] else []
        # Take the newest `limit` messages when doing a full sync
        if last_uid == 0 and len(uids) > limit:
            uids = uids[-limit:]
        elif len(uids) > limit:
            uids = uids[:limit]

        max_uid_seen = last_uid

        for uid_bytes in uids:
            uid = int(uid_bytes)
            if uid <= last_uid:
                continue
            try:
                typ, msg_data = client.uid('fetch', uid_bytes, '(RFC822)')
                if typ != 'OK' or not msg_data or not msg_data[0]:
                    skipped += 1
                    continue
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                message_id = (msg.get('Message-ID') or '').strip()
                if message_id and MailboxMessage.objects.filter(
                    account=account, message_id=message_id
                ).exists():
                    skipped += 1
                    max_uid_seen = max(max_uid_seen, uid)
                    continue

                from_name, from_addr = parseaddr(msg.get('From', ''))
                to_raw = msg.get_all('To', []) or []
                cc_raw = msg.get_all('Cc', []) or []
                to_addresses = [_decode_header_value(t) for t in to_raw]
                cc_addresses = [_decode_header_value(c) for c in cc_raw]

                subject = _decode_header_value(msg.get('Subject'))
                text_body, html_body = _get_body(msg)
                snippet_src = text_body or re.sub(r'<[^>]+>', ' ', html_body or '')
                snippet = ' '.join(snippet_src.split())[:250]

                received_at = timezone.now()
                date_hdr = msg.get('Date')
                if date_hdr:
                    try:
                        received_at = parsedate_to_datetime(date_hdr)
                        if timezone.is_naive(received_at):
                            received_at = timezone.make_aware(received_at, timezone.utc)
                    except Exception:
                        pass

                in_reply_to = (msg.get('In-Reply-To') or '').strip()
                references = (msg.get('References') or '').strip()
                thread_key = in_reply_to or message_id or str(uid)

                MailboxMessage.objects.create(
                    organization=account.organization,
                    account=account,
                    direction='INBOUND',
                    folder='INBOX',
                    message_id=message_id,
                    in_reply_to=in_reply_to,
                    references=references,
                    thread_key=thread_key,
                    from_address=from_addr or 'unknown@unknown',
                    from_name=from_name or '',
                    to_addresses=to_addresses,
                    cc_addresses=cc_addresses,
                    subject=(subject or '(no subject)')[:998],
                    text_body=text_body,
                    html_body=html_body,
                    snippet=snippet,
                    imap_uid=uid,
                    raw_headers={
                        'from': msg.get('From'),
                        'to': msg.get('To'),
                        'date': msg.get('Date'),
                        'subject': msg.get('Subject'),
                    },
                    attachments_meta=_attachment_meta(msg),
                    is_read=False,
                    received_at=received_at,
                )
                fetched += 1
                max_uid_seen = max(max_uid_seen, uid)
            except Exception as exc:
                logger.exception('Failed to process IMAP UID %s', uid)
                errors.append(str(exc))
                skipped += 1

        try:
            client.logout()
        except Exception:
            pass

        account.imap_last_uid = max_uid_seen
        account.last_synced_at = timezone.now()
        account.sync_status = 'IDLE'
        account.last_sync_error = '; '.join(errors)[:2000] if errors else ''
        account.save(update_fields=[
            'imap_last_uid', 'last_synced_at', 'sync_status', 'last_sync_error', 'updated_at'
        ])

        return {
            'success': True,
            'fetched': fetched,
            'skipped': skipped,
            'errors': errors,
            'last_uid': max_uid_seen,
        }
    except Exception as exc:
        logger.exception('IMAP sync failed for account %s', account.id)
        account.sync_status = 'ERROR'
        account.last_sync_error = str(exc)[:2000]
        account.save(update_fields=['sync_status', 'last_sync_error', 'updated_at'])
        return {'success': False, 'error': str(exc), 'fetched': fetched, 'skipped': skipped}
