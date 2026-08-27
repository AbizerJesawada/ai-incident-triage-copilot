from contextlib import asynccontextmanager
from uuid import UUID
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from time import perf_counter
from app.database import Base, engine, get_db
from app.escalation_router import route_incident
from app.ml_classifier import get_model_metadata, predict_incident
from app.models import (ChangeEvent, EngineerNotification, Incident, IncidentReview, IncidentChangeCorrelation,RemediationRecommendation,LLMGenerationLog,)
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
    RemediationRecommendationResponse,
    RemediationRecommendationReview,
    IncidentBriefingResponse,
    LLMGenerationLogResponse,
    LLMGenerationSummaryResponse,
    EngineerNotificationResponse,
)
from app.correlation_service import (
    refresh_incident_change_correlations,
    build_root_cause_hypothesis,
)
from app.services import find_related_change_events
from app.triage_service import triage_incident
from app.remediation_service import (
    generate_remediation_recommendations,
)
from app.llm_service import (
    generate_incident_briefing,
    validate_briefing_evidence,
)
from app.notification_service import (
    create_review_notification_if_needed,
)

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

    create_review_notification_if_needed(
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

    db.add(incident)
    db.flush()

    create_review_notification_if_needed(
        db=db,
        incident=incident,
    )

    db.commit()
    db.refresh(incident)

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

@app.post(
    "/incidents/{incident_id}/recommendations/generate",
    response_model=list[RemediationRecommendationResponse],
)
def generate_incident_recommendations(
    incident_id: UUID,
    db: Session = Depends(get_db),
) -> list[RemediationRecommendation]:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    correlations = list(
        db.scalars(
            select(IncidentChangeCorrelation).where(
                IncidentChangeCorrelation.incident_id
                == incident_id
            )
        ).all()
    )

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

    recommendation_data = (
        generate_remediation_recommendations(
            incident=incident,
            correlations=correlations,
            change_events_by_id=change_events_by_id,
        )
    )

    source_ids = [
        item["source_id"]
        for item in recommendation_data
        if item["source_id"] is not None
    ]

    existing_source_ids = set()

    if source_ids:
        existing_source_ids = set(
            db.scalars(
                select(RemediationRecommendation.source_id).where(
                    RemediationRecommendation.incident_id
                    == incident_id,
                    RemediationRecommendation.source_id.in_(
                        source_ids
                    ),
                )
            ).all()
        )

    new_recommendations = []

    for item in recommendation_data:
        if item["source_id"] in existing_source_ids:
            continue

        recommendation = RemediationRecommendation(
            incident_id=incident_id,
            recommendation=str(item["recommendation"]),
            evidence=str(item["evidence"]),
            source_type=str(item["source_type"]),
            source_id=item["source_id"],
        )

        db.add(recommendation)
        new_recommendations.append(recommendation)

    db.commit()

    for recommendation in new_recommendations:
        db.refresh(recommendation)

    return new_recommendations

@app.get(
    "/incidents/{incident_id}/recommendations",
    response_model=list[RemediationRecommendationResponse],
)
def list_incident_recommendations(
    incident_id: UUID,
    db: Session = Depends(get_db),
) -> list[RemediationRecommendation]:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    statement = (
        select(RemediationRecommendation)
        .where(
            RemediationRecommendation.incident_id == incident_id
        )
        .order_by(RemediationRecommendation.created_at.desc())
    )

    return list(db.scalars(statement).all())

@app.patch(
    "/recommendations/{recommendation_id}/review",
    response_model=RemediationRecommendationResponse,
)
def review_remediation_recommendation(
    recommendation_id: UUID,
    review_data: RemediationRecommendationReview,
    db: Session = Depends(get_db),
) -> RemediationRecommendation:
    recommendation = db.get(
        RemediationRecommendation,
        recommendation_id,
    )

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found.",
        )

    if recommendation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending recommendations can be reviewed.",
        )

    recommendation.status = review_data.status
    recommendation.reviewer_name = review_data.reviewer_name
    recommendation.review_note = review_data.review_note
    recommendation.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(recommendation)

    return recommendation

@app.get(
    "/incidents/{incident_id}/briefing",
    response_model=IncidentBriefingResponse,
)
def get_incident_briefing(
    incident_id: UUID,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    correlation_rows = db.execute(
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
            IncidentChangeCorrelation.correlation_score.desc()
        )
    ).all()

    recommendations = list(
        db.scalars(
            select(RemediationRecommendation)
            .where(
                RemediationRecommendation.incident_id
                == incident_id
            )
            .order_by(
                RemediationRecommendation.created_at.desc()
            )
        ).all()
    )

    evidence_sources = []
    correlation_context = []

    for correlation, change_event in correlation_rows:
        reference = change_event.reference_id or str(
            change_event.id
        )
        timing = (
            "before"
            if change_event.occurred_at <= incident.created_at
            else "after"
        )

        evidence_sources.append(
            {
                "source_type": "change_event",
                "source_id": change_event.id,
                "reference_id": change_event.reference_id,
                "description": (
                    f"{change_event.event_type.replace('_', ' ')} "
                    f"{reference} occurred "
                    f"{correlation.time_difference_minutes} minutes "
                    f"{timing} the incident. "
                    f"Correlation score: "
                    f"{correlation.correlation_score}."
                ),
            }
        )

        correlation_context.append(
            f"- {change_event.event_type}: {reference}; "
            f"{correlation.time_difference_minutes} minutes "
            f"{timing}; score {correlation.correlation_score}; "
            f"{correlation.correlation_reason}"
        )

    recommendation_context = [
        (
            f"- Status: {recommendation.status}; "
            f"Recommendation: {recommendation.recommendation}; "
            f"Evidence: {recommendation.evidence}"
        )
        for recommendation in recommendations
    ]

    incident_context = "\n".join(
        [
            "Incident:",
            f"- ID: {incident.id}",
            f"- Title: {incident.title}",
            f"- Description: {incident.description}",
            f"- Service: {incident.service_name}",
            f"- Predicted category: "
            f"{incident.predicted_category or 'not available'}",
            f"- Predicted severity: "
            f"{incident.predicted_severity or 'not available'}",
            f"- Triage reason: "
            f"{incident.triage_reason or 'not available'}",
            "",
            "Correlation evidence:",
            *(
                correlation_context
                or ["- No saved correlation evidence."]
            ),
            "",
            "Saved recommendations:",
            *(
                recommendation_context
                or ["- No saved recommendations."]
            ),
        ]
    )

    started_at = perf_counter()

    try:
        llm_result = generate_incident_briefing(
            incident_context=incident_context,
        )
    except Exception as error:
        latency_ms = round(
            (perf_counter() - started_at) * 1000,
            2,
        )

        failed_log = LLMGenerationLog(
            incident_id=incident.id,
            model_name="unknown",
            status="error",
            latency_ms=latency_ms,
            error_message=str(error),
        )

        db.add(failed_log)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not generate incident briefing: {error}",
        ) from error

    latency_ms = round(
        (perf_counter() - started_at) * 1000,
        2,
    )

    briefing = str(llm_result["briefing"])

    allowed_reference_ids = [
        str(source["reference_id"])
        for source in evidence_sources
        if source["reference_id"] is not None
    ]

    evidence_validation = validate_briefing_evidence(
        briefing=briefing,
        allowed_reference_ids=allowed_reference_ids,
    )

    grounding_status = (
        "verified"
        if not evidence_validation["unsupported_reference_ids"]
        else "unverified"
    )

    success_log = LLMGenerationLog(
        incident_id=incident.id,
        model_name=str(llm_result["model_name"]),
        grounding_status=grounding_status,
        status="success",
        latency_ms=latency_ms,
        prompt_token_count=llm_result["prompt_token_count"],
        response_token_count=llm_result["response_token_count"],
    )

    db.add(success_log)
    db.commit()

    return {
        "incident_id": incident.id,
        "briefing": briefing,
        "evidence_sources": evidence_sources,
        "evidence_validation": evidence_validation,
        "grounding_status": grounding_status,
    }

@app.get(
    "/incidents/{incident_id}/llm-generation-logs",
    response_model=list[LLMGenerationLogResponse],
)
def list_incident_llm_generation_logs(
    incident_id: UUID,
    db: Session = Depends(get_db),
) -> list[LLMGenerationLog]:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    statement = (
        select(LLMGenerationLog)
        .where(LLMGenerationLog.incident_id == incident_id)
        .order_by(LLMGenerationLog.created_at.desc())
    )

    return list(db.scalars(statement).all())

@app.get(
    "/llm-generation-summary",
    response_model=LLMGenerationSummaryResponse,
)
def get_llm_generation_summary(
    db: Session = Depends(get_db),
) -> dict[str, object]:
    total_calls = db.scalar(
        select(func.count()).select_from(LLMGenerationLog)
    ) or 0

    successful_calls = db.scalar(
        select(func.count())
        .select_from(LLMGenerationLog)
        .where(LLMGenerationLog.status == "success")
    ) or 0

    failed_calls = db.scalar(
        select(func.count())
        .select_from(LLMGenerationLog)
        .where(LLMGenerationLog.status == "error")
    ) or 0

    verified_briefings = db.scalar(
        select(func.count())
        .select_from(LLMGenerationLog)
        .where(LLMGenerationLog.grounding_status == "verified")
    ) or 0

    average_latency_ms = db.scalar(
        select(func.avg(LLMGenerationLog.latency_ms))
    )

    total_prompt_tokens = db.scalar(
        select(
            func.coalesce(
                func.sum(LLMGenerationLog.prompt_token_count),
                0,
            )
        )
    ) or 0

    total_response_tokens = db.scalar(
        select(
            func.coalesce(
                func.sum(LLMGenerationLog.response_token_count),
                0,
            )
        )
    ) or 0

    return {
        "total_calls": total_calls,
        "successful_calls": successful_calls,
        "failed_calls": failed_calls,
        "verified_briefings": verified_briefings,
        "average_latency_ms": (
            round(float(average_latency_ms), 2)
            if average_latency_ms is not None
            else None
        ),
        "total_prompt_tokens": int(total_prompt_tokens),
        "total_response_tokens": int(total_response_tokens),
    }

@app.get(
    "/engineer-notifications",
    response_model=list[EngineerNotificationResponse],
)
def list_engineer_notifications(
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
    db: Session = Depends(get_db),
) -> list[EngineerNotification]:
    statement = select(EngineerNotification)

    if status_filter:
        statement = statement.where(
            EngineerNotification.status == status_filter
        )

    statement = statement.order_by(
        EngineerNotification.created_at.desc()
    )

    return list(db.scalars(statement).all())

@app.patch(
    "/engineer-notifications/{notification_id}/read",
    response_model=EngineerNotificationResponse,
)
def mark_engineer_notification_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
) -> EngineerNotification:
    notification = db.get(
        EngineerNotification,
        notification_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    notification.status = "read"
    notification.read_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(notification)

    return notification