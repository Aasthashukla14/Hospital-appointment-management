"""
Audit log endpoints.

RBAC summary:
    - Read/search: SUPER_ADMIN only. Audit trails are sensitive; even
      HOSPITAL_ADMIN does not get blanket read access by default.
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, Pagination, RoleChecker
from app.models.user import UserRole
from app.schemas.audit import AuditLogResponse
from app.schemas.common import PaginatedResponse
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

can_view_audit_logs = RoleChecker([UserRole.SUPER_ADMIN])


@router.get(
    "/",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="Search the audit trail (SUPER_ADMIN only)",
    dependencies=[Depends(can_view_audit_logs)],
)
def search_audit_logs(
    db: DbSession,
    pagination: Pagination,
    actor_user_id: uuid.UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    success: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    return AuditLogService(db).search(
        pagination,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        success=success,
        date_from=date_from,
        date_to=date_to,
    )
