from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.escalation_router import route_incident
from app.ml_classifier import get_model_metadata, predict_incident
from app.models import (ChangeEvent, Incident, IncidentReview, IncidentChangeCorrelation,)
from app.schemas import (
    ChangeEventCreate,
    ChangeEventResponse,
    IncidentClassificationRequest,
    IncidentClassificationResponse,
    IncidentCreate,
    IncidentResponse,
    IncidentReviewCreate,
    IncidentReviewResponse,
    IncidentRoutingResponse,
    IncidentUpdate,
    FeedbackTrainingExample,
    IncidentChangeCorrelationResponse,
    IncidentCorrelationTimelineItem,
    RootCauseHypothesisResponse,
)
from app.correlation_service import (
    refresh_incident_change_correlations,
    build_root_cause_hypothesis,
)
from app.services import find_related_change_events
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

    refresh_incident_change_correlations(
        db=db,
        incident=incident,
    )

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
    event = ChangeEvent(
        **event_data.model_dump(exclude_none=True),
    )

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

    incident.triaged_at = triage["triaged_at"]

    db.commit()
    db.refresh(incident)

    refresh_incident_change_correlations(
        db=db,
        incident=incident,
    )

    db.commit()
    db.refresh(incident)

    return incident


@app.post(
    "/incidents/{incident_id}/reviews",
    response_model=IncidentReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_incident_review(
    incident_id: UUID,
    review_data: IncidentReviewCreate,
    db: Session = Depends(get_db),
) -> IncidentReview:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    review = IncidentReview(
        incident_id=incident_id,
        **review_data.model_dump(),
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review


@app.get(
    "/incidents/{incident_id}/reviews",
    response_model=list[IncidentReviewResponse],
)
def list_incident_reviews(
    incident_id: UUID,
    db: Session = Depends(get_db),
) -> list[IncidentReview]:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    statement = (
        select(IncidentReview)
        .where(IncidentReview.incident_id == incident_id)
        .order_by(IncidentReview.created_at.desc())
    )

    return list(db.scalars(statement).all())


@app.get(
    "/review-queue",
    response_model=list[IncidentResponse],
)
def list_review_queue(
    db: Session = Depends(get_db),
) -> list[Incident]:
    statement = (
        select(Incident)
        .where(Incident.human_review_required.is_(True))
        .where(Incident.status != "resolved")
        .order_by(Incident.created_at.desc())
    )

    return list(db.scalars(statement).all())

@app.get(
    "/ml/feedback-training-examples",
    response_model=list[FeedbackTrainingExample],
)
def list_feedback_training_examples(
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
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

    rows = db.execute(statement).all()

    return [
        {
            "incident_id": incident.id,
            "review_id": review.id,
            "title": incident.title,
            "description": incident.description,
            "service_name": incident.service_name,
            "category": review.actual_category,
            "severity": review.actual_severity,
            "reviewer_name": review.reviewer_name,
            "reviewed_at": review.created_at,
        }
        for review, incident in rows
    ]

@app.post(
    "/incidents/{incident_id}/correlations/refresh",
    response_model=list[IncidentChangeCorrelationResponse],
)
def refresh_incident_correlations(
    incident_id: UUID,
    window_minutes: int = Query(default=30, ge=1, le=240),
    db: Session = Depends(get_db),
) -> list[IncidentChangeCorrelation]:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    correlations = refresh_incident_change_correlations(
        db=db,
        incident=incident,
        window_minutes=window_minutes,
    )

    db.commit()

    return correlations

@app.get(
    "/incidents/{incident_id}/correlations",
    response_model=list[IncidentChangeCorrelationResponse],
)
def list_incident_correlations(
    incident_id: UUID,
    db: Session = Depends(get_db),
) -> list[IncidentChangeCorrelation]:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    statement = (
        select(IncidentChangeCorrelation)
        .where(
            IncidentChangeCorrelation.incident_id == incident_id
        )
        .order_by(
            IncidentChangeCorrelation.correlation_score.desc()
        )
    )

    return list(db.scalars(statement).all())

@app.get(
    "/incidents/{incident_id}/correlation-timeline",
    response_model=list[IncidentCorrelationTimelineItem],
)
def get_incident_correlation_timeline(
    incident_id: UUID,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    statement = (
        select(IncidentChangeCorrelation, ChangeEvent)
        .join(
            ChangeEvent,
            IncidentChangeCorrelation.change_event_id
            == ChangeEvent.id,
        )
        .where(
            IncidentChangeCorrelation.incident_id == incident_id
        )
        .order_by(
            IncidentChangeCorrelation.correlation_score.desc(),
            ChangeEvent.occurred_at.desc(),
        )
    )

    rows = db.execute(statement).all()

    return [
        {
            "correlation_id": correlation.id,
            "change_event_id": change_event.id,
            "event_type": change_event.event_type,
            "reference_id": change_event.reference_id,
            "description": change_event.description,
            "occurred_at": change_event.occurred_at,
            "time_difference_minutes": (
                correlation.time_difference_minutes
            ),
            "correlation_score": correlation.correlation_score,
            "correlation_reason": correlation.correlation_reason,
        }
        for correlation, change_event in rows
    ]

@app.get(
    "/incidents/{incident_id}/root-cause-hypothesis",
    response_model=RootCauseHypothesisResponse,
)
def get_root_cause_hypothesis(
    incident_id: UUID,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    statement = (
        select(IncidentChangeCorrelation)
        .where(
            IncidentChangeCorrelation.incident_id == incident_id
        )
        .order_by(
            IncidentChangeCorrelation.correlation_score.desc()
        )
    )

    correlations = list(db.scalars(statement).all())

    change_event_ids = [
        correlation.change_event_id
        for correlation in correlations
    ]

    change_events_by_id = {}

    if change_event_ids:
        change_events = db.scalars(
            select(ChangeEvent).where(
                ChangeEvent.id.in_(change_event_ids)
            )
        ).all()

        change_events_by_id = {
            change_event.id: change_event
            for change_event in change_events
        }

    root_cause_correlations = [
        correlation
        for correlation in correlations
        if change_events_by_id[
            correlation.change_event_id
        ].occurred_at <= incident.created_at
    ]

    hypothesis = build_root_cause_hypothesis(
        incident=incident,
        correlations=root_cause_correlations,
        change_events_by_id=change_events_by_id,
    )

    strongest_score = (
        max(
            root_cause_correlations,
            key=lambda correlation: correlation.correlation_score,
        ).correlation_score
        if root_cause_correlations
        else None
    )

    return {
        "incident_id": incident.id,
        "hypothesis": hypothesis,
        "strongest_correlation_score": strongest_score,
    }