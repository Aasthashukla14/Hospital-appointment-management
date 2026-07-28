"""
Security headers middleware.

Adds a standard set of defensive HTTP response headers to every response.
None of these replace proper input validation or auth checks — they are
cheap, well-established mitigations for browser-side attack classes
(clickjacking, MIME sniffing, referrer leakage, etc.) that cost nothing to
apply globally.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # Legacy header, ignored by modern browsers but harmless to send for
        # older clients that still honor it.
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS only makes sense once the app is actually served over HTTPS
        # (typically terminated at a load balancer/reverse proxy in front
        # of this service). Sending it in plain-http local development
        # would incorrectly instruct browsers to force https on localhost.
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"

        return response
