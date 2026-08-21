from contextlib import asynccontextmanager
from uuid import UUID
from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import ChangeEvent, Incident
from app.schemas import (
    ChangeEventCreate,
    ChangeEventResponse,
    IncidentClassificationRequest,
    IncidentClassificationResponse,
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
    IncidentRoutingResponse,
)
from app.services import find_related_change_events
from app.ml_classifier import (
    get_model_metadata,
    predict_incident,
)
from app.escalation_router import route_incident
from app.triage_service import triage_incident

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
    try:
        triage = triage_incident(
            title=incident_data.title,
            description=incident_data.description,
            service_name=incident_data.service_name,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    incident = Incident(
        **incident_data.model_dump(),
        predicted_category=str(triage["predicted_category"]),
        predicted_severity=str(triage["predicted_severity"]),
        category_confidence=float(triage["category_confidence"]),
        severity_confidence=float(triage["severity_confidence"]),
        triage_route=str(triage["route"]),
        model_tier=str(triage["model_tier"]),
        human_review_required=bool(
            triage["human_review_required"],
        ),
        triage_reason=str(triage["reason"]),
        triaged_at=triage["triaged_at"],
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident

@app.get(
    "/incidents",
    response_model=list[IncidentResponse],
)
def list_incidents(
    severity: str | None = None,
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
    service_name: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[Incident]:
    statement = select(Incident)

    if severity:
        statement = statement.where(Incident.severity == severity)

    if status_filter:
        statement = statement.where(Incident.status == status_filter)

    if service_name:
        statement = statement.where(
            Incident.service_name == service_name,
        )

    statement = statement.order_by(
        Incident.created_at.desc(),
    ).limit(limit)

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

@app.post(
    "/change-events",
    response_model=ChangeEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_change_event(
    event_data: ChangeEventCreate,
    db: Session = Depends(get_db),
) -> ChangeEvent:
    event = ChangeEvent(**event_data.model_dump(exclude_none=True))

    db.add(event)
    db.commit()
    db.refresh(event)

    return event

@app.get(
    "/change-events",
    response_model=list[ChangeEventResponse],
)
def list_change_events(
    service_name: str | None = None,
    event_type: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ChangeEvent]:
    statement = select(ChangeEvent)

    if service_name:
        statement = statement.where(
            ChangeEvent.service_name == service_name,
        )

    if event_type:
        statement = statement.where(
            ChangeEvent.event_type == event_type,
        )

    statement = statement.order_by(
        ChangeEvent.occurred_at.desc(),
    ).limit(limit)

    return list(db.scalars(statement).all())

@app.get(
    "/incidents/{incident_id}/related-change-events",
    response_model=list[ChangeEventResponse],
)
def get_related_change_events(
    incident_id: UUID,
    window_minutes: int = Query(default=30, ge=1, le=240),
    db: Session = Depends(get_db),
) -> list[ChangeEvent]:
    incident, events = find_related_change_events(
        db=db,
        incident_id=incident_id,
        window_minutes=window_minutes,
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    return events

@app.post(
    "/ml/classify-incident",
    response_model=IncidentClassificationResponse,
)
def classify_incident(
    incident_data: IncidentClassificationRequest,
) -> dict[str, object]:
    return predict_incident(
        title=incident_data.title,
        description=incident_data.description,
        service_name=incident_data.service_name,
    )

@app.get("/ml/model-metadata")
def get_incident_classifier_metadata() -> dict:
    try:
        return get_model_metadata()
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

@app.post(
    "/ml/route-incident",
    response_model=IncidentRoutingResponse,
)
def route_new_incident(
    incident_data: IncidentClassificationRequest,
) -> dict[str, object]:
    prediction = predict_incident(
        title=incident_data.title,
        description=incident_data.description,
        service_name=incident_data.service_name,
    )

    routing = route_incident(
        predicted_severity=str(
            prediction["predicted_severity"],
        ),
        category_confidence=float(
            prediction["category_confidence"],
        ),
        severity_confidence=float(
            prediction["severity_confidence"],
        ),
    )

    return {
        **prediction,
        **routing,
    }

@app.post(
    "/incidents/{incident_id}/triage",
    response_model=IncidentResponse,
)
def retriage_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
) -> Incident:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    try:
        triage = triage_incident(
            title=incident.title,
            description=incident.description,
            service_name=incident.service_name,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    incident.predicted_category = str(
        triage["predicted_category"],
    )
    incident.predicted_severity = str(
        triage["predicted_severity"],
    )
    incident.category_confidence = float(
        triage["category_confidence"],
    )
    incident.severity_confidence = float(
        triage["severity_confidence"],
    )
    incident.triage_route = str(triage["route"])
    incident.model_tier = str(triage["model_tier"])
    incident.human_review_required = bool(
        triage["human_review_required"],
    )
    incident.triage_reason = str(triage["reason"])
    incident.triaged_at = triage["triaged_at"]

    db.commit()
    db.refresh(incident)

    return incident