"""
Patient schemas.
"""
import re
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.patient import Gender, PatientStatus

MOBILE_REGEX = re.compile(r"^\+?[0-9]{10,15}$")


class PatientBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    gender: Gender
    date_of_birth: date
    mobile_number: str
    email: EmailStr | None = None

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        if not MOBILE_REGEX.match(v):
            raise ValueError("mobile_number must be 10-15 digits, optionally prefixed with '+'")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return v


class PatientCreateRequest(PatientBase):
    pass


class PatientUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    gender: Gender | None = None
    date_of_birth: date | None = None
    mobile_number: str | None = None
    email: EmailStr | None = None
    status: PatientStatus | None = None

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile(cls, v: str | None) -> str | None:
        if v is not None and not MOBILE_REGEX.match(v):
            raise ValueError("mobile_number must be 10-15 digits, optionally prefixed with '+'")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date | None) -> date | None:
        if v is not None and v > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return v


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    uhid: str
    first_name: str
    last_name: str
    full_name: str
    gender: Gender
    date_of_birth: date
    mobile_number: str
    email: EmailStr | None
    status: PatientStatus
    created_at: datetime
    updated_at: datetime


class PatientSearchParams(BaseModel):
    name: str | None = Field(default=None, description="Matches first or last name (partial)")
    uhid: str | None = None
    mobile_number: str | None = None
    status: PatientStatus | None = None
