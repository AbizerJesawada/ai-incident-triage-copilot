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