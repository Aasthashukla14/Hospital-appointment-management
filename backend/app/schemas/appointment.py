"""
Appointment schemas.
"""
import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.config import settings
from app.models.appointment import AppointmentPriority, AppointmentStatus, AppointmentType


class AppointmentCreateRequest(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    department_id: uuid.UUID
    appointment_date: date
    appointment_time: time
    duration: int = Field(
        default_factory=lambda: settings.DEFAULT_APPOINTMENT_DURATION_MINUTES,
        ge=5,
        le=240,
        description="Duration in minutes (default configurable, 30 by default)",
    )
    appointment_type: AppointmentType = AppointmentType.OPD
    priority: AppointmentPriority = AppointmentPriority.NORMAL
    reason_for_visit: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=2000)
    parent_appointment_id: uuid.UUID | None = Field(
        default=None, description="Required when appointment_type is FOLLOW_UP"
    )

    @model_validator(mode="after")
    def validate_followup_reference(self) -> "AppointmentCreateRequest":
        if self.appointment_type == AppointmentType.FOLLOW_UP and not self.parent_appointment_id:
            raise ValueError("parent_appointment_id is required when appointment_type is FOLLOW_UP")
        if self.appointment_type != AppointmentType.FOLLOW_UP and self.parent_appointment_id:
            raise ValueError("parent_appointment_id may only be set for FOLLOW_UP appointments")
        return self


class AppointmentUpdateRequest(BaseModel):
    """
    General update endpoint — covers status transitions (confirm, check-in,
    start consultation, complete, no-show) and editable metadata.
    Date/time changes go through the dedicated reschedule endpoint.
    """

    status: AppointmentStatus | None = None
    appointment_type: AppointmentType | None = None
    priority: AppointmentPriority | None = None
    reason_for_visit: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=2000)


class AppointmentCancelRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class AppointmentRescheduleRequest(BaseModel):
    appointment_date: date
    appointment_time: time
    duration: int | None = Field(default=None, ge=5, le=240)
    reason: str = Field(min_length=1, max_length=500)


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    appointment_number: str
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    department_id: uuid.UUID
    appointment_date: date
    appointment_time: time
    duration: int
    appointment_type: AppointmentType
    priority: AppointmentPriority
    status: AppointmentStatus
    reason_for_visit: str | None
    notes: str | None
    parent_appointment_id: uuid.UUID | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AppointmentSearchParams(BaseModel):
    patient_id: uuid.UUID | None = None
    doctor_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    status: AppointmentStatus | None = None
    appointment_type: AppointmentType | None = None
    priority: AppointmentPriority | None = None
    date_from: date | None = None
    date_to: date | None = None
    uhid: str | None = Field(default=None, description="Search by patient UHID")

    @model_validator(mode="after")
    def validate_date_range(self) -> "AppointmentSearchParams":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from cannot be after date_to")
        return self
