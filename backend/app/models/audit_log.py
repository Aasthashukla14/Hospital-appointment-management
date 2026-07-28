"""
AuditLog model.

Records sensitive actions (authentication events, appointment cancellations,
status changes, etc.) for compliance and traceability. Deliberately kept as
plain, denormalized columns rather than an enum-backed `action` column:
audit event types tend to grow over the life of a system, and adding a new
kind of event should never require an Alembic migration to widen a DB enum.

NOTE: This model is included in Part 4 so the application layer (services,
repositories, router) is complete and runnable. The actual Alembic migration
that creates the `audit_logs` table is generated in Part 5 alongside the
rest of the schema, per the agreed part breakdown.
"""
import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class AuditAction:
    """String constants for the `action` column. Not a DB enum — see module
    docstring for why. Treat this as the single source of truth for valid
    action names used across the codebase."""

    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    USER_REGISTERED = "USER_REGISTERED"
    APPOINTMENT_BOOKED = "APPOINTMENT_BOOKED"
    APPOINTMENT_STATUS_CHANGED = "APPOINTMENT_STATUS_CHANGED"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"
    APPOINTMENT_RESCHEDULED = "APPOINTMENT_RESCHEDULED"


class AuditLog(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    # Nullable + ondelete SET NULL: a user being deleted (or the actor being
    # unauthenticated, e.g. a failed login) must never block or cascade-wipe
    # the audit trail. `actor_username` is also captured redundantly as a
    # denormalized string so the log entry stays human-readable even after
    # the user record is gone.
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_username: Mapped[str | None] = mapped_column(String(64), nullable=True)

    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6-safe length
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog id={self.id} action={self.action} actor={self.actor_username}>"
