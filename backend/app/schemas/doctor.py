"""
Doctor schemas.
"""
import re
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.doctor import DoctorStatus

MOBILE_REGEX = re.compile(r"^\+?[0-9]{10,15}$")


class DoctorBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    department_id: uuid.UUID
    specialization: str = Field(min_length=1, max_length=150)
    mobile_number: str
    email: EmailStr
    consultation_fee: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        if not MOBILE_REGEX.match(v):
            raise ValueError("mobile_number must be 10-15 digits, optionally prefixed with '+'")
        return v


class DoctorCreateRequest(DoctorBase):
    pass


class DoctorUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    department_id: uuid.UUID | None = None
    specialization: str | None = Field(default=None, min_length=1, max_length=150)
    mobile_number: str | None = None
    email: EmailStr | None = None
    consultation_fee: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    status: DoctorStatus | None = None

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: str | None) -> str | None:
        if v is not None and not MOBILE_REGEX.match(v):
            raise ValueError("mobile_number must be 10-15 digits, optionally prefixed with '+'")
        return v


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: str
    full_name: str
    department_id: uuid.UUID
    specialization: str
    mobile_number: str
    email: EmailStr
    consultation_fee: Decimal
    status: DoctorStatus
    created_at: datetime
    updated_at: datetime


class DoctorSearchParams(BaseModel):
    name: str | None = None
    department_id: uuid.UUID | None = None
    specialization: str | None = None
    status: DoctorStatus | None = None
