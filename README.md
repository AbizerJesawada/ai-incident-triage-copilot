# AI Incident Triage and Resolution Copilot

An agentic AI system for helping engineering teams triage incidents, identify likely causes, retrieve relevant runbooks, correlate incidents with recent changes, and propose grounded remediation actions for human approval.

## Project Goals

The final system will support:

- Incident intake from alerts, logs, and manual reports.
- ML-based incident severity and category classification.
- Confidence-calibrated escalation routing.
- RAG retrieval from runbooks and previous incidents.
- Temporal correlation with recent deployments, configuration changes, and feature flags.
- LLM-generated recommendations with source citations.
- Validation that blocks unverified recommendations from one-click approval.
- Human approval, incident history, and audit trail.
- MLOps and LLMOps evaluation, monitoring, and feedback workflows.

## Current Implementation

The Docker foundation is complete.

Current services:

- **PostgreSQL**: Persistent storage for future incidents, approvals, feedback, audit records, and evaluation data.
- **FastAPI backend**: A minimal API with a health-check endpoint.

## Project Structure

```text
ai-incident-triage-copilot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
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

## Prerequisites

Install:

- Docker Desktop
- WSL 2 on Windows
- Visual Studio Code with the WSL extension

Verify Docker:

```bash
docker --version
docker compose version
docker run hello-world
```

## Environment Configuration

Create a local environment file:

```bash
cp .env.example .env
```

Update the password in `.env`:

```env
POSTGRES_DB=incident_copilot
POSTGRES_USER=incident_user
POSTGRES_PASSWORD=your-private-local-password
```

Do not commit `.env` because it contains private local settings.

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

PostgreSQL should show a `healthy` status.

## Test the Backend

Run this in the project terminal:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected response:

```text
status  : ok
service : ai-incident-triage-copilot-backend
```

Open FastAPI Swagger documentation:

```text
http://localhost:8000/docs
```

## PostgreSQL Access

Open PostgreSQL inside the running container:

```bash
docker compose exec postgres psql -U incident_user -d incident_copilot
```

Check the connected database and user:

```sql
SELECT current_database(), current_user;
```

Exit PostgreSQL:

```sql
\q
```

## Docker Concepts Used

- **Image**: Reusable software blueprint, such as `postgres:16-alpine`.
- **Container**: A running copy created from an image.
- **Docker Compose**: `docker-compose.yml`, which defines and starts project services.
- **Service**: A named container role, such as `postgres` or `backend`.
- **Environment file**: `.env`, which supplies private configuration values.
- **Port mapping**: PostgreSQL uses `5432:5432`; FastAPI uses `8000:8000`.
- **Volume**: `postgres_data` preserves database data after container restarts.
- **Health check**: Confirms PostgreSQL is ready before the backend starts.
- **Network**: Docker Compose creates a private network for container communication.

## Stop Services

Stop containers while preserving PostgreSQL data:

```bash
docker compose down
```

Start them again:

```bash
docker compose up -d
```

The following command deletes the PostgreSQL volume and all database data. Use it only when you intentionally want a fresh database:

```bash
docker compose down -v
```

## Next Steps

1. Add incident database models and migrations.
2. Build incident creation and retrieval API endpoints.
3. Add Redis and Qdrant services.
4. Create the incident triage frontend.
5. Add the ML classifier and confidence-calibrated routing.
6. Add RAG, temporal event correlation, grounded recommendations, and human approval.