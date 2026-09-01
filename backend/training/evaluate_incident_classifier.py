import csv
import json
from pathlib import Path
import os
import joblib
from sklearn.metrics import accuracy_score


EVALUATION_DATASET_PATH = Path(
    "/data/incident_evaluation.csv"
)

CANDIDATE_METADATA_PATH = Path(
    "/app/artifacts/candidate_incident_classifier_metadata.json"
)


def build_incident_text(row: dict[str, str]) -> str:
    return " ".join(
        [
            row["title"],
            row["description"],
            row["service_name"],
        ]
    )


def load_evaluation_rows() -> list[dict[str, str]]:
    with EVALUATION_DATASET_PATH.open(
        encoding="utf-8",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def load_candidate_model_path() -> Path:
    model_path = os.getenv("MODEL_PATH")

    if model_path:
        return Path(model_path)

    metadata = json.loads(
        CANDIDATE_METADATA_PATH.read_text(
            encoding="utf-8",
        )
    )

    return Path(metadata["candidate_model_path"])


def main() -> None:
    rows = load_evaluation_rows()
    candidate_model_path = load_candidate_model_path()

    model_bundle = joblib.load(candidate_model_path)

    texts = [
        build_incident_text(row)
        for row in rows
    ]

    actual_categories = [
        row["category"]
        for row in rows
    ]

    actual_severities = [
        row["severity"]
        for row in rows
    ]

    predicted_categories = model_bundle[
        "category_model"
    ].predict(texts)

    predicted_severities = model_bundle[
        "severity_model"
    ].predict(texts)

    category_accuracy = accuracy_score(
        actual_categories,
        predicted_categories,
    )

    severity_accuracy = accuracy_score(
        actual_severities,
        predicted_severities,
    )

    print(f"Candidate model: {candidate_model_path}")
    print(f"Evaluation rows: {len(rows)}")
    print(
        "Category accuracy:",
        round(float(category_accuracy), 4),
    )
    print(
        "Severity accuracy:",
        round(float(severity_accuracy), 4),
    )
    print()
    print("Predictions:")

    for index, row in enumerate(rows):
        print(f"- {row['title']}")
        print(
            f"  Category: actual={actual_categories[index]}, "
            f"predicted={predicted_categories[index]}"
        )
        print(
            f"  Severity: actual={actual_severities[index]}, "
            f"predicted={predicted_severities[index]}"
        )


if __name__ == "__main__":
    main()