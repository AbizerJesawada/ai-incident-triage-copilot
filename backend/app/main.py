from fastapi import FastAPI

app = FastAPI(
    title="AI Incident Triage and Resolution Copilot API",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-incident-triage-copilot-backend",
    }