"""
Appointment model — the core entity of the HIMS Appointment Management Module.
"""
import enum
import uuid
from datetime import date, time

from sqlalchemy import Date, ForeignKey, Integer, String, Text, Time
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class AppointmentType(str, enum.Enum):
    OPD = "OPD"
    FOLLOW_UP = "FOLLOW_UP"
    VIDEO_CONSULTATION = "VIDEO_CONSULTATION"


class AppointmentPriority(str, enum.Enum):
    NORMAL = "NORMAL"
    EMERGENCY = "EMERGENCY"


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


# Statuses that no longer occupy a doctor's / patient's calendar slot.
RELEASED_STATUSES = (AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW)

# Legal forward transitions for the appointment workflow.
ALLOWED_STATUS_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.SCHEDULED: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CHECKED_IN,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.CONFIRMED: {
        AppointmentStatus.CHECKED_IN,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.CHECKED_IN: {
        AppointmentStatus.IN_CONSULTATION,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.IN_CONSULTATION: {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED},
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.NO_SHOW: set(),
}


class Appointment(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "appointments"

    appointment_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    appointment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    appointment_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    appointment_type: Mapped[AppointmentType] = mapped_column(
        SAEnum(AppointmentType, name="appointment_type_enum"), nullable=False, default=AppointmentType.OPD
    )
    priority: Mapped[AppointmentPriority] = mapped_column(
        SAEnum(AppointmentPriority, name="appointment_priority_enum"),
        nullable=False,
        default=AppointmentPriority.NORMAL,
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        SAEnum(AppointmentStatus, name="appointment_status_enum"),
        nullable=False,
        default=AppointmentStatus.SCHEDULED,
        index=True,
    )

    reason_for_visit: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Self-referential link for follow-up appointments.
    parent_appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    # ---- Relationships ----
    patient: Mapped["Patient"] = relationship("Patient", back_populates="appointments")  # noqa: F821
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="appointments")  # noqa: F821
    department: Mapped["Department"] = relationship("Department", back_populates="appointments")  # noqa: F821
    parent_appointment: Mapped["Appointment | None"] = relationship(
        "Appointment", remote_side="Appointment.id", back_populates="follow_ups"
    )
    follow_ups: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="parent_appointment"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Appointment id={self.id} number={self.appointment_number} "
            f"date={self.appointment_date} time={self.appointment_time} status={self.status}>"
        )
