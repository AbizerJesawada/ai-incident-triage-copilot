import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ARTIFACTS_DIR = Path("/app/artifacts")
CANDIDATE_METADATA_PATH = (
    ARTIFACTS_DIR / "candidate_incident_classifier_metadata.json"
)
ACTIVE_MODEL_PATH = ARTIFACTS_DIR / "incident_classifier.joblib"
ACTIVE_METADATA_PATH = (
    ARTIFACTS_DIR / "incident_classifier_metadata.json"
)


def main() -> None:
    if not CANDIDATE_METADATA_PATH.exists():
        raise FileNotFoundError(
            "Candidate metadata file was not found."
        )

    candidate_metadata = json.loads(
        CANDIDATE_METADATA_PATH.read_text(encoding="utf-8")
    )

    candidate_model_path = Path(
        candidate_metadata["candidate_model_path"]
    )

    if not candidate_model_path.exists():
        raise FileNotFoundError(
            f"Candidate model was not found: {candidate_model_path}"
        )

    approved_at = datetime.now(timezone.utc).isoformat()

    shutil.copy2(candidate_model_path, ACTIVE_MODEL_PATH)

    active_metadata = {
        **candidate_metadata,
        "promotion_status": "active",
        "promoted_at": approved_at,
        "active_model_path": str(ACTIVE_MODEL_PATH),
    }

    ACTIVE_METADATA_PATH.write_text(
        json.dumps(active_metadata, indent=2),
        encoding="utf-8",
    )

    print(
        "Promoted candidate model to active model:"
        f" {candidate_metadata['model_version']}"
    )
    print(f"Active model path: {ACTIVE_MODEL_PATH}")
    print(f"Active metadata path: {ACTIVE_METADATA_PATH}")


if __name__ == "__main__":
    main()