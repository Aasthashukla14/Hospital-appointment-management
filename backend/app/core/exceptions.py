"""
Application-wide custom exception hierarchy.

Services and repositories raise these instead of raw HTTPException so that
business logic stays framework-agnostic. The exception handlers registered
in app.main translate these into consistent JSON error responses.
"""


class AppException(Exception):
    """Base class for all application exceptions."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "An unexpected error occurred", details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundException(AppException):
    status_code = 404
    error_code = "NOT_FOUND"

    def __init__(self, resource: str = "Resource", identifier: str | None = None):
        message = f"{resource} not found" + (f" (id={identifier})" if identifier else "")
        super().__init__(message)


class ConflictException(AppException):
    status_code = 409
    error_code = "CONFLICT"


class ValidationException(AppException):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class BadRequestException(AppException):
    status_code = 400
    error_code = "BAD_REQUEST"


class UnauthorizedException(AppException):
    status_code = 401
    error_code = "UNAUTHORIZED"

    def __init__(self, message: str = "Authentication credentials were invalid or missing"):
        super().__init__(message)


class ForbiddenException(AppException):
    status_code = 403
    error_code = "FORBIDDEN"

    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message)


class DuplicateResourceException(ConflictException):
    error_code = "DUPLICATE_RESOURCE"

    def __init__(self, resource: str, field: str, value: str):
        message = f"{resource} with {field}='{value}' already exists"
        super().__init__(message)


class SlotUnavailableException(ConflictException):
    error_code = "SLOT_UNAVAILABLE"

    def __init__(self, message: str = "The requested time slot is not available"):
        super().__init__(message)


class InactiveResourceException(BadRequestException):
    error_code = "INACTIVE_RESOURCE"


class RateLimitExceededException(AppException):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"

    def __init__(
        self,
        message: str = "Too many requests. Please try again later.",
        retry_after: int | None = None,
    ):
        details = {"retry_after_seconds": retry_after} if retry_after is not None else {}
        super().__init__(message, details)


class TokenRevokedException(UnauthorizedException):
    error_code = "TOKEN_REVOKED"

    def __init__(self, message: str = "This token has been revoked. Please log in again."):
        super().__init__(message)
