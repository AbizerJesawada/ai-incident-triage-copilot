import hashlib
import hmac
import os
import time

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EngineerNotification

def is_valid_slack_request(
    raw_body: bytes,
    timestamp: str | None,
    signature: str | None,
) -> bool:
    signing_secret = os.getenv("SLACK_SIGNING_SECRET")

    if not signing_secret or not timestamp or not signature:
        return False

    try:
        request_age_seconds = abs(
            time.time() - int(timestamp)
        )
    except ValueError:
        return False

    if request_age_seconds > 300:
        return False

    signing_text = (
        f"v0:{timestamp}:".encode("utf-8")
        + raw_body
    )

    expected_signature = "v0=" + hmac.new(
        signing_secret.encode("utf-8"),
        signing_text,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature,
    )


def acknowledge_eyes_reaction(
    db: Session,
    event: dict,
) -> bool:
    if event.get("type") != "reaction_added":
        return False

    if event.get("reaction") != "eyes":
        return False

    item = event.get("item", {})

    if item.get("type") != "message":
        return False

    notification = db.scalar(
        select(EngineerNotification)
        .where(
            EngineerNotification.slack_channel_id
            == item.get("channel")
        )
        .where(
            EngineerNotification.slack_message_ts
            == item.get("ts")
        )
    )

    if notification is None:
        return False

    if notification.acknowledged_at is not None:
        return True

    acknowledged_at = datetime.now(timezone.utc)

    notification.status = "read"
    notification.read_at = (
        notification.read_at or acknowledged_at
    )
    notification.acknowledged_by = str(event.get("user"))
    notification.acknowledged_at = acknowledged_at

    db.commit()

    return True