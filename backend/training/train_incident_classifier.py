import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


DATASET_PATH = Path("/data/incidents_training.csv")
ARTIFACTS_DIR = Path("/app/artifacts")
MODEL_PATH = ARTIFACTS_DIR / "incident_classifier.joblib"
METADATA_PATH = ARTIFACTS_DIR / "incident_classifier_metadata.json"


def load_training_rows() -> list[dict[str, str]]:
    with DATASET_PATH.open(encoding="utf-8", newline="") as dataset_file:
        return list(csv.DictReader(dataset_file))


def build_incident_text(row: dict[str, str]) -> str:
    return " ".join(
        [
            row["title"],
            row["description"],
            row["service_name"],
        ]
    )


def train_model(
    texts: list[str],
    labels: list[str],
) -> tuple[Pipeline, dict]:
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )

    model = Pipeline(
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
    rows = load_training_rows()

    if len(rows) < 8:
        raise ValueError(
            "The training dataset needs at least eight labeled rows."
        )

    texts = [build_incident_text(row) for row in rows]
    category_labels = [row["category"] for row in rows]
    severity_labels = [row["severity"] for row in rows]

    category_model, category_metrics = train_model(
        texts=texts,
        labels=category_labels,
    )
    severity_model, severity_metrics = train_model(
        texts=texts,
        labels=severity_labels,
    )

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "category_model": category_model,
            "severity_model": severity_model,
        },
        MODEL_PATH,
    )

    metadata = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(DATASET_PATH),
        "dataset_row_count": len(rows),
        "model_path": str(MODEL_PATH),
        "category_metrics": category_metrics,
        "severity_metrics": severity_metrics,
    }

    METADATA_PATH.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print(f"Saved trained model to: {MODEL_PATH}")
    print(f"Saved training metadata to: {METADATA_PATH}")
    print(
        "Category accuracy:",
        category_metrics["accuracy"],
    )
    print(
        "Severity accuracy:",
        severity_metrics["accuracy"],
    )


if __name__ == "__main__":
    main()