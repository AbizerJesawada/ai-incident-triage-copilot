import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.models import Incident


def send_engineer_review_alert(
    incident: Incident,
) -> bool:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        return False

    message = (
        ":rotating_light: Engineer review required\n"
        f"*Incident:* {incident.title}\n"
        f"*Service:* {incident.service_name}\n"
        f"*Incident ID:* {incident.id}\n"
        f"*Reason:* {incident.triage_reason}"
    )

    request = Request(
        webhook_url,
        data=json.dumps({"text": message}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=5) as response:
            return response.status == 200
    except (HTTPError, URLError):
        return False