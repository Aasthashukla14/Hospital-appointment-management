"""
Application entrypoint.
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.middleware.request_id_middleware import RequestIdMiddleware
from app.middleware.security_headers_middleware import SecurityHeadersMiddleware

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s [%s]", settings.PROJECT_NAME, settings.VERSION, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Backend for the Appointment Management Module of a Hospital "
        "Information Management System (HIMS). Provides Patient, "
        "Department, Doctor, and Appointment management with JWT auth "
        "and role-based access control."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------
# Middleware (order matters: outermost registered last executes first
# on the way in, and last on the way out).
#
# Desired request flow (outermost -> innermost):
#   RateLimitMiddleware      reject abusive traffic before anything else runs
#   SecurityHeadersMiddleware   applied to every response, including 429s
#   log_requests (app.middleware) access logging around everything downstream
#   RequestIdMiddleware       assigns the id everything else (incl. logging) uses
#   CORSMiddleware            closest to the route handlers
#
# CORS note: `allow_credentials=True` together with a literal wildcard
# origin ("*") is rejected by browsers (the Fetch spec forbids sending
# `Access-Control-Allow-Origin: *` alongside credentialed requests), so if
# BACKEND_CORS_ORIGINS is left at its permissive default we disable
# allow_credentials to keep the combination valid. In any real deployment,
# BACKEND_CORS_ORIGINS should be set to the exact list of trusted frontend
# origins, at which point allow_credentials=True is safe and desired for
# cookie/Authorization-header-based auth flows from a browser.
# ---------------------------------------------------------------------
_cors_allows_all_origins = settings.BACKEND_CORS_ORIGINS == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=not _cors_allows_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestIdMiddleware)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.2fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)


# ---------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------
register_exception_handlers(app)

# ---------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"], summary="Liveness/readiness probe")
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME, "version": settings.VERSION}
