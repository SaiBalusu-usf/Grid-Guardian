"""Notification tool for sending alerts through various channels (mock implementation)."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

logger = logging.getLogger(__name__)


async def send_notification(
    channel: str,
    message: str,
    recipients: list[str] | None = None,
    severity: str = "info",
) -> dict:
    """Send a notification through the specified channel.

    Args:
        channel: Delivery channel (sms, email, push, broadcast, siren).
        message: Notification message body.
        recipients: List of recipient identifiers. Empty means broadcast.
        severity: Severity level (info, warning, high, critical).

    Returns:
        Notification delivery receipt.
    """
    if recipients is None:
        recipients = []

    notification_id = str(uuid4())
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    logger.info(
        "Notification sent: id=%s channel=%s severity=%s recipients=%d",
        notification_id,
        channel,
        severity,
        len(recipients) if recipients else -1,
    )

    return {
        "notification_id": notification_id,
        "channel": channel,
        "status": "sent",
        "timestamp": timestamp,
        "recipients_count": len(recipients) if recipients else 0,
        "severity": severity,
        "message_preview": message[:120] + ("..." if len(message) > 120 else ""),
    }
