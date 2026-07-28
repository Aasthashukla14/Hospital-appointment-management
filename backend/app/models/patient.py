"""
Patient model.
"""
import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class PatientStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Patient(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "patients"

    uhid: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[Gender] = mapped_column(SAEnum(Gender, name="gender_enum"), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    mobile_number: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    status: Mapped[PatientStatus] = mapped_column(
        SAEnum(PatientStatus, name="patient_status_enum"),
        nullable=False,
        default=PatientStatus.ACTIVE,
    )

    # Back-reference populated once Appointment model is added (Part 3).
    appointments: Mapped[list["Appointment"]] = relationship(  # noqa: F821
        "Appointment",
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Patient id={self.id} uhid={self.uhid} name={self.full_name}>"
