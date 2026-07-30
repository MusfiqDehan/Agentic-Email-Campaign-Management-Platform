"""
Public tracking endpoints (open pixel + click redirect) and SES webhook mount helpers.
"""
import logging

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.campaigns.models import EmailDeliveryLog
from apps.campaigns.utils.email_tracking import (
    PIXEL_GIF,
    decode_click_token,
    decode_open_token,
)

logger = logging.getLogger(__name__)


def _client_meta(request):
    ua = request.META.get('HTTP_USER_AGENT', '')[:1000]
    # Prefer X-Forwarded-For when behind a proxy
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        ip = xff.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ua, ip


@method_decorator(csrf_exempt, name='dispatch')
class TrackOpenView(APIView):
    """1x1 GIF open-tracking pixel. Always returns a pixel even on miss."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, token: str):
        # Strip optional .gif suffix if present in path converter leftovers
        clean = token[:-4] if token.endswith('.gif') else token
        log_id = decode_open_token(clean)
        if log_id:
            try:
                log = EmailDeliveryLog.objects.select_related('contact', 'campaign').get(id=log_id)
                ua, ip = _client_meta(request)
                log.mark_opened(user_agent=ua, ip_address=ip)
                if log.campaign_id:
                    try:
                        log.campaign.update_stats_from_logs()
                    except Exception:
                        logger.debug('Failed to refresh campaign stats after open', exc_info=True)
            except EmailDeliveryLog.DoesNotExist:
                logger.debug('Open track: unknown log %s', log_id)
            except Exception:
                logger.exception('Open track error for %s', log_id)

        return HttpResponse(PIXEL_GIF, content_type='image/gif')


@method_decorator(csrf_exempt, name='dispatch')
class TrackClickView(APIView):
    """Click tracking redirect. Falls back to 404 if token/url invalid."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, token: str):
        log_id, url = decode_click_token(token)
        if not log_id or not url:
            return HttpResponseNotFound('Invalid tracking link')

        try:
            log = EmailDeliveryLog.objects.select_related('contact', 'campaign').get(id=log_id)
            ua, ip = _client_meta(request)
            log.mark_clicked(url=url, user_agent=ua, ip_address=ip)
            if log.campaign_id:
                try:
                    log.campaign.update_stats_from_logs()
                except Exception:
                    logger.debug('Failed to refresh campaign stats after click', exc_info=True)
        except EmailDeliveryLog.DoesNotExist:
            logger.debug('Click track: unknown log %s', log_id)
        except Exception:
            logger.exception('Click track error for %s', log_id)

        # Basic open-redirect guard: only http(s)
        if not (url.startswith('http://') or url.startswith('https://')):
            return HttpResponseNotFound('Invalid destination')
        return HttpResponseRedirect(url)
