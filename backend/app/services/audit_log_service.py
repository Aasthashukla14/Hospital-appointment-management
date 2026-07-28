"""
Audit logging service.

Other services call `AuditLogService.record(...)` to append an audit trail
entry for a sensitive action (authentication events, appointment
cancellations, status changes, etc.).

Transaction behavior: `record()` adds and flushes the AuditLog row on the
*same* SQLAlchemy session as the action being audited, but does NOT commit.
This means the audit entry is committed atomically together with the
business change it describes (e.g. an appointment cancellation and its
audit row either both persist or both roll back) whenever the caller's own
`repo.commit()` runs afterwards. For events with no other DB write in the
same request (e.g. a failed login), the caller must commit explicitly —
`record_and_commit()` is provided for that case.
"""
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit import AuditLogResponse
from app.schemas.common import PaginatedResponse, PaginationParams

logger = get_logger(__name__)


class AuditLogService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditLogRepository(db)

    def record(
        self,
        *,
        action: str,
        actor_user_id: uuid.UUID | None = None,
        actor_username: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        success: bool = True,
        ip_address: str | None = None,
        details: dict | None = None,
        message: str | None = None,
    ) -> AuditLog:
        entry = self.repo.create(
            {
                "action": action,
                "actor_user_id": actor_user_id,
                "actor_username": actor_username,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id is not None else None,
                "success": success,
                "ip_address": ip_address,
                "details": details or {},
                "message": message,
            }
        )
        logger.info(
            "AUDIT action=%s actor=%s resource=%s/%s success=%s",
            action,
            actor_username,
            resource_type,
            resource_id,
            success,
        )
        return entry

    def record_and_commit(self, **kwargs) -> AuditLog:
        entry = self.record(**kwargs)
        self.repo.commit()
        return entry

    def search(
        self,
        pagination: PaginationParams,
        *,
        actor_user_id: uuid.UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        success: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> PaginatedResponse[AuditLogResponse]:
        items, total = self.repo.search(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            date_from=date_from,
            date_to=date_to,
            skip=pagination.offset,
            limit=pagination.page_size,
        )
        response_items = [AuditLogResponse.model_validate(item) for item in items]
        return PaginatedResponse.create(response_items, total, pagination.page, pagination.page_size)
