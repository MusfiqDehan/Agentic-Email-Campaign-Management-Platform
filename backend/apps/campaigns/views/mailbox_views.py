"""
Mailbox API: connect Gmail/SES accounts, sync inbox, compose/send/reply.
"""
import logging
import uuid as uuid_lib
from email.utils import formataddr

from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.views import APIView

from apps.utils.mixins import CustomResponseMixin
from apps.campaigns.models import EmailAccount, MailboxMessage, EmailDeliveryLog
from apps.campaigns.serializers.mailbox_serializers import (
    EmailAccountSerializer,
    MailboxMessageListSerializer,
    MailboxMessageDetailSerializer,
    MailboxMessageUpdateSerializer,
    ComposeMessageSerializer,
)
from apps.campaigns.utils.email_providers import EmailProviderFactory, SMTPProvider
from apps.campaigns.utils.mailbox_sync import sync_account_inbox
from apps.campaigns.utils.email_tracking import apply_tracking

logger = logging.getLogger(__name__)


def _require_org(user):
    return getattr(user, 'organization', None)


class EmailAccountListCreateView(CustomResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        org = _require_org(request.user)
        if not org:
            return self.error_response('No organization', status_code=status.HTTP_400_BAD_REQUEST)
        qs = EmailAccount.objects.filter(organization=org).order_by('name')
        return self.success_response(
            data=EmailAccountSerializer(qs, many=True).data,
            message='Email accounts retrieved',
        )

    def post(self, request):
        org = _require_org(request.user)
        if not org:
            return self.error_response('No organization', status_code=status.HTTP_400_BAD_REQUEST)
        serializer = EmailAccountSerializer(data=request.data, context={'organization': org})
        if not serializer.is_valid():
            return self.error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        account = serializer.save()
        return self.success_response(
            data=EmailAccountSerializer(account).data,
            message='Email account connected',
            status_code=status.HTTP_201_CREATED,
        )


class EmailAccountDetailView(CustomResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get(self, request, pk):
        org = _require_org(request.user)
        try:
            return EmailAccount.objects.get(id=pk, organization=org)
        except EmailAccount.DoesNotExist:
            return None

    def get(self, request, pk):
        account = self._get(request, pk)
        if not account:
            return self.error_response('Not found', status_code=status.HTTP_404_NOT_FOUND)
        return self.success_response(data=EmailAccountSerializer(account).data)

    def patch(self, request, pk):
        account = self._get(request, pk)
        if not account:
            return self.error_response('Not found', status_code=status.HTTP_404_NOT_FOUND)
        serializer = EmailAccountSerializer(
            account, data=request.data, partial=True, context={'organization': account.organization}
        )
        if not serializer.is_valid():
            return self.error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        account = serializer.save()
        return self.success_response(data=EmailAccountSerializer(account).data, message='Updated')

    def delete(self, request, pk):
        account = self._get(request, pk)
        if not account:
            return self.error_response('Not found', status_code=status.HTTP_404_NOT_FOUND)
        account.delete()
        return self.success_response(message='Account deleted')


class EmailAccountSyncView(CustomResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        org = _require_org(request.user)
        try:
            account = EmailAccount.objects.get(id=pk, organization=org)
        except EmailAccount.DoesNotExist:
            return self.error_response('Not found', status_code=status.HTTP_404_NOT_FOUND)

        if account.account_type in ('AWS_SES', 'SENDGRID', 'BREVO'):
            return self.success_response(
                data={
                    'note': (
                        'This provider receives mail via webhooks, not IMAP. '
                        'Configure SendGrid Inbound Parse or SES SNS to '
                        '/api/v1/campaigns/webhooks/... '
                    ),
                    'account_type': account.account_type,
                },
                message='Webhook-based accounts do not use IMAP sync',
            )

        result = sync_account_inbox(account)
        if not result.get('success'):
            return self.error_response(
                result.get('error', 'Sync failed'),
                status_code=status.HTTP_400_BAD_REQUEST,
                data=result,
            )
        return self.success_response(data=result, message='Mailbox synced')


class MailboxMessageListView(CustomResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        org = _require_org(request.user)
        if not org:
            return self.error_response('No organization', status_code=status.HTTP_400_BAD_REQUEST)

        qs = MailboxMessage.objects.filter(organization=org).select_related('account')

        folder = request.query_params.get('folder', 'INBOX')
        if folder and folder != 'ALL':
            qs = qs.filter(folder=folder)

        direction = request.query_params.get('direction')
        if direction:
            qs = qs.filter(direction=direction)

        account_id = request.query_params.get('account_id')
        if account_id:
            qs = qs.filter(account_id=account_id)

        is_read = request.query_params.get('is_read')
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() in ('1', 'true', 'yes'))

        q = request.query_params.get('q')
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(subject__icontains=q)
                | Q(from_address__icontains=q)
                | Q(snippet__icontains=q)
                | Q(from_name__icontains=q)
            )

        try:
            limit = min(int(request.query_params.get('limit', 50)), 200)
            offset = max(int(request.query_params.get('offset', 0)), 0)
        except ValueError:
            limit, offset = 50, 0

        total = qs.count()
        unread = MailboxMessage.objects.filter(
            organization=org, folder='INBOX', direction='INBOUND', is_read=False
        ).count()
        page = qs[offset:offset + limit]
        return self.success_response(
            data={
                'results': MailboxMessageListSerializer(page, many=True).data,
                'total': total,
                'unread': unread,
                'limit': limit,
                'offset': offset,
            },
            message='Messages retrieved',
        )


class MailboxMessageDetailView(CustomResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get(self, request, pk):
        org = _require_org(request.user)
        try:
            return MailboxMessage.objects.select_related('account').get(id=pk, organization=org)
        except MailboxMessage.DoesNotExist:
            return None

    def get(self, request, pk):
        msg = self._get(request, pk)
        if not msg:
            return self.error_response('Not found', status_code=status.HTTP_404_NOT_FOUND)
        if not msg.is_read:
            msg.mark_read()
        return self.success_response(data=MailboxMessageDetailSerializer(msg).data)

    def patch(self, request, pk):
        msg = self._get(request, pk)
        if not msg:
            return self.error_response('Not found', status_code=status.HTTP_404_NOT_FOUND)
        serializer = MailboxMessageUpdateSerializer(msg, data=request.data, partial=True)
        if not serializer.is_valid():
            return self.error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return self.success_response(data=MailboxMessageDetailSerializer(msg).data, message='Updated')

    def delete(self, request, pk):
        msg = self._get(request, pk)
        if not msg:
            return self.error_response('Not found', status_code=status.HTTP_404_NOT_FOUND)
        msg.folder = 'TRASH'
        msg.save(update_fields=['folder', 'updated_at'])
        return self.success_response(message='Moved to trash')


def _provider_for_account(account):
    """Build an EmailProviderInterface for outbound sends from a mailbox account."""
    config = account.decrypt_config()
    defaults = account.get_smtp_defaults()
    merged = {**defaults, **config}
    merged.setdefault('from_email', account.email_address)
    merged.setdefault('default_from_email', account.email_address)

    if account.email_provider_id:
        try:
            provider_cfg = account.email_provider.decrypt_config()
            merged = {**provider_cfg, **merged}
            return EmailProviderFactory.create_provider(
                account.email_provider.provider_type, merged
            )
        except Exception as e:
            logger.warning('Falling back to account config: %s', e)

    if account.account_type == 'AWS_SES':
        return EmailProviderFactory.create_provider('AWS_SES', merged)

    if account.account_type == 'SENDGRID':
        return EmailProviderFactory.create_provider('SENDGRID', merged)

    if account.account_type == 'BREVO':
        return EmailProviderFactory.create_provider('BREVO', merged)

    # Gmail / Custom → SMTP
    smtp_config = {
        'smtp_server': merged.get('smtp_server', 'smtp.gmail.com'),
        'smtp_port': int(merged.get('smtp_port') or 587),
        'username': merged.get('username') or merged.get('imap_username') or account.email_address,
        'password': merged.get('password') or merged.get('app_password') or merged.get('imap_password'),
        'from_email': account.email_address,
        'use_tls': merged.get('use_tls', True),
        'use_ssl': merged.get('use_ssl', False),
    }
    return SMTPProvider(smtp_config)


class MailboxComposeView(CustomResponseMixin, APIView):
    """Send a new message (or reply) from a connected mailbox account."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        org = _require_org(request.user)
        if not org:
            return self.error_response('No organization', status_code=status.HTTP_400_BAD_REQUEST)

        serializer = ComposeMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            account = EmailAccount.objects.get(id=data['account_id'], organization=org)
        except EmailAccount.DoesNotExist:
            return self.error_response('Account not found', status_code=status.HTTP_404_NOT_FOUND)

        # Enforce sender identities once the org has adopted sending domains
        # (suspended/unverified addresses must not send from the mailbox either).
        from django.core.exceptions import ValidationError as DjangoValidationError
        from ..utils.sender_validation import validate_sender
        try:
            validate_sender(org, account.email_address)
        except DjangoValidationError as exc:
            return self.error_response(
                '; '.join(exc.messages), status_code=status.HTTP_403_FORBIDDEN
            )

        parent = None
        headers = {}
        if data.get('reply_to_message_id'):
            try:
                parent = MailboxMessage.objects.get(
                    id=data['reply_to_message_id'], organization=org, account=account
                )
                if parent.message_id:
                    headers['In-Reply-To'] = parent.message_id
                    headers['References'] = (
                        f"{parent.references} {parent.message_id}".strip()
                        if parent.references else parent.message_id
                    )
            except MailboxMessage.DoesNotExist:
                return self.error_response('Reply target not found', status_code=status.HTTP_404_NOT_FOUND)

        html_body = data.get('html_body') or ''
        text_body = data.get('text_body') or ''
        if not html_body and text_body:
            html_body = f"<pre>{text_body}</pre>"

        # Create delivery log early so we can embed tracking tokens before send
        primary_to = data['to'][0]
        delivery_log = EmailDeliveryLog.objects.create(
            organization=org,
            recipient_email=primary_to,
            sender_email=account.email_address,
            subject=data['subject'],
            delivery_status='QUEUED',
            context_data={
                'cc': data.get('cc') or [],
                'bcc': data.get('bcc') or [],
                'mailbox': True,
            },
        )

        if data.get('track_opens') or data.get('track_clicks'):
            html_body = apply_tracking(
                html_body,
                str(delivery_log.id),
                track_opens=data.get('track_opens', False),
                track_clicks=data.get('track_clicks', False),
            )

        display = account.display_name or account.name
        sender = formataddr((display, account.email_address)) if display else account.email_address

        try:
            provider = _provider_for_account(account)
            # Send to primary; additional recipients via To header when supported
            success, message_id, response_data = provider.send_email(
                recipient_email=primary_to,
                subject=data['subject'],
                html_content=html_body,
                text_content=text_body,
                sender_email=sender,
                headers=headers or None,
            )
            # Best-effort extra To/Cc via additional sends for SMTP/SES simple API
            for extra in (data.get('to') or [])[1:] + (data.get('cc') or []):
                try:
                    provider.send_email(
                        recipient_email=extra,
                        subject=data['subject'],
                        html_content=html_body,
                        text_content=text_body,
                        sender_email=sender,
                        headers=headers or None,
                    )
                except Exception as exc:
                    logger.warning('Failed sending to extra recipient %s: %s', extra, exc)
        except Exception as exc:
            logger.exception('Mailbox compose failed')
            delivery_log.delivery_status = 'FAILED'
            delivery_log.error_message = str(exc)
            delivery_log.save(update_fields=['delivery_status', 'error_message', 'updated_at'])
            return self.error_response(str(exc), status_code=status.HTTP_400_BAD_REQUEST)

        if not success:
            err = response_data.get('error') if isinstance(response_data, dict) else response_data
            if isinstance(err, dict):
                err_msg = err.get('message', str(err))
            else:
                err_msg = str(err or response_data.get('error_message', 'Send failed'))
            delivery_log.delivery_status = 'FAILED'
            delivery_log.error_message = err_msg
            delivery_log.save(update_fields=['delivery_status', 'error_message', 'updated_at'])
            return self.error_response(
                err_msg,
                status_code=status.HTTP_400_BAD_REQUEST,
                data=response_data,
            )

        delivery_log.delivery_status = 'SENT'
        delivery_log.provider_message_id = message_id or ''
        delivery_log.sent_at = timezone.now()
        delivery_log.save(update_fields=[
            'delivery_status', 'provider_message_id', 'sent_at', 'updated_at'
        ])

        rfc_message_id = f"<{uuid_lib.uuid4()}@{account.email_address.split('@')[-1]}>"
        mailbox_msg = MailboxMessage.objects.create(
            organization=org,
            account=account,
            direction='OUTBOUND',
            folder='SENT',
            message_id=rfc_message_id,
            in_reply_to=headers.get('In-Reply-To', ''),
            references=headers.get('References', ''),
            thread_key=headers.get('In-Reply-To') or rfc_message_id,
            from_address=account.email_address,
            from_name=display,
            to_addresses=data['to'],
            cc_addresses=data.get('cc') or [],
            bcc_addresses=data.get('bcc') or [],
            subject=data['subject'],
            text_body=text_body,
            html_body=html_body,
            snippet=(text_body or '')[:250],
            provider_message_id=message_id or '',
            is_read=True,
            sent_at=timezone.now(),
            delivery_log=delivery_log,
            parent_message=parent,
        )

        return self.success_response(
            data=MailboxMessageDetailSerializer(mailbox_msg).data,
            message='Message sent',
            status_code=status.HTTP_201_CREATED,
        )


class MailboxStatsView(CustomResponseMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        org = _require_org(request.user)
        if not org:
            return self.error_response('No organization', status_code=status.HTTP_400_BAD_REQUEST)

        base = MailboxMessage.objects.filter(organization=org)
        return self.success_response(data={
            'accounts': EmailAccount.objects.filter(organization=org).count(),
            'inbox': base.filter(folder='INBOX', direction='INBOUND').count(),
            'unread': base.filter(folder='INBOX', direction='INBOUND', is_read=False).count(),
            'sent': base.filter(folder='SENT').count(),
            'drafts': base.filter(folder='DRAFTS').count(),
            'trash': base.filter(folder='TRASH').count(),
        })
