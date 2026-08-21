# AI Incident Triage and Resolution Copilot

An agentic AI system that helps engineering teams triage production incidents, identify likely causes, correlate incidents with recent system changes, retrieve relevant runbooks, and propose grounded remediation actions for human approval.

## Problem

During an incident, engineers often need to search alerts, logs, runbooks, deployment history, and previous incidents manually. This takes time when services are already degraded.

This project will reduce time-to-triage while keeping engineers in control. It will combine incident data, ML classification, retrieval-augmented generation (RAG), temporal correlation, cited recommendations, and approval workflows.

## Planned Capabilities

- Create and manage incident records.
- Classify incident category and severity using ML.
- Use confidence-calibrated routing for escalation decisions.
- Retrieve relevant runbooks and similar incidents with RAG.
- Correlate incidents with recent deployments, configuration changes, and feature flags.
- Generate remediation recommendations with evidence citations.
- Block unverified recommendations from one-click approval.
- Support human review, approval, feedback, and audit trails.
- Track MLOps and LLMOps metrics, evaluations, latency, cost, and feedback.

## Current Implementation

The project currently includes:

- Docker Compose development environment.
- PostgreSQL database with persistent Docker storage.
- FastAPI backend running in Docker.
- PostgreSQL health check before backend startup.
- Incident database model and `incidents` table.
- Incident creation, listing, retrieval, and partial update APIs.
- FastAPI Swagger documentation.

## Architecture

```text
User / Future Frontend
        |
        v
FastAPI Backend
        |
        v
PostgreSQL Database
        |
        v
Persistent Docker Volume: postgres_data
```

Later architecture:

```text
Alert / Log / Manual Incident
        |
        v
ML Classifier: category + severity + confidence
        |
        v
Confidence-Based Escalation Router
        |
        +--> Recent deploy/config/feature-flag correlation
        |
        +--> RAG retrieval: runbooks + historical incidents
        |
        v
LLM with structured, cited recommendations
        |
        v
Citation validation and human approval
        |
        v
Incident timeline, feedback, and postmortem
```

## Project Structure

```text
ai-incident-triage-copilot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── Dockerfile
│   └── requirements.txt
├── docs/
├── frontend/
├── sample-data/
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Technology Stack

- **Backend:** FastAPI, Uvicorn
- **Database:** PostgreSQL 16
- **ORM:** SQLAlchemy
- **PostgreSQL driver:** Psycopg
- **Containerization:** Docker and Docker Compose
- **Future frontend:** Next.js
- **Future ML:** scikit-learn
- **Future vector search:** Qdrant
- **Future cache and background tasks:** Redis
- **Future orchestration:** LangGraph
- **Future LLM and RAG:** LLM API, embeddings, retrieval pipeline

## Prerequisites

Install:

- Docker Desktop
- WSL 2 on Windows
- Visual Studio Code with the WSL extension
- Git

Verify Docker:

```bash
docker --version
docker compose version
docker run hello-world
```

## Environment Configuration

Create your local environment file:

```bash
cp .env.example .env
```

Set a private local database password in `.env`:

```env
POSTGRES_DB=incident_copilot
POSTGRES_USER=incident_user
POSTGRES_PASSWORD=your-private-local-password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

Do not commit `.env`. It contains private local configuration and is ignored by Git.

## Start the Application

Build and start PostgreSQL and the FastAPI backend:

```bash
docker compose up --build -d
```

Check service status:

```bash
docker compose ps
```

Expected services:

```text
incident-copilot-postgres
incident-copilot-backend
```

PostgreSQL should have a `healthy` status.

## Backend Health Check

Run:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected response:

```text
status  : ok
service : ai-incident-triage-copilot-backend
```

## API Documentation

FastAPI automatically provides Swagger documentation:

```text
http://localhost:8000/docs
```

## Incident API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Check backend health |
| `POST` | `/incidents` | Create a new incident |
| `GET` | `/incidents` | List all incidents |
| `GET` | `/incidents/{incident_id}` | Get one incident by ID |
| `PATCH` | `/incidents/{incident_id}` | Update incident severity or status |

### Create an Incident

Use `POST /incidents` with:

```json
{
  "title": "Payment API errors",
  "description": "Customers receive 500 errors during checkout.",
  "service_name": "payment-api",
  "severity": "high",
  "source": "monitoring_alert"
}
```

The backend generates:

- A unique incident ID.
- Default status: `open`.
- `created_at` timestamp.
- `updated_at` timestamp.

### Update an Incident

Use `PATCH /incidents/{incident_id}` with only the fields to change:

```json
{
  "severity": "critical",
  "status": "investigating"
}
```

## PostgreSQL Access

Open the PostgreSQL terminal inside its Docker container:

```bash
docker compose exec postgres psql -U incident_user -d incident_copilot
```

List tables:

```sql
\dt
```

Exit PostgreSQL:

```sql
\q
```

## Docker Concepts Used

- **Image:** Reusable software blueprint, such as `postgres:16-alpine`.
- **Container:** A running instance of an image.
- **Dockerfile:** Instructions for building the custom FastAPI backend image.
- **Docker Compose:** `docker-compose.yml`, which defines and starts project services.
- **Service:** A named container role, such as `postgres` or `backend`.
- **Environment file:** `.env`, which supplies private configuration to containers.
- **Port mapping:** `5432:5432` exposes PostgreSQL; `8000:8000` exposes FastAPI.
- **Named volume:** `postgres_data` keeps database data after containers restart.
- **Health check:** Ensures PostgreSQL is ready before FastAPI starts.
- **Network:** Docker Compose creates a private network for container-to-container communication.

## Stop Services

Stop containers while keeping database data:

```bash
docker compose down
```

Start them again:

```bash
docker compose up -d
```

The following command deletes the database volume and all stored data. Use it only when intentionally resetting local development data:

```bash
docker compose down -v
```

## Next Steps

1. Add database migrations with Alembic.
2. Add incident validation, filtering, and pagination.
3. Add deployment, configuration change, and feature flag event models.
4. Add temporal correlation between incidents and recent events.
5. Add Redis and Qdrant to Docker Compose.
6. Add ML incident classification and calibrated confidence routing.
7. Add RAG retrieval from runbooks and historical incidents.
8. Add structured, cited LLM recommendations and citation validation.
9. Add human approval, feedback, evaluation, and audit workflows.
10. Build the Next.js incident triage frontend.



Copy this entire section into `README.md` before `## Next Steps`:

````md
## Day 3: Incident Filtering and Temporal Change Correlation

Day 3 adds the first investigation features to the incident triage backend.

The system can now:

- Filter incidents by severity, status, and affected service.
- Store important system changes as change events.
- Filter change events by service and event type.
- Find change events that occurred close to an incident.
- Validate incident severity, incident status, and event-type values.

### Incident Filtering

The incident list endpoint supports filters so the frontend does not need to receive every incident.

| Filter | Example |
|---|---|
| Severity | `GET /incidents?severity=critical` |
| Status | `GET /incidents?status=investigating` |
| Service | `GET /incidents?service_name=payment-api` |
| Maximum results | `GET /incidents?limit=10` |

Filters can be combined:

```text
GET /incidents?service_name=payment-api&status=investigating
```

### Change Events

A change event records an important change to a service that might be connected to a later incident.

Supported change-event types:

- `deployment`
- `configuration_change`
- `feature_flag`

Example:

```json
{
  "service_name": "payment-api",
  "event_type": "deployment",
  "description": "Deployed payment-api version 2.4 before checkout errors began.",
  "reference_id": "deploy-482",
  "occurred_at": "2026-08-19T17:35:00Z"
}
```

Change-event endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/change-events` | Create a change event |
| `GET` | `/change-events` | List change events |
| `GET` | `/change-events?service_name=payment-api` | List events for one service |
| `GET` | `/change-events?event_type=deployment` | List deployment events |

### Temporal Correlation

Temporal correlation helps an engineer answer:

> What changed shortly before this incident started?

The endpoint is:

```text
GET /incidents/{incident_id}/related-change-events
```

It performs these steps:

1. Finds the specific incident using its ID.
2. Reads the incident's affected service and creation time.
3. Searches for change events from the same service.
4. Keeps events inside the selected time window.
5. Returns those events as possible investigation clues.

Example:

```text
17:35 - payment-api deployment
17:40 - payment-api checkout incident
```

Request:

```text
GET /incidents/3fe2b29e-1e63-4d13-ad66-98cb72e15aad/related-change-events?window_minutes=30
```

Result:

```text
The payment-api deployment happened five minutes before the incident.
It is a possible related change that an engineer should investigate.
```

Temporal correlation does not prove that a change caused an incident. It identifies relevant recent changes for investigation.

### API Validation

The API now accepts only consistent values.

Incident severity:

```text
unknown
low
medium
high
critical
```

Incident status:

```text
open
investigating
resolved
```

Change-event type:

```text
deployment
configuration_change
feature_flag
```

If a user sends an invalid value, such as:

```json
{
  "severity": "very-urgent"
}
```

the API rejects the request with HTTP status code `422`.

### Day 3 Verification

Day 3 was verified through FastAPI Swagger at:

```text
http://localhost:8000/docs
```

Verified behaviors:

- Incident filters return only matching incidents.
- Change events can be created and listed.
- Related change events are found by incident ID, service name, and time window.
- Invalid severity values are rejected.
- PostgreSQL continues to store incident and change-event data in the Docker volume.
````

Add this complete Day 4 section to `README.md` before `## Next Steps`:

````md
## Day 4: ML Incident Classification Baseline

Day 4 adds the first machine-learning baseline for incident triage.

The backend can now classify new incident text into:

- A predicted incident category
- A predicted severity level
- A confidence score for each prediction

### Training Dataset

The training dataset is:

```text
sample-data/incidents_training.csv
```

It contains synthetic labeled examples with these fields:

```text
title
description
service_name
category
severity
```

Supported categories:

```text
application_error
database
network
authentication
```

Supported severity levels:

```text
low
medium
high
critical
```

### ML Pipeline

The ML pipeline is:

```text
Incident title + description + service name
        ↓
TF-IDF vectorizer converts text into numeric features
        ↓
Logistic Regression category model
        ↓
Predicted category + probability

Incident title + description + service name
        ↓
TF-IDF vectorizer converts text into numeric features
        ↓
Logistic Regression severity model
        ↓
Predicted severity + probability
```

Two models are trained because category and severity answer different questions:

```text
Category: What kind of incident is this?
Severity: How serious is this incident?
```

### Train the Models

Build the backend image:

```bash
docker compose build backend
```

Train both models inside Docker:

```bash
docker compose run --rm backend python training/train_incident_classifier.py
```

Training reads:

```text
/data/incidents_training.csv
```

and saves generated artifacts locally:

```text
backend/artifacts/incident_classifier.joblib
backend/artifacts/incident_classifier_metadata.json
```

The trained model files are ignored by Git because they are generated outputs.

### ML API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/ml/classify-incident` | Predict incident category, severity, and confidence |
| `GET` | `/ml/model-metadata` | View training data details and evaluation metrics |

Example classification request:

```json
{
  "title": "Database connection pool exhausted",
  "description": "New payment requests cannot get a PostgreSQL connection and checkout is failing.",
  "service_name": "payment-api"
}
```

Example response:

```json
{
  "predicted_category": "database",
  "predicted_severity": "critical",
  "category_confidence": 0.3581,
  "severity_confidence": 0.3935
}
```

### Baseline Evaluation

The first training run used 32 synthetic examples:

```text
Training rows: 24
Test rows: 8
Category accuracy: 0.50
Severity accuracy: 0.125
```

These results are intentionally treated as a weak baseline, not production-quality performance.

The small synthetic dataset has too few varied examples, especially for reliable severity prediction. Therefore, ML predictions must remain advisory and require human review.

### MLOps Learning

The project now records:

- Training timestamp
- Dataset path
- Dataset row count
- Training and test row counts
- Category accuracy and classification report
- Severity accuracy and classification report

This makes model quality visible and traceable. Later improvements will include larger data, model comparison, probability calibration, monitoring, feedback, and retraining.
````

## Day 5: Confidence-Based Escalation Routing

Day 5 adds safety routing after ML classification.

The ML model predicts incident category, severity, and confidence. The escalation router then decides whether the incident can follow standard triage or needs stronger analysis and mandatory engineer review.

### Routing Rules

| Condition | Route | Model Tier | Human Review |
|---|---|---|---|
| Predicted severity is `critical` | `critical_escalation` | `strong` | Required |
| Category or severity confidence is below `0.70` | `uncertain_escalation` | `strong` | Required |
| Predicted severity is `high` | `high_priority_review` | `strong` | Required |
| Low or medium severity with sufficient confidence | `standard_triage` | `standard` | Not required |

### Routing API

```text
POST /ml/route-incident
```

This endpoint:

1. Receives a title, description, and service name.
2. Uses the ML models to predict category and severity.
3. Reads both confidence scores.
4. Applies the routing rules.
5. Returns the recommended workflow and review requirement.

Example request:

```json
{
  "title": "Database connection pool exhausted",
  "description": "New payment requests cannot get a PostgreSQL connection and checkout is failing.",
  "service_name": "payment-api"
}
```

Example response:

```json
{
  "predicted_category": "database",
  "predicted_severity": "critical",
  "category_confidence": 0.3581,
  "severity_confidence": 0.3935,
  "route": "critical_escalation",
  "model_tier": "strong",
  "human_review_required": true,
  "reason": "The incident is predicted as critical, so it requires strong analysis and mandatory engineer review."
}
```

### Why This Matters

The system does not blindly trust an ML prediction.

```text
High severity
or
Low model confidence
        ↓
Escalate to stronger analysis and require an engineer
```

This reduces the risk of an uncertain model making an unsafe operational decision.