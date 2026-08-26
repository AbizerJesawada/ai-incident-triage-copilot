import os
import re
from google import genai


DEFAULT_MODEL = "gemini-3.5-flash"


def generate_incident_briefing(
    incident_context: str,
) -> str:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an incident-response assistant.

Write a concise briefing for an engineer using only the
verified context below.

Rules:
- Do not invent facts, deployments, logs, or root causes.
- Treat every correlation as possible, not confirmed.
- Mention evidence IDs such as deployment reference IDs when present.
- Do not recommend automatic actions.
- State that engineer verification is required before remediation.

Verified incident context:
{incident_context}
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
        contents=prompt,
    )

    if not response.text:
        raise ValueError(
            "Gemini returned an empty incident briefing."
        )

    return response.text.strip()

def validate_briefing_evidence(
    briefing: str,
    allowed_reference_ids: list[str],
) -> dict[str, list[str]]:
    mentioned_reference_ids = sorted(
        set(
            re.findall(
                r"\b(?:deploy|config|flag)-[A-Za-z0-9_-]+\b",
                briefing,
                flags=re.IGNORECASE,
            )
        )
    )

    allowed_ids = {
        reference_id.lower()
        for reference_id in allowed_reference_ids
    }

    unsupported_reference_ids = [
        reference_id
        for reference_id in mentioned_reference_ids
        if reference_id.lower() not in allowed_ids
    ]

    return {
        "mentioned_reference_ids": mentioned_reference_ids,
        "unsupported_reference_ids": unsupported_reference_ids,
    }