"""
Department schemas.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.department import DepartmentStatus


class DepartmentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)


class DepartmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    status: DepartmentStatus | None = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    status: DepartmentStatus
    created_at: datetime
    updated_at: datetime


class DepartmentSearchParams(BaseModel):
    name: str | None = None
    status: DepartmentStatus | None = None
