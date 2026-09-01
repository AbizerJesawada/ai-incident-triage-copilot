import csv
import random
from collections import Counter
from pathlib import Path


BASE_DATASET_PATH = Path("sample-data/incidents_training.csv")
OUTPUT_DATASET_PATH = Path(
    "sample-data/incidents_training_300.csv"
)

CATEGORIES = [
    "application_error",
    "database",
    "network",
    "authentication",
]

SEVERITIES = [
    "low",
    "medium",
    "high",
    "critical",
]

TARGET_ROWS_PER_CATEGORY = 75
TARGET_ROWS_PER_SEVERITY = 75

SERVICES_BY_CATEGORY = {
    "application_error": [
        "checkout-api",
        "orders-api",
        "catalog-api",
        "reporting-api",
        "billing-api",
    ],
    "database": [
        "payment-api",
        "orders-api",
        "inventory-api",
        "analytics-api",
        "billing-api",
    ],
    "network": [
        "gateway-api",
        "portal-api",
        "identity-api",
        "notification-api",
        "checkout-api",
    ],
    "authentication": [
        "identity-api",
        "admin-api",
        "portal-api",
        "automation-api",
        "billing-api",
    ],
}

TITLE_TEMPLATES = {
    "application_error": [
        "{service} returns unexpected server errors",
        "{service} request processing fails",
        "{service} cannot complete a customer workflow",
        "{service} has an exception during request handling",
        "{service} returns invalid response data",
    ],
    "database": [
        "{service} cannot obtain a database connection",
        "{service} database queries are failing",
        "{service} cannot write records to PostgreSQL",
        "{service} database operation is timing out",
        "{service} reports a database resource problem",
    ],
    "network": [
        "{service} cannot reach an upstream service",
        "{service} has intermittent network failures",
        "{service} cannot resolve a required hostname",
        "{service} requests fail through the API gateway",
        "{service} has connection timeout errors",
    ],
    "authentication": [
        "{service} users cannot complete sign in",
        "{service} rejects valid access tokens",
        "{service} has an authentication validation error",
        "{service} cannot verify user credentials",
        "{service} has a multi factor authentication problem",
    ],
}

DESCRIPTION_TEMPLATES = {
    "application_error": [
        "The request handler raises an unhandled exception during processing.",
        "A recent code path returns an invalid response to callers.",
        "The service fails while processing a normal customer request.",
        "An application dependency returns data the service cannot process.",
        "The service logs repeated internal errors for the same workflow.",
    ],
    "database": [
        "PostgreSQL has no available connections for the service.",
        "A database query exceeds its allowed execution time.",
        "The database cannot accept a new write from the application.",
        "The connection pool is exhausted during normal traffic.",
        "A required database transaction is rolled back unexpectedly.",
    ],
    "network": [
        "The service cannot establish a connection to its required dependency.",
        "DNS resolution fails for an internal service hostname.",
        "Network requests time out before an upstream response arrives.",
        "The gateway reports failed connections between services.",
        "Intermittent packet loss interrupts requests to an upstream service.",
    ],
    "authentication": [
        "Valid users receive an authentication failure during sign in.",
        "The identity provider rejects a token that should be valid.",
        "A credential verification request fails before login completes.",
        "The multi factor authentication step cannot be completed.",
        "A service account cannot authenticate to a required dependency.",
    ],
}

IMPACT_TEMPLATES = {
    "low": [
        "A small number of requests are affected and retrying usually succeeds.",
        "The issue affects a noncritical workflow with no data loss.",
        "Users can continue working after a short delay.",
    ],
    "medium": [
        "Multiple users experience delays and the affected workflow is degraded.",
        "The issue affects an important feature but a temporary workaround exists.",
        "The service remains available but some requests fail.",
    ],
    "high": [
        "A large group of users cannot complete the affected workflow.",
        "Customer requests fail repeatedly and engineer investigation is needed.",
        "The incident has significant business impact and requires fast action.",
    ],
    "critical": [
        "All users are blocked from a critical workflow and immediate escalation is required.",
        "The service is unavailable for customers and there is no working workaround.",
        "A production-critical operation is failing for every affected request.",
    ],
}


def load_rows(dataset_path: Path) -> list[dict[str, str]]:
    with dataset_path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def choose_label_with_largest_remaining(
    remaining_counts: dict[str, int],
) -> str:
    return max(
        remaining_counts,
        key=lambda label: remaining_counts[label],
    )


def create_demo_row(
    category: str,
    severity: str,
    randomizer: random.Random,
) -> dict[str, str]:
    service_name = randomizer.choice(
        SERVICES_BY_CATEGORY[category]
    )

    title = randomizer.choice(
        TITLE_TEMPLATES[category]
    ).format(service=service_name)

    description = " ".join(
        [
            randomizer.choice(
                DESCRIPTION_TEMPLATES[category]
            ),
            randomizer.choice(
                IMPACT_TEMPLATES[severity]
            ),
        ]
    )

    return {
        "title": title,
        "description": description,
        "service_name": service_name,
        "category": category,
        "severity": severity,
    }


def main() -> None:
    base_rows = load_rows(BASE_DATASET_PATH)

    category_counts = Counter(
        row["category"] for row in base_rows
    )
    severity_counts = Counter(
        row["severity"] for row in base_rows
    )

    category_remaining = {
        category: TARGET_ROWS_PER_CATEGORY
        - category_counts[category]
        for category in CATEGORIES
    }

    severity_remaining = {
        severity: TARGET_ROWS_PER_SEVERITY
        - severity_counts[severity]
        for severity in SEVERITIES
    }

    if any(count < 0 for count in category_remaining.values()):
        raise ValueError(
            "The base dataset already exceeds a category target."
        )

    if any(count < 0 for count in severity_remaining.values()):
        raise ValueError(
            "The base dataset already exceeds a severity target."
        )

    randomizer = random.Random(42)
    generated_rows = []

    while any(category_remaining.values()):
        category = choose_label_with_largest_remaining(
            category_remaining
        )
        severity = choose_label_with_largest_remaining(
            severity_remaining
        )

        generated_rows.append(
            create_demo_row(
                category=category,
                severity=severity,
                randomizer=randomizer,
            )
        )

        category_remaining[category] -= 1
        severity_remaining[severity] -= 1

    all_rows = base_rows + generated_rows

    with OUTPUT_DATASET_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "title",
                "description",
                "service_name",
                "category",
                "severity",
            ],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Base rows: {len(base_rows)}")
    print(f"Generated demo rows: {len(generated_rows)}")
    print(f"Total rows: {len(all_rows)}")
    print(
        "Category counts:",
        Counter(row["category"] for row in all_rows),
    )
    print(
        "Severity counts:",
        Counter(row["severity"] for row in all_rows),
    )
    print(f"Saved dataset to: {OUTPUT_DATASET_PATH}")


if __name__ == "__main__":
    main()