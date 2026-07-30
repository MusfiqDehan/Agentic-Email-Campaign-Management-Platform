"""
First-party open/click tracking for campaign emails.

Injects a 1x1 tracking pixel and rewrites links so opens/clicks work for every
provider (SES, SMTP/Gmail, SendGrid, Brevo) without relying solely on SES events.
"""
import logging
import re
from html import escape
from typing import Optional, Tuple
from urllib.parse import quote, urlencode, urlparse

from django.conf import settings
from django.core import signing

logger = logging.getLogger(__name__)

TRACKING_SALT = 'email-delivery-tracking'
CLICK_SALT = 'email-click-tracking'
PIXEL_GIF = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04'
    b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)

# Skip rewriting these URL schemes / destinations
_SKIP_HREF_PREFIXES = (
    'mailto:', 'tel:', 'sms:', 'javascript:', '#', 'data:',
)


def get_tracking_base_url() -> str:
    return (
        getattr(settings, 'PUBLIC_API_BASE_URL', None)
        or getattr(settings, 'BACKEND_URL', None)
        or 'http://localhost:8001'
    ).rstrip('/')


def make_open_token(log_id: str) -> str:
    return signing.dumps({'log_id': str(log_id), 't': 'open'}, salt=TRACKING_SALT)


def make_click_token(log_id: str, url: str) -> str:
    return signing.dumps({'log_id': str(log_id), 'url': url, 't': 'click'}, salt=CLICK_SALT)


def decode_open_token(token: str, max_age: int = 60 * 60 * 24 * 90) -> Optional[str]:
    try:
        data = signing.loads(token, salt=TRACKING_SALT, max_age=max_age)
        if data.get('t') != 'open':
            return None
        return data.get('log_id')
    except signing.BadSignature:
        logger.debug('Invalid open tracking token')
        return None


def decode_click_token(token: str, max_age: int = 60 * 60 * 24 * 90) -> Tuple[Optional[str], Optional[str]]:
    try:
        data = signing.loads(token, salt=CLICK_SALT, max_age=max_age)
        if data.get('t') != 'click':
            return None, None
        return data.get('log_id'), data.get('url')
    except signing.BadSignature:
        logger.debug('Invalid click tracking token')
        return None, None


def open_pixel_url(log_id: str) -> str:
    token = make_open_token(log_id)
    return f"{get_tracking_base_url()}/api/v1/campaigns/track/open/{quote(token)}.gif"


def click_redirect_url(log_id: str, destination: str) -> str:
    token = make_click_token(log_id, destination)
    return f"{get_tracking_base_url()}/api/v1/campaigns/track/click/{quote(token)}/"


def _should_rewrite_url(url: str) -> bool:
    if not url or not url.strip():
        return False
    lowered = url.strip().lower()
    if any(lowered.startswith(p) for p in _SKIP_HREF_PREFIXES):
        return False
    # Don't double-wrap our own tracking URLs
    if '/campaigns/track/' in lowered:
        return False
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in ('http', 'https'):
        return False
    return True


_HREF_RE = re.compile(
    r'(<a\b[^>]*?\bhref\s*=\s*)([\'"])(.*?)\2',
    re.IGNORECASE | re.DOTALL,
)


def inject_open_pixel(html_content: str, log_id: str) -> str:
    if not html_content:
        return html_content
    pixel = (
        f'<img src="{escape(open_pixel_url(log_id))}" width="1" height="1" '
        f'alt="" style="display:none!important;width:1px;height:1px;border:0;" />'
    )
    lower = html_content.lower()
    body_close = lower.rfind('</body>')
    if body_close != -1:
        return html_content[:body_close] + pixel + html_content[body_close:]
    return html_content + pixel


def rewrite_click_links(html_content: str, log_id: str) -> str:
    if not html_content:
        return html_content

    def replacer(match):
        prefix, quote_char, url = match.group(1), match.group(2), match.group(3)
        if not _should_rewrite_url(url):
            return match.group(0)
        tracked = click_redirect_url(log_id, url)
        return f'{prefix}{quote_char}{tracked}{quote_char}'

    return _HREF_RE.sub(replacer, html_content)


def apply_tracking(
    html_content: str,
    log_id: str,
    track_opens: bool = True,
    track_clicks: bool = True,
) -> str:
    """Apply open pixel and/or click rewriting to HTML body."""
    result = html_content or ''
    if track_clicks:
        result = rewrite_click_links(result, log_id)
    if track_opens:
        result = inject_open_pixel(result, log_id)
    return result


def build_list_unsubscribe_header(unsubscribe_url: str) -> str:
    return f'<{unsubscribe_url}>'


def unsubscribe_url_for_contact(token: str) -> str:
    """Human-facing unsubscribe page on the frontend."""
    base = getattr(settings, 'FRONTEND_URL', 'http://localhost:3001').rstrip('/')
    return f"{base}/unsubscribe?{urlencode({'token': token})}"


def api_unsubscribe_url_for_contact(token: str) -> str:
    """
    API URL for List-Unsubscribe / RFC 8058 one-click POST.
    Mail clients POST List-Unsubscribe=One-Click to this URL.
    """
    base = get_tracking_base_url()
    return f"{base}/api/v1/campaigns/unsubscribe/?{urlencode({'token': token})}"


def build_unsubscribe_footer_html(unsubscribe_url: str, organization_name: str = '') -> str:
    org = organization_name or 'us'
    return (
        '<div style="margin-top:32px;padding-top:16px;border-top:1px solid #e5e7eb;'
        'font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.5;color:#6b7280;text-align:center;">'
        f'<p style="margin:0 0 8px;">You are receiving this email from {org}.</p>'
        f'<p style="margin:0;"><a href="{unsubscribe_url}" style="color:#2563eb;text-decoration:underline;">'
        'Unsubscribe</a> from future emails.</p>'
        '</div>'
    )


def ensure_unsubscribe_footer(html_content: str, unsubscribe_url: str, organization_name: str = '') -> str:
    """Append an unsubscribe footer if the HTML does not already include one."""
    if not html_content:
        html_content = '<html><body></body></html>'
    lowered = html_content.lower()
    if 'unsubscribe' in lowered and (unsubscribe_url.lower() in lowered or '{{unsubscribe_url}}' in lowered):
        return html_content
    footer = build_unsubscribe_footer_html(unsubscribe_url, organization_name)
    body_close = lowered.rfind('</body>')
    if body_close != -1:
        return html_content[:body_close] + footer + html_content[body_close:]
    return html_content + footer
