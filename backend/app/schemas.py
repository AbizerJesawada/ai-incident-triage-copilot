from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


Severity = Literal[
    "unknown",
    "low",
    "medium",
    "high",
    "critical",
]

IncidentStatus = Literal[
    "open",
    "investigating",
    "resolved",
]

ChangeEventType = Literal[
    "deployment",
    "configuration_change",
    "feature_flag",
]


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3)
    service_name: str = Field(min_length=2, max_length=100)
    severity: Severity = "unknown"
    source: str = Field(default="manual", max_length=50)


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    service_name: str
    severity: Severity
    status: IncidentStatus
    source: str
    created_at: datetime
    updated_at: datetime


class IncidentUpdate(BaseModel):
    severity: Severity | None = None
    status: IncidentStatus | None = None


class ChangeEventCreate(BaseModel):
    service_name: str = Field(min_length=2, max_length=100)
    event_type: ChangeEventType
    description: str = Field(min_length=3)
    reference_id: str | None = Field(
        default=None,
        max_length=100,
    )
    occurred_at: datetime | None = None


class ChangeEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    service_name: str
    event_type: ChangeEventType
    description: str
    reference_id: str | None
    occurred_at: datetime

class IncidentClassificationRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3)
    service_name: str = Field(min_length=2, max_length=100)


class IncidentClassificationResponse(BaseModel):
    predicted_category: str
    predicted_severity: Severity
    category_confidence: float
    severity_confidence: float