Replace the full `README.md` with this shorter version:

````md
# AI Incident Triage and Resolution Copilot

An agentic AI system that helps engineering teams triage production incidents, identify likely causes, correlate incidents with recent system changes, and require human approval for risky decisions.

## What It Does

```text
Incident report
    ↓
ML predicts category, severity, and confidence
    ↓
Confidence-based router selects standard or escalated handling
    ↓
Recent same-service changes are correlated
    ↓
Engineer reviews risky incidents
    ↓
Data, decisions, and history are stored in PostgreSQL
```

## Current Features

- Dockerized FastAPI backend and PostgreSQL database
- Persistent incident storage
- Incident create, list, filter, retrieve, and update APIs
- Change-event storage for deployments, configuration changes, and feature flags
- Temporal correlation between incidents and recent same-service changes
- ML baseline using TF-IDF and Logistic Regression
- Category and severity predictions with confidence scores
- Confidence-based escalation routing
- Saved automated triage results for each incident
- Re-triage endpoint for existing incidents
- Engineer review history and review queue

## Architecture

```text
User / Future Frontend
        ↓
FastAPI Backend
        ├── PostgreSQL: incidents, change events, reviews
        ├── ML classifier: category and severity prediction
        └── Escalation router: review and workflow decision
```

## Technology Stack

- FastAPI and Uvicorn
- PostgreSQL 16
- SQLAlchemy and Psycopg
- Docker and Docker Compose
- scikit-learn
- TF-IDF and Logistic Regression
- Future: Next.js, Redis, Qdrant, RAG, LLM, LangGraph

## Project Structure

```text
ai-incident-triage-copilot/
├── backend/
│   ├── app/
│   ├── artifacts/
│   ├── migrations/
│   ├── training/
│   ├── Dockerfile
│   └── requirements.txt
├── sample-data/
├── .env.example
├── docker-compose.yml
└── README.md
```

## Local Setup

Create local settings:

```bash
cp .env.example .env
```

Set values in `.env`:

```env
POSTGRES_DB=incident_copilot
POSTGRES_USER=incident_user
POSTGRES_PASSWORD=your-private-local-password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

Start the application:

```bash
docker compose up --build -d
docker compose ps
```

Open API documentation:

```text
http://localhost:8000/docs
```

Stop services while keeping database data:

```bash
docker compose down
```

Do not use `docker compose down -v` unless you intentionally want to delete all local database data.

## Main API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Backend health check |
| `POST` | `/incidents` | Create and automatically triage an incident |
| `GET` | `/incidents` | List and filter incidents |
| `GET` | `/incidents/{incident_id}` | Get one incident |
| `PATCH` | `/incidents/{incident_id}` | Update incident severity or status |
| `POST` | `/incidents/{incident_id}/triage` | Re-run ML triage for an incident |
| `POST` | `/change-events` | Create a deployment/config/flag event |
| `GET` | `/change-events` | List and filter change events |
| `GET` | `/incidents/{incident_id}/related-change-events` | Find nearby same-service changes |
| `POST` | `/incidents/{incident_id}/reviews` | Save an engineer review |
| `GET` | `/incidents/{incident_id}/reviews` | Get review history |
| `GET` | `/review-queue` | List unresolved incidents requiring review |
| `POST` | `/ml/classify-incident` | Test ML prediction |
| `POST` | `/ml/route-incident` | Test prediction and routing |
| `GET` | `/ml/model-metadata` | View model metrics |

## ML Baseline

The training file is:

```text
sample-data/incidents_training.csv
```

Training pipeline:

```text
Incident title + description + service
        ↓
TF-IDF text features
        ↓
Logistic Regression models
        ↓
Category + severity + confidence
```

Train the model:

```bash
docker compose build backend
docker compose run --rm backend python training/train_incident_classifier.py
```

The current model is a learning baseline with a small synthetic dataset. Predictions are advisory; high-severity or low-confidence predictions require human review.

## Escalation Rules

```text
Critical severity
→ critical escalation and mandatory review

Low confidence
→ uncertain escalation and mandatory review

High severity
→ priority review

Low/medium severity with high confidence
→ standard triage
```

## Human Review

Risky, unresolved incidents appear in:

```text
GET /review-queue
```

Engineers can submit:

```text
approved
needs_investigation
rejected
```

Each review records the reviewer, decision, note, and timestamp for audit history.

## Next Steps

1. Compare Logistic Regression with calibrated Linear SVM.
2. Add incident deduplication and an incident timeline.
3. Add Redis and Qdrant.
4. Add RAG runbook retrieval and similar-incident search.
5. Add cited LLM recommendations and approval controls.
6. Build the Next.js frontend and notification workflow.
````

## MLOps Feedback and Model Promotion

The system keeps risky or low-confidence incidents in an engineer review workflow.

1. An engineer can save confirmed labels using `actual_category` and `actual_severity`.
2. Confirmed reviews are exported from PostgreSQL into a feedback CSV.
3. New models are trained as candidates, not activated automatically.
4. Candidate metrics are reviewed before promotion.
5. An approved candidate is manually promoted to the active API model.

This prevents an untested or weaker model from replacing the current active model.

## Temporal Correlation

When an incident is created or re-triaged, the system checks recent change events for the same service.

- Changes within 30 minutes are saved as correlation evidence.
- Deployments close to an incident receive higher scores.
- The correlation timeline shows changes before and after an incident.
- Root-cause hypotheses use only changes that occurred before the incident.
- A hypothesis is a lead for investigation, not confirmed root cause.

## Grounded Remediation Recommendations

The system generates remediation recommendations only from strong, pre-incident correlation evidence.

- Each recommendation includes the supporting evidence and source change event.
- New recommendations start with `pending` status.
- An engineer can approve or reject a pending recommendation.
- Approved recommendations are recorded with reviewer details and time.
- The system never runs a rollback or remediation action automatically.

## Grounded LLM Briefings

The backend can generate an engineer briefing with Gemini from verified incident data.

- Gemini receives the incident, saved correlation evidence, and recommendations.
- The API returns the original evidence sources with the LLM briefing.
- Deployment IDs mentioned by Gemini are checked against the supplied evidence.
- A briefing is marked `verified` only when it contains no unsupported evidence IDs.
- The LLM cannot execute rollbacks or any external remediation action.
- Engineers remain responsible for confirming the root cause and approving recommendations.

## Day 12: LLM Observability

Each Gemini incident briefing is logged in PostgreSQL.

The log stores:
- Model name
- Success or error status
- Grounding status
- Response latency
- Prompt and response token counts

Endpoints:
- `GET /incidents/{incident_id}/llm-generation-logs`
- `GET /llm-generation-summary`

## Day 13: Engineer Notifications

When an incident requires human review, the system automatically creates a pending engineer notification.

Endpoints:
- `GET /engineer-notifications?status=pending`
- `PATCH /engineer-notifications/{notification_id}/read`

Current notifications are stored inside PostgreSQL. Slack or email delivery will be added later.