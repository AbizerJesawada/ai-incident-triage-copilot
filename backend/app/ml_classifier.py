from functools import lru_cache
from pathlib import Path

import joblib
import json

MODEL_PATH = Path("/app/artifacts/incident_classifier.joblib")


@lru_cache
def load_models() -> dict:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Incident classifier model was not found. "
            "Run the training script first."
        )

    return joblib.load(MODEL_PATH)


def build_incident_text(
    title: str,
    description: str,
    service_name: str,
) -> str:
    return " ".join([title, description, service_name])


def predict_incident(
    title: str,
    description: str,
    service_name: str,
) -> dict[str, object]:
    models = load_models()
    incident_text = build_incident_text(
        title=title,
        description=description,
        service_name=service_name,
    )

    category_model = models["category_model"]
    severity_model = models["severity_model"]

    category_prediction = category_model.predict([incident_text])[0]
    severity_prediction = severity_model.predict([incident_text])[0]

    category_confidence = float(
        category_model.predict_proba([incident_text]).max()
    )
    severity_confidence = float(
        severity_model.predict_proba([incident_text]).max()
    )

    return {
        "predicted_category": category_prediction,
        "predicted_severity": severity_prediction,
        "category_confidence": round(category_confidence, 4),
        "severity_confidence": round(severity_confidence, 4),
    }

METADATA_PATH = Path(
    "/app/artifacts/incident_classifier_metadata.json"
)


def get_model_metadata() -> dict:
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            "Incident classifier metadata was not found. "
            "Run the training script first."
        )

    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))