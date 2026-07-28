"""
Department model.
"""
import enum

from sqlalchemy import Enum as SAEnum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class DepartmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Department(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DepartmentStatus] = mapped_column(
        SAEnum(DepartmentStatus, name="department_status_enum"),
        nullable=False,
        default=DepartmentStatus.ACTIVE,
    )

    doctors: Mapped[list["Doctor"]] = relationship(
        "Doctor",
        back_populates="department",
        passive_deletes=True,
    )

    # Populated once Appointment model is added (Part 3).
    appointments: Mapped[list["Appointment"]] = relationship(  # noqa: F821
        "Appointment",
        back_populates="department",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Department id={self.id} name={self.name}>"
