import csv
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
import argparse
import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


DATASET_PATH = Path(
    os.getenv(
        "TRAINING_DATASET_PATH",
        "/data/incidents_training.csv",
    )
)
ARTIFACTS_DIR = Path("/app/artifacts")
FEEDBACK_DATASET_PATH = (
    ARTIFACTS_DIR / "engineer_feedback_training.csv"
)
ACTIVE_MODEL_PATH = ARTIFACTS_DIR / "incident_classifier.joblib"
CANDIDATE_METADATA_PATH = (
    ARTIFACTS_DIR / "candidate_incident_classifier_metadata.json"
)


def load_csv_rows(dataset_path: Path) -> list[dict[str, str]]:
    with dataset_path.open(
        encoding="utf-8",
        newline="",
    ) as dataset_file:
        return list(csv.DictReader(dataset_file))

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--exclude-feedback",
        action="store_true",
        help="Train using only the original dataset.",
    )

    return parser.parse_args()


def load_training_rows(include_feedback: bool,) -> tuple[list[dict[str, str]], int, int]:
    base_rows = load_csv_rows(DATASET_PATH)
    feedback_rows = []

    if include_feedback and FEEDBACK_DATASET_PATH.exists():
        feedback_rows = load_csv_rows(FEEDBACK_DATASET_PATH)

    return (
        base_rows + feedback_rows,
        len(base_rows),
        len(feedback_rows),
    )


def build_incident_text(row: dict[str, str]) -> str:
    return " ".join(
        [
            row["title"],
            row["description"],
            row["service_name"],
        ]
    )


def create_logistic_regression_model() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "vectorizer",
                TfidfVectorizer(
                    stop_words="english",
                    ngram_range=(1, 2),
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def create_calibrated_linear_svm_model() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "vectorizer",
                TfidfVectorizer(
                    stop_words="english",
                    ngram_range=(1, 2),
                ),
            ),
            (
                "classifier",
                CalibratedClassifierCV(
                    estimator=LinearSVC(
                        class_weight="balanced",
                        random_state=42,
                    ),
                    method="sigmoid",
                    cv=3,
                ),
            ),
        ]
    )


def train_model(
    texts: list[str],
    labels: list[str],
    model_factory: Callable[[], Pipeline],
) -> tuple[Pipeline, dict]:
    train_texts, test_texts, train_labels, test_labels = (
        train_test_split(
            texts,
            labels,
            test_size=0.25,
            random_state=42,
            stratify=labels,
        )
    )

    model = model_factory()
    model.fit(train_texts, train_labels)

    predicted_labels = model.predict(test_texts)

    metrics = {
        "accuracy": round(
            float(accuracy_score(test_labels, predicted_labels)),
            4,
        ),
        "classification_report": classification_report(
            test_labels,
            predicted_labels,
            output_dict=True,
            zero_division=0,
        ),
        "training_row_count": len(train_texts),
        "test_row_count": len(test_texts),
    }

    return model, metrics


def main() -> None:
    arguments = parse_arguments()

    rows, base_row_count, feedback_row_count = (
        load_training_rows(
            include_feedback=not arguments.exclude_feedback,
        )
    )

    if len(rows) < 8:
        raise ValueError(
            "The training dataset needs at least "
            "eight labeled rows."
        )

    trained_at = datetime.now(timezone.utc)
    model_version = (
        "candidate-incident-classifier-"
        f"{trained_at.strftime('%Y%m%d-%H%M%S')}"
    )

    texts = [build_incident_text(row) for row in rows]
    category_labels = [row["category"] for row in rows]
    severity_labels = [row["severity"] for row in rows]

    category_model, category_metrics = train_model(
        texts=texts,
        labels=category_labels,
        model_factory=create_logistic_regression_model,
    )

    severity_model, severity_metrics = train_model(
        texts=texts,
        labels=severity_labels,
        model_factory=create_calibrated_linear_svm_model,
    )

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    candidate_model_path = (
        ARTIFACTS_DIR / f"{model_version}.joblib"
    )

    joblib.dump(
        {
            "category_model": category_model,
            "severity_model": severity_model,
        },
        candidate_model_path,
    )

    metadata = {
        "trained_at": trained_at.isoformat(),
        "model_version": model_version,
        "promotion_status": "candidate",
        "candidate_model_path": str(candidate_model_path),
        "active_model_path": str(ACTIVE_MODEL_PATH),
        "dataset_path": str(DATASET_PATH),
        "feedback_dataset_path": str(FEEDBACK_DATASET_PATH),
        "engineer_feedback_included": (
            not arguments.exclude_feedback
        ),
        "base_dataset_row_count": base_row_count,
        "feedback_dataset_row_count": feedback_row_count,
        "dataset_row_count": len(rows),
        "model_selection": {
            "category_model": (
                "TF-IDF + Logistic Regression"
            ),
            "severity_model": (
                "TF-IDF + Calibrated Linear SVM"
            ),
        },
        "category_metrics": category_metrics,
        "severity_metrics": severity_metrics,
    }

    CANDIDATE_METADATA_PATH.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print(f"Base dataset rows: {base_row_count}")
    print(f"Engineer feedback rows: {feedback_row_count}")
    print(f"Total training rows: {len(rows)}")
    print(f"Candidate model: {candidate_model_path}")
    print(
        f"Candidate metadata: {CANDIDATE_METADATA_PATH}"
    )
    print(f"Candidate version: {model_version}")
    print("Promotion status: candidate")
    print(
        "Engineer feedback included:",
        not arguments.exclude_feedback,
    )
    print("Category accuracy:", category_metrics["accuracy"])
    print("Severity accuracy:", severity_metrics["accuracy"])
    print(
        "The active API model was not replaced: "
        f"{ACTIVE_MODEL_PATH}"
    )


if __name__ == "__main__":
    main()