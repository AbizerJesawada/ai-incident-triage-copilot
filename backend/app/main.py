from contextlib import asynccontextmanager
from uuid import UUID
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Incident
from app.schemas import IncidentCreate, IncidentResponse, IncidentUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI Incident Triage and Resolution Copilot API",
    lifespan=lifespan,
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-incident-triage-copilot-backend",
    }


@app.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_incident(
    incident_data: IncidentCreate,
    db: Session = Depends(get_db),
) -> Incident:
    incident = Incident(**incident_data.model_dump())

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident

@app.get(
    "/incidents",
    response_model=list[IncidentResponse],
)
def list_incidents(
    db: Session = Depends(get_db),
) -> list[Incident]:
    statement = select(Incident).order_by(
        Incident.created_at.desc(),
    )

    return list(db.scalars(statement).all())

@app.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
)
def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
) -> Incident:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    return incident

@app.patch(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
)
def update_incident(
    incident_id: UUID,
    incident_data: IncidentUpdate,
    db: Session = Depends(get_db),
) -> Incident:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    for field_name, value in incident_data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(incident, field_name, value)

    db.commit()
    db.refresh(incident)

    return incident