"""
AuditLog repository.
"""
import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session):
        super().__init__(AuditLog, db)

    def search(
        self,
        *,
        actor_user_id: uuid.UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        success: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[AuditLog], int]:
        base_stmt = select(AuditLog)
        count_stmt = select(func.count()).select_from(AuditLog)

        conditions = []
        if actor_user_id:
            conditions.append(AuditLog.actor_user_id == actor_user_id)
        if action:
            conditions.append(AuditLog.action == action)
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLog.resource_id == resource_id)
        if success is not None:
            conditions.append(AuditLog.success == success)
        if date_from:
            conditions.append(func.date(AuditLog.created_at) >= date_from)
        if date_to:
            conditions.append(func.date(AuditLog.created_at) <= date_to)

        for cond in conditions:
            base_stmt = base_stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        base_stmt = base_stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

        items = list(self.db.scalars(base_stmt).all())
        total = self.db.scalar(count_stmt) or 0
        return items, total
