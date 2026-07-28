"""
Authentication service — business logic for registration, login, token
refresh, and logout. Depends only on repositories, never on the DB session
directly (beyond what the repository already wraps).
"""
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import DuplicateResourceException, UnauthorizedException
from app.core.logging import get_logger
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.token_blacklist import revoke_token
from app.models.audit_log import AuditAction
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from app.services.audit_log_service import AuditLogService

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit = AuditLogService(db)

    def register(self, payload: UserRegisterRequest, ip_address: str | None = None) -> User:
        if self.user_repo.get_by_username(payload.username):
            raise DuplicateResourceException("User", "username", payload.username)
        if self.user_repo.get_by_email(payload.email):
            raise DuplicateResourceException("User", "email", payload.email)

        user = self.user_repo.create(
            {
                "username": payload.username,
                "email": payload.email,
                "full_name": payload.full_name,
                "hashed_password": hash_password(payload.password),
                "role": payload.role,
                "is_active": True,
            }
        )
        self.audit.record(
            action=AuditAction.USER_REGISTERED,
            actor_user_id=user.id,
            actor_username=user.username,
            resource_type="User",
            resource_id=str(user.id),
            ip_address=ip_address,
            details={"role": payload.role.value},
        )
        self.user_repo.commit()
        logger.info("New user registered: %s (role=%s)", user.username, user.role)
        return user

    def authenticate(self, payload: UserLoginRequest, ip_address: str | None = None) -> User:
        user = self.user_repo.get_by_username(payload.username)
        if not user or not verify_password(payload.password, user.hashed_password):
            self.audit.record_and_commit(
                action=AuditAction.LOGIN_FAILURE,
                actor_username=payload.username,
                resource_type="User",
                success=False,
                ip_address=ip_address,
                message="Invalid username or password",
            )
            raise UnauthorizedException("Invalid username or password")
        if not user.is_active:
            self.audit.record_and_commit(
                action=AuditAction.LOGIN_FAILURE,
                actor_user_id=user.id,
                actor_username=user.username,
                resource_type="User",
                resource_id=str(user.id),
                success=False,
                ip_address=ip_address,
                message="Account is deactivated",
            )
            raise UnauthorizedException("This account has been deactivated")
        return user

    def login(self, payload: UserLoginRequest, ip_address: str | None = None) -> TokenResponse:
        user = self.authenticate(payload, ip_address=ip_address)
        tokens = self._issue_tokens(user)
        self.audit.record_and_commit(
            action=AuditAction.LOGIN_SUCCESS,
            actor_user_id=user.id,
            actor_username=user.username,
            resource_type="User",
            resource_id=str(user.id),
            ip_address=ip_address,
        )
        return tokens

    def refresh(self, refresh_token: str, ip_address: str | None = None) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise UnauthorizedException("Invalid or expired refresh token")

        if payload.get("type") != TokenType.REFRESH.value:
            raise UnauthorizedException("Token provided is not a refresh token")

        user = self.user_repo.get_by_username(payload.get("sub", ""))
        if not user or not user.is_active:
            raise UnauthorizedException("User no longer exists or is inactive")

        tokens = self._issue_tokens(user)
        self.audit.record_and_commit(
            action=AuditAction.TOKEN_REFRESH,
            actor_user_id=user.id,
            actor_username=user.username,
            resource_type="User",
            resource_id=str(user.id),
            ip_address=ip_address,
        )
        return tokens

    def logout(
        self,
        current_user: User,
        access_token_payload: dict,
        refresh_token: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """
        Revokes the caller's current access token (always) and, if provided,
        their refresh token too — so a client can invalidate both halves of
        the token pair in one call. See app.core.token_blacklist for how
        revocation works and its tradeoffs.
        """
        access_jti = access_token_payload.get("jti")
        access_exp = access_token_payload.get("exp")
        if access_jti and access_exp:
            revoke_token(access_jti, access_exp)

        if refresh_token:
            try:
                refresh_payload = decode_token(refresh_token)
            except JWTError:
                refresh_payload = None
            if refresh_payload and refresh_payload.get("type") == TokenType.REFRESH.value:
                refresh_jti = refresh_payload.get("jti")
                refresh_exp = refresh_payload.get("exp")
                if refresh_jti and refresh_exp:
                    revoke_token(refresh_jti, refresh_exp)

        self.audit.record_and_commit(
            action=AuditAction.LOGOUT,
            actor_user_id=current_user.id,
            actor_username=current_user.username,
            resource_type="User",
            resource_id=str(current_user.id),
            ip_address=ip_address,
        )
        logger.info("User logged out: %s", current_user.username)

    @staticmethod
    def _issue_tokens(user: User) -> TokenResponse:
        access_token = create_access_token(subject=user.username, role=user.role.value)
        refresh_token = create_refresh_token(subject=user.username, role=user.role.value)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
