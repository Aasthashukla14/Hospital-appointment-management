"""
User model — backs authentication and RBAC.

Roles:
    SUPER_ADMIN   - full system access
    HOSPITAL_ADMIN- manage departments/doctors/patients, view everything
    RECEPTIONIST  - book/manage appointments, manage patients
    DOCTOR        - view own appointments, update consultation status
"""
import enum
import uuid

from sqlalchemy import Boolean, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    HOSPITAL_ADMIN = "HOSPITAL_ADMIN"
    RECEPTIONIST = "RECEPTIONIST"
    DOCTOR = "DOCTOR"


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.RECEPTIONIST
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Nullable link to a Doctor record when role == DOCTOR.
    # Doctor model is introduced in Part 2; the FK column is added there
    # via alembic migration and mapped back with a relationship at that point.
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} username={self.username} role={self.role}>"
