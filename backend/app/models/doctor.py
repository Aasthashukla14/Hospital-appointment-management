"""
Doctor model.
"""
import enum
import uuid

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class DoctorStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Doctor(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "doctors"

    employee_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    specialization: Mapped[str] = mapped_column(String(150), nullable=False)
    mobile_number: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    consultation_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    status: Mapped[DoctorStatus] = mapped_column(
        SAEnum(DoctorStatus, name="doctor_status_enum"),
        nullable=False,
        default=DoctorStatus.ACTIVE,
    )

    department: Mapped["Department"] = relationship("Department", back_populates="doctors")

    # Populated once Appointment model is added (Part 3).
    appointments: Mapped[list["Appointment"]] = relationship(  # noqa: F821
        "Appointment",
        back_populates="doctor",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Doctor id={self.id} employee_id={self.employee_id} name={self.full_name}>"
