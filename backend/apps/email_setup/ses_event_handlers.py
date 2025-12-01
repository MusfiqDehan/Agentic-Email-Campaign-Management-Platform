import logging
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

from django.db import transaction
from django.dispatch import receiver
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from django_ses.signals import (
    bounce_received,
    click_received,
    complaint_received,
    delivery_received,
    open_received,
    send_received,
)

from .models import EmailDeliveryLog

logger = logging.getLogger(__name__)


def _extract_timestamp(event_obj: Optional[Dict[str, Any]], mail_obj: Optional[Dict[str, Any]]) -> datetime:
    timestamp = None
    if isinstance(event_obj, dict):
        timestamp = (
            event_obj.get("timestamp")
            or event_obj.get("sentTimestamp")
            or event_obj.get("processingTime")
        )
    if not timestamp and isinstance(mail_obj, dict):
        timestamp = mail_obj.get("timestamp")

    dt = parse_datetime(timestamp) if timestamp else None
    if dt is None:
        return timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    return dt


def _append_event(log: EmailDeliveryLog, event: str, occurred_at: timezone.datetime, payload: Dict[str, Any]) -> None:
    history = list(log.event_history or [])
    history.append({
        "event": event,
        "timestamp": occurred_at.isoformat(),
        "payload": payload,
    })
    log.event_history = history


def _recalculate_click_metrics(log: EmailDeliveryLog) -> None:
    history = log.event_history or []
    log.open_count = sum(1 for evt in history if evt.get("event") == "OPEN")
    log.click_count = sum(1 for evt in history if evt.get("event") == "CLICK")
    unique_links = {
        evt.get("payload", {}).get("link")
        for evt in history
        if evt.get("event") == "CLICK" and evt.get("payload", {}).get("link")
    }
    log.unique_click_count = len(unique_links)


def _normalise_bounce_type(raw_type: Optional[str]) -> str:
    mapping = {
        "PERMANENT": "HARD",
        "TRANSIENT": "SOFT",
        "UNDETERMINED": "SOFT",
        "COMPLAINT": "COMPLAINT",
    }
    if not raw_type:
        return "SOFT"
    return mapping.get(raw_type.upper(), "SOFT")


def _bounce_reason(bounce_obj: Dict[str, Any]) -> str:
    recipients: Iterable[Dict[str, Any]] = bounce_obj.get("bouncedRecipients", []) or []
    reasons = []
    for recipient in recipients:
        parts = []
        if recipient.get("emailAddress"):
            parts.append(recipient["emailAddress"])
        diagnostic = recipient.get("diagnosticCode") or recipient.get("status")
        if diagnostic:
            parts.append(str(diagnostic))
        if parts:
            reasons.append(" - ".join(parts))
    if reasons:
        return "; ".join(reasons)
    return bounce_obj.get("bounceSubType", "")


def _apply_queue_failure(log: EmailDeliveryLog, reason: str) -> None:
    queue_item = getattr(log, "queue_item", None)
    if queue_item and queue_item.status != "FAILED":
        queue_item.status = "FAILED"
        queue_item.error_message = reason
        queue_item.save(update_fields=["status", "error_message", "updated_at"])


def _handle_event(event_name: str, mail_obj: Dict[str, Any], event_obj: Dict[str, Any], processor) -> None:
    message_id = (mail_obj or {}).get("messageId")
    if not message_id:
        logger.warning("SES %s event missing messageId; skipping", event_name)
        return

    try:
        with transaction.atomic():
            log = (
                EmailDeliveryLog.objects.select_for_update()
                .select_related("email_validation", "queue_item")
                .get(provider_message_id=message_id)
            )
            occurred_at = _extract_timestamp(event_obj, mail_obj)
            update_fields = processor(log, occurred_at, event_obj, mail_obj)
            update_fields = set(update_fields or [])
            update_fields.add("event_history")
            update_fields.add("updated_at")
            log.save(update_fields=list(update_fields))
    except EmailDeliveryLog.DoesNotExist:
        logger.warning(
            "SES %s event received for unknown message id %s", event_name, message_id
        )


@receiver(send_received)
def ses_send_received(sender, mail_obj, send_obj, raw_message, **kwargs):
    def processor(log: EmailDeliveryLog, occurred_at, event_obj, _mail_obj):
        update_fields = set()
        if not log.sent_at or occurred_at < log.sent_at:
            log.sent_at = occurred_at
            update_fields.add("sent_at")
        if log.delivery_status in {"QUEUED", "FAILED", "SENT"}:
            log.delivery_status = "SENT"
            update_fields.add("delivery_status")
        _append_event(log, "SEND", occurred_at, event_obj or {})
        return update_fields

    _handle_event("send", mail_obj, send_obj or {}, processor)


@receiver(delivery_received)
def ses_delivery_received(sender, mail_obj, delivery_obj, raw_message, **kwargs):
    def processor(log: EmailDeliveryLog, occurred_at, event_obj, _mail_obj):
        update_fields = {"delivered_at"}
        if not log.delivered_at or occurred_at >= log.delivered_at:
            log.delivered_at = occurred_at
        if log.delivery_status in {"QUEUED", "FAILED", "SENT", "DELIVERED"}:
            log.delivery_status = "DELIVERED"
            update_fields.add("delivery_status")
        _append_event(log, "DELIVERY", occurred_at, event_obj or {})
        if log.email_validation:
            log.email_validation.update_reputation("delivered")
        return update_fields

    _handle_event("delivery", mail_obj, delivery_obj or {}, processor)


@receiver(bounce_received)
def ses_bounce_received(sender, mail_obj, bounce_obj, raw_message, **kwargs):
    def processor(log: EmailDeliveryLog, occurred_at, event_obj, _mail_obj):
        reason = _bounce_reason(event_obj or {})
        log.delivery_status = "BOUNCED"
        log.bounced_at = occurred_at
        log.bounce_type = _normalise_bounce_type(event_obj.get("bounceType"))
        log.bounce_reason = reason
        _append_event(log, "BOUNCE", occurred_at, event_obj or {})
        if log.email_validation:
            log.email_validation.update_reputation("bounced")
        _apply_queue_failure(log, reason or "SES bounce event")
        return {"delivery_status", "bounced_at", "bounce_type", "bounce_reason", "updated_at"}

    _handle_event("bounce", mail_obj, bounce_obj or {}, processor)


@receiver(complaint_received)
def ses_complaint_received(sender, mail_obj, complaint_obj, raw_message, **kwargs):
    def processor(log: EmailDeliveryLog, occurred_at, event_obj, _mail_obj):
        complaint_reason = event_obj.get("complaintFeedbackType") or event_obj.get("complaintSubType") or "Complaint received"
        log.delivery_status = "COMPLAINED"
        log.bounced_at = occurred_at
        log.bounce_type = "COMPLAINT"
        log.bounce_reason = complaint_reason
        log.is_spam = True
        _append_event(log, "COMPLAINT", occurred_at, event_obj or {})
        if log.email_validation:
            log.email_validation.update_reputation("complained")
        _apply_queue_failure(log, complaint_reason)
        return {"delivery_status", "bounced_at", "bounce_type", "bounce_reason", "is_spam", "updated_at"}

    _handle_event("complaint", mail_obj, complaint_obj or {}, processor)


@receiver(open_received)
def ses_open_received(sender, mail_obj, open_obj, raw_message, **kwargs):
    def processor(log: EmailDeliveryLog, occurred_at, event_obj, _mail_obj):
        if not log.opened_at:
            log.opened_at = occurred_at
        if log.delivery_status in {"DELIVERED", "SENT", "OPENED"}:
            log.delivery_status = "OPENED"
        if event_obj:
            log.user_agent = event_obj.get("userAgent") or log.user_agent
            log.ip_address = event_obj.get("ipAddress") or log.ip_address
        _append_event(log, "OPEN", occurred_at, event_obj or {})
        _recalculate_click_metrics(log)
        return {"opened_at", "delivery_status", "user_agent", "ip_address", "open_count", "click_count", "unique_click_count", "updated_at"}

    _handle_event("open", mail_obj, open_obj or {}, processor)


@receiver(click_received)
def ses_click_received(sender, mail_obj, click_obj, raw_message, **kwargs):
    def processor(log: EmailDeliveryLog, occurred_at, event_obj, _mail_obj):
        if not log.clicked_at:
            log.clicked_at = occurred_at
        log.delivery_status = "CLICKED" if log.delivery_status not in {"BOUNCED", "COMPLAINED"} else log.delivery_status
        if event_obj:
            log.user_agent = event_obj.get("userAgent") or log.user_agent
            log.ip_address = event_obj.get("ipAddress") or log.ip_address
        _append_event(log, "CLICK", occurred_at, event_obj or {})
        _recalculate_click_metrics(log)
        return {"clicked_at", "delivery_status", "user_agent", "ip_address", "open_count", "click_count", "unique_click_count", "updated_at"}

    _handle_event("click", mail_obj, click_obj or {}, processor)
