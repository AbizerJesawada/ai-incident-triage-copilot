import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.models import Incident


SLACK_POST_MESSAGE_URL = (
    "https://slack.com/api/chat.postMessage"
)


def send_engineer_review_alert(
    incident: Incident,
) -> dict[str, str] | None:
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    channel_id = os.getenv("SLACK_CHANNEL_ID")

    if not bot_token or not channel_id:
        return None

    message = (
        ":rotating_light: *Engineer review required*\n"
        f"*Incident:* {incident.title}\n"
        f"*Service:* {incident.service_name}\n"
        f"*Incident ID:* {incident.id}\n"
        f"*Reason:* {incident.triage_reason}\n\n"
        "React with :eyes: after you have reviewed this alert."
    )

    request = Request(
        SLACK_POST_MESSAGE_URL,
        data=json.dumps(
            {
                "channel": channel_id,
                "text": message,
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=5) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )
    except (HTTPError, URLError):
        return None

    if not payload.get("ok"):
        return None

    return {
        "channel_id": str(payload["channel"]),
        "message_ts": str(payload["ts"]),
    }