"""
Authentication endpoints.
"""
from fastapi import APIRouter, Request, status

from app.api.deps import CurrentAccessTokenPayload, CurrentUser, DbSession
from app.schemas.auth import (
    LogoutRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _client_ip(request: Request) -> str | None:
    # Respect a trusted reverse-proxy header if present (e.g. behind nginx/
    # an API gateway), falling back to the direct connecting client.
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (staff account)",
)
def register(payload: UserRegisterRequest, db: DbSession, request: Request):
    service = AuthService(db)
    user = service.register(payload, ip_address=_client_ip(request))
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain access + refresh tokens",
)
def login(payload: UserLoginRequest, db: DbSession, request: Request):
    service = AuthService(db)
    return service.login(payload, ip_address=_client_ip(request))


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a valid refresh token for a new token pair",
)
def refresh(payload: RefreshTokenRequest, db: DbSession, request: Request):
    service = AuthService(db)
    return service.refresh(payload.refresh_token, ip_address=_client_ip(request))


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke the current access token (and optionally the refresh token)",
)
def logout(
    db: DbSession,
    current_user: CurrentUser,
    access_token_payload: CurrentAccessTokenPayload,
    request: Request,
    payload: LogoutRequest | None = None,
):
    service = AuthService(db)
    refresh_token = payload.refresh_token if payload else None
    service.logout(
        current_user,
        access_token_payload,
        refresh_token=refresh_token,
        ip_address=_client_ip(request),
    )
    return MessageResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user's profile",
)
def read_current_user(current_user: CurrentUser):
    return current_user
