"""
AWS SES (v2) identity management for sending domains.

Provisions a SendingDomain as an SES email identity with DKIM signing and a
custom MAIL FROM domain, reads back verification status, and produces the DNS
records the organization must publish.

Credentials are resolved per SendingDomain.ownership_mode:
- PLATFORM: the platform's own AWS account (settings.AWS_ACCESS_KEY_ID /
  AWS_SECRET_ACCESS_KEY / AWS_SES_REGION_NAME).
- ORG: the organization's AWS SES EmailProvider (decrypted encrypted_config).

Credentials stay per-instance — never copy the global-settings-mutation
pattern used by backends._build_ses_backend.
"""
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings

logger = logging.getLogger(__name__)

RETRYABLE_ERROR_CODES = {
    'TooManyRequestsException',
    'ThrottlingException',
    'InternalServiceErrorException',
    'ServiceUnavailableException',
    'RequestTimeout',
}


class SESIdentityError(Exception):
    """A typed wrapper around AWS SES identity API failures."""

    def __init__(self, message, code='', retryable=False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class SESIdentityService:
    """Manage the SES identity backing a single SendingDomain."""

    def __init__(self, domain):
        self.domain = domain
        self._client_instance = None

    # ------------------------------------------------------------------
    # Credentials / client
    # ------------------------------------------------------------------

    def _resolve_credentials(self):
        """Return (access_key, secret_key, region) for this domain's mode."""
        if self.domain.ownership_mode == self.domain.OWNERSHIP_ORG:
            provider = self.domain.provider
            if provider is None:
                raise SESIdentityError(
                    "Org-owned domain has no linked AWS SES provider", code='MissingProvider'
                )
            config = provider.decrypt_config()
            access_key = config.get('aws_access_key') or config.get('aws_access_key_id')
            secret_key = config.get('aws_secret_key') or config.get('aws_secret_access_key')
            region = (
                self.domain.region
                or config.get('aws_region_name') or config.get('region_name')
                or config.get('region') or settings.AWS_SES_REGION_NAME
            )
            if not access_key or not secret_key:
                raise SESIdentityError(
                    "The linked SES provider is missing AWS credentials", code='MissingCredentials'
                )
            return access_key, secret_key, region

        access_key = settings.AWS_ACCESS_KEY_ID
        secret_key = settings.AWS_SECRET_ACCESS_KEY
        region = self.domain.region or settings.AWS_SES_REGION_NAME
        if not access_key or not secret_key:
            raise SESIdentityError(
                "Platform AWS SES credentials are not configured "
                "(AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY)",
                code='MissingCredentials',
            )
        return access_key, secret_key, region

    def _client(self):
        """Build (and cache) the sesv2 client. Single seam for test mocking."""
        if self._client_instance is None:
            access_key, secret_key, region = self._resolve_credentials()
            self._client_instance = boto3.client(
                'sesv2',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )
        return self._client_instance

    @staticmethod
    def _wrap_error(exc):
        if isinstance(exc, ClientError):
            code = exc.response.get('Error', {}).get('Code', '')
            message = exc.response.get('Error', {}).get('Message', str(exc))
            return SESIdentityError(message, code=code, retryable=code in RETRYABLE_ERROR_CODES)
        return SESIdentityError(str(exc), retryable=True)

    # ------------------------------------------------------------------
    # Identity lifecycle
    # ------------------------------------------------------------------

    def create_identity(self):
        """
        Create the domain identity with Easy DKIM and configure the custom
        MAIL FROM domain. Updates dkim_tokens / dns_records / region on the
        SendingDomain (caller saves). Adopts an already-existing identity.
        """
        client = self._client()
        _, _, region = self._resolve_credentials()

        try:
            client.create_email_identity(EmailIdentity=self.domain.domain)
        except ClientError as exc:
            code = exc.response.get('Error', {}).get('Code', '')
            if code != 'AlreadyExistsException':
                raise self._wrap_error(exc)
        except BotoCoreError as exc:
            raise self._wrap_error(exc)

        try:
            client.put_email_identity_mail_from_attributes(
                EmailIdentity=self.domain.domain,
                MailFromDomain=self.domain.mail_from_domain,
                BehaviorOnMxFailure='USE_DEFAULT_VALUE',
            )
            identity = client.get_email_identity(EmailIdentity=self.domain.domain)
        except (ClientError, BotoCoreError) as exc:
            raise self._wrap_error(exc)

        dkim_tokens = identity.get('DkimAttributes', {}).get('Tokens', []) or []
        self.domain.region = region
        self.domain.dkim_tokens = dkim_tokens
        self.domain.dns_records = self.build_dns_records(dkim_tokens, region)
        return identity

    def get_verification_status(self):
        """
        Return (verified: bool, detail: dict) from SES for this identity.

        SES's DKIM verification status is what actually gates sending from
        the domain, so it is the single source of truth here.
        """
        client = self._client()
        try:
            identity = client.get_email_identity(EmailIdentity=self.domain.domain)
        except (ClientError, BotoCoreError) as exc:
            raise self._wrap_error(exc)

        dkim = identity.get('DkimAttributes', {})
        mail_from = identity.get('MailFromAttributes', {})
        verified = bool(identity.get('VerifiedForSendingStatus')) and dkim.get('Status') == 'SUCCESS'
        detail = {
            'verified_for_sending': bool(identity.get('VerifiedForSendingStatus')),
            'dkim_status': dkim.get('Status', ''),
            'mail_from_status': mail_from.get('MailFromDomainStatus', ''),
        }
        return verified, detail

    def delete_identity(self):
        """Delete the SES identity. Missing identities are treated as success."""
        client = self._client()
        try:
            client.delete_email_identity(EmailIdentity=self.domain.domain)
        except ClientError as exc:
            code = exc.response.get('Error', {}).get('Code', '')
            if code == 'NotFoundException':
                return
            raise self._wrap_error(exc)
        except BotoCoreError as exc:
            raise self._wrap_error(exc)

    # ------------------------------------------------------------------
    # DNS records
    # ------------------------------------------------------------------

    def build_dns_records(self, dkim_tokens, region):
        """Human-displayable DNS records the org must publish for this domain."""
        d = self.domain.domain
        mail_from = self.domain.mail_from_domain
        records = [
            {
                'type': 'CNAME',
                'name': f'{token}._domainkey.{d}',
                'value': f'{token}.dkim.amazonses.com',
                'purpose': 'DKIM signing (required for verification)',
            }
            for token in dkim_tokens
        ]
        records.append({
            'type': 'MX',
            'name': mail_from,
            'value': f'10 feedback-smtp.{region}.amazonses.com',
            'purpose': 'Custom MAIL FROM domain (bounce handling)',
        })
        records.append({
            'type': 'TXT',
            'name': mail_from,
            'value': '"v=spf1 include:amazonses.com ~all"',
            'purpose': 'SPF for the MAIL FROM domain',
        })
        records.append({
            'type': 'TXT',
            'name': f'_dmarc.{d}',
            'value': '"v=DMARC1; p=none;"',
            'purpose': 'DMARC policy (recommended)',
        })
        if self.domain.ownership_mode == self.domain.OWNERSHIP_PLATFORM:
            records.append({
                'type': 'MX',
                'name': d,
                'value': f'10 inbound-smtp.{region}.amazonaws.com',
                'purpose': 'Inbound email receiving (required to receive mail)',
            })
        return records
