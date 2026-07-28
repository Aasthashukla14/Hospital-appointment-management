"""
Shared FastAPI dependencies: DB session re-export, current-user resolution,
and role-based access control (RBAC) guards.
"""
import uuid
from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, TokenRevokedException, UnauthorizedException
from app.core.security import TokenType, decode_token
from app.core.token_blacklist import is_token_revoked
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginationParams

bearer_scheme = HTTPBearer(auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


def get_current_access_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict:

    token = credentials.credentials if credentials else None
    if not token:
        raise UnauthorizedException("Not authenticated. Provide a bearer token.")

    try:
        payload = decode_token(token)
    except JWTError:
        raise UnauthorizedException("Invalid or expired access token")

    if payload.get("type") != TokenType.ACCESS.value:
        raise UnauthorizedException("Token provided is not an access token")

    if is_token_revoked(payload.get("jti")):
        raise TokenRevokedException()

    return payload


CurrentAccessTokenPayload = Annotated[dict, Depends(get_current_access_token_payload)]


def get_current_user(
    db: DbSession,
    payload: CurrentAccessTokenPayload,
) -> User:
    username = payload.get("sub")
    if not username:
        raise UnauthorizedException("Malformed token payload")

    user = UserRepository(db).get_by_username(username)
    if not user:
        raise UnauthorizedException("User no longer exists")
    if not user.is_active:
        raise UnauthorizedException("This account has been deactivated")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


class RoleChecker:
    """
    Dependency factory for RBAC. Usage:

        @router.post("/", dependencies=[Depends(RoleChecker([UserRole.SUPER_ADMIN]))])
    or
        current_user: CurrentUser = Depends(RoleChecker([UserRole.SUPER_ADMIN]))
    """

    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: CurrentUser) -> User:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenException(
                f"Role '{current_user.role.value}' is not permitted to perform this action. "
                f"Allowed roles: {[r.value for r in self.allowed_roles]}"
            )
        return current_user


def require_own_doctor_profile(current_user: CurrentUser) -> uuid.UUID | None:
    """
    Resolves the caller's own doctor scope for the appointment module.

    Returns:
        - None if the caller is not a DOCTOR (no scoping should be applied —
          RECEPTIONIST/HOSPITAL_ADMIN/SUPER_ADMIN can see/manage all
          appointments).
        - The caller's own `doctor_id` if the caller IS a DOCTOR and their
          user account is correctly linked to a doctor profile.

    Raises:
        ForbiddenException if the caller's role is DOCTOR but their account
        has no linked doctor profile (`user.doctor_id is None`) — this is a
        misconfigured account and must not silently fall through to
        "see everything" or "see nothing" behavior.
    """
    if current_user.role != UserRole.DOCTOR:
        return None
    if current_user.doctor_id is None:
        raise ForbiddenException(
            "Your account has the DOCTOR role but is not linked to a doctor "
            "profile. Contact an administrator to link your account before "
            "accessing appointments."
        )
    return current_user.doctor_id


OwnDoctorScope = Annotated[uuid.UUID | None, Depends(require_own_doctor_profile)]


def get_pagination_params(
    page: int = Query(default=1, ge=1, description="1-indexed page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    sort_by: str | None = Query(default=None, description="Field name to sort by"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)


Pagination = Annotated[PaginationParams, Depends(get_pagination_params)]
