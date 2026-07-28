"""
Rate limiting middleware.

SCOPE OF THIS IMPLEMENTATION
------------------------------
A full, production-grade rate limiter (per-user AND per-IP, sliding-window
or token-bucket, backed by a shared store) is a substantial piece of
infrastructure on its own. What's implemented here is a deliberately small
but genuinely functional fixed-window limiter, scoped to the endpoints that
matter most for a HIMS deployment: authentication. `/auth/login` and
`/auth/register` are brute-force / credential-stuffing / spam-registration
targets in a way that, say, `GET /patients/{id}` is not, so they get an
explicit per-IP request cap. Every other route is left unthrottled by this
middleware.

ALGORITHM
---------
Fixed window: for each (client_ip, path) pair, count requests in the current
`window_seconds` bucket; once the count exceeds `max_requests`, further
requests in that window get HTTP 429 until the window rolls over. Fixed-
window is simpler than sliding-window/token-bucket and can allow a burst of
up to 2x the limit right at a window boundary — an acceptable tradeoff for
protecting login/register endpoints, where the goal is "make brute-forcing
expensive," not perfectly smooth traffic shaping.

PRODUCTION TRADEOFF (documented per the assignment's request)
-----------------------------------------------------------------
Like app.core.token_blacklist, the counters here live in an in-process
dict:
    * Not shared across multiple workers/replicas — an attacker distributing
      requests across processes (or you simply scaling to >1 replica)
      effectively multiplies the real limit by the process count.
    * Not durable across restarts — a redeploy resets everyone's counters.

For real production traffic, replace the counter storage with Redis
(`INCR` + `EXPIRE`, or a library such as `slowapi`/`fastapi-limiter` backed
by Redis) so limits are enforced consistently across every process and
survive restarts. The request-classification logic (which paths, what
limits) would carry over unchanged.
"""
import threading
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

# path -> (max_requests, window_seconds)
_RATE_LIMITED_PATHS: dict[str, tuple[int, int]] = {
    "/api/v1/auth/login": (10, 60),
    "/api/v1/auth/register": (5, 60),
}


class _FixedWindowCounter:
    def __init__(self) -> None:
        self._counts: dict[tuple[str, str], tuple[int, float]] = {}  # key -> (count, window_start)
        self._lock = threading.Lock()

    def hit(self, key: tuple[str, str], max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """Registers one request for `key`. Returns (allowed, retry_after_seconds)."""
        now = time.time()
        with self._lock:
            count, window_start = self._counts.get(key, (0, now))
            if now - window_start >= window_seconds:
                # New window.
                count, window_start = 0, now

            count += 1
            self._counts[key] = (count, window_start)

            if count > max_requests:
                retry_after = max(0, int(window_seconds - (now - window_start)))
                return False, retry_after
            return True, 0


_counter = _FixedWindowCounter()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        limit_config = _RATE_LIMITED_PATHS.get(request.url.path)
        if limit_config is None:
            return await call_next(request)

        max_requests, window_seconds = limit_config
        key = (_client_ip(request), request.url.path)
        allowed, retry_after = _counter.hit(key, max_requests, window_seconds)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "details": {"retry_after_seconds": retry_after},
                    },
                    "path": str(request.url.path),
                    "request_id": request.headers.get("X-Request-ID"),
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
