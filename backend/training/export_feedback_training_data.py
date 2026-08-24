import csv
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import engine
from app.models import Incident, IncidentReview


OUTPUT_PATH = Path("/app/artifacts/engineer_feedback_training.csv")

FIELDNAMES = [
    "title",
    "description",
    "service_name",
    "category",
    "severity",
]


def main() -> None:
    statement = (
        select(IncidentReview, Incident)
        .join(
            Incident,
            IncidentReview.incident_id == Incident.id,
        )
        .where(IncidentReview.actual_category.is_not(None))
        .where(IncidentReview.actual_severity.is_not(None))
        .order_by(IncidentReview.created_at.desc())
    )

    training_rows = []
    processed_incident_ids = set()

    with Session(engine) as db:
        review_rows = db.execute(statement).all()

        for review, incident in review_rows:
            if incident.id in processed_incident_ids:
                continue

            processed_incident_ids.add(incident.id)

            training_rows.append(
                {
                    "title": incident.title,
                    "description": incident.description,
                    "service_name": incident.service_name,
                    "category": review.actual_category,
                    "severity": review.actual_severity,
                }
            )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=FIELDNAMES,
        )
        writer.writeheader()
        writer.writerows(training_rows)

    print(
        f"Exported {len(training_rows)} confirmed "
        f"engineer feedback examples to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()