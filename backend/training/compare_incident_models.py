import csv
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


DATASET_PATH = Path(
    os.getenv(
        "TRAINING_DATASET_PATH",
        "/data/incidents_training.csv",
    )
)
REPORT_PATH = Path("/app/artifacts/model_comparison_report.json")


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


def evaluate_model(
    model: Pipeline,
    train_texts: list[str],
    test_texts: list[str],
    train_labels: list[str],
    test_labels: list[str],
) -> dict[str, object]:
    training_start = perf_counter()
    model.fit(train_texts, train_labels)
    training_time_ms = round(
        (perf_counter() - training_start) * 1000,
        2,
    )

    prediction_start = perf_counter()
    predicted_labels = model.predict(test_texts)
    prediction_time_ms = round(
        (perf_counter() - prediction_start) * 1000,
        2,
    )

    return {
        "accuracy": round(
            float(accuracy_score(test_labels, predicted_labels)),
            4,
        ),
        "macro_f1": round(
            float(
                f1_score(
                    test_labels,
                    predicted_labels,
                    average="macro",
                    zero_division=0,
                )
            ),
            4,
        ),
        "training_time_ms": training_time_ms,
        "test_prediction_time_ms": prediction_time_ms,
        "classification_report": classification_report(
            test_labels,
            predicted_labels,
            output_dict=True,
            zero_division=0,
        ),
    }


def compare_target(
    texts: list[str],
    labels: list[str],
) -> dict[str, object]:
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )

    return {
        "training_row_count": len(train_texts),
        "test_row_count": len(test_texts),
        "logistic_regression": evaluate_model(
            model=create_logistic_regression_model(),
            train_texts=train_texts,
            test_texts=test_texts,
            train_labels=train_labels,
            test_labels=test_labels,
        ),
        "calibrated_linear_svm": evaluate_model(
            model=create_calibrated_linear_svm_model(),
            train_texts=train_texts,
            test_texts=test_texts,
            train_labels=train_labels,
            test_labels=test_labels,
        ),
    }


def main() -> None:
    rows = load_training_rows()

    texts = [build_incident_text(row) for row in rows]

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(DATASET_PATH),
        "dataset_row_count": len(rows),
        "category_comparison": compare_target(
            texts=texts,
            labels=[row["category"] for row in rows],
        ),
        "severity_comparison": compare_target(
            texts=texts,
            labels=[row["severity"] for row in rows],
        ),
    }

    REPORT_PATH.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(f"Saved model comparison report to: {REPORT_PATH}")

    for target_name in [
        "category_comparison",
        "severity_comparison",
    ]:
        comparison = report[target_name]

        print(f"\n{target_name}:")
        print(
            "Logistic Regression accuracy:",
            comparison["logistic_regression"]["accuracy"],
        )
        print(
            "Calibrated Linear SVM accuracy:",
            comparison["calibrated_linear_svm"]["accuracy"],
        )


if __name__ == "__main__":
    main()