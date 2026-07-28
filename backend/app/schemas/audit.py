"""
Audit log schemas.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    actor_username: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    success: bool
    ip_address: str | None
    details: dict | None
    message: str | None
    created_at: datetime
