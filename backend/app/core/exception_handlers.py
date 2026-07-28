"""
Global exception handlers — registered on the FastAPI app in app.main.

Ensures every error, whether a known business exception, a validation
error, or an unexpected crash, is returned to the client in the same
consistent JSON envelope (see schemas.common.ErrorResponse).

NOTE: This will be extended with request logging/audit hooks in Part 4.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger(__name__)


def _request_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning("AppException: %s (%s) at %s", exc.message, exc.error_code, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
            "path": str(request.url.path),
            "request_id": _request_id(request),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {
            "field": ".".join(str(loc) for loc in err["loc"] if loc != "body"),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]
    logger.info("Validation error at %s: %s", request.url.path, errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "error_code": "VALIDATION_ERROR",
                "message": "One or more fields failed validation",
                "details": {"errors": errors},
            },
            "path": str(request.url.path),
            "request_id": _request_id(request),
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "error_code": "HTTP_ERROR",
                "message": str(exc.detail),
                "details": {},
            },
            "path": str(request.url.path),
            "request_id": _request_id(request),
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception at %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {},
            },
            "path": str(request.url.path),
            "request_id": _request_id(request),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
