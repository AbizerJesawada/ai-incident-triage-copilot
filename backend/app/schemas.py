from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3)
    service_name: str = Field(min_length=2, max_length=100)
    severity: str = Field(default="unknown", max_length=20)
    source: str = Field(default="manual", max_length=50)


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    service_name: str
    severity: str
    status: str
    source: str
    created_at: datetime
    updated_at: datetime
class IncidentUpdate(BaseModel):
    severity: str | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None, max_length=20)