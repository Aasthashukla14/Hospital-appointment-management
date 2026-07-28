"""
Token revocation ("blacklist") store.

WHY THIS EXISTS
----------------
JWT access/refresh tokens are stateless by design: the server can validate
them without a DB round-trip. That's great for performance but means there
is no built-in way to force a token to stop working before it naturally
expires — which is exactly what a `/auth/logout` endpoint needs to do.

The standard fix is to track only the small `jti` (JWT ID) claim of tokens
that have been explicitly revoked, and reject any token whose `jti` shows up
in that store, even if the token's signature and expiry are otherwise valid.

IMPLEMENTATION — IN-MEMORY, WITH A DOCUMENTED TRADEOFF
--------------------------------------------------------
This implementation keeps revoked `jti`s in an in-process dict, each entry
expiring at the same time the underlying token itself would have expired
(so the set never grows unbounded). This is intentionally the simplest
correct implementation and is a fine default for local development, a
single-process demo/deployment, or the scope of this assignment.

Tradeoffs to be aware of before shipping this to real production traffic:
    * Not shared across processes/workers. If you run this app with more
      than one uvicorn/gunicorn worker (or more than one container replica),
      a token revoked on one process is still accepted by the others,
      because each process has its own copy of this in-memory dict.
    * Not durable. A process restart (deploy, crash, autoscale-down) clears
      all revocations; previously "logged out" tokens become valid again
      until they naturally expire.
    * Unbounded-ish memory in pathological cases (extremely high logout
      volume before cleanup runs), though the periodic sweep of expired
      entries keeps this bounded in practice.

For a real multi-instance production deployment, swap this module's storage
for a shared, durable store with native per-key TTL — Redis
(`SETEX blacklist:<jti> <ttl_seconds> 1`) is the conventional choice — while
keeping the exact same `revoke()` / `is_revoked()` call sites in the rest of
the app unchanged.
"""
import threading
import time
from datetime import datetime, timezone


class InMemoryTokenBlacklist:
    """Thread-safe store of revoked JWT `jti`s, each with its own expiry."""

    def __init__(self) -> None:
        self._revoked: dict[str, float] = {}  # jti -> unix expiry timestamp
        self._lock = threading.Lock()
        self._last_sweep = time.monotonic()
        self._sweep_interval_seconds = 60.0

    def revoke(self, jti: str, expires_at: datetime) -> None:
        """Mark a token's jti as revoked until its natural expiry."""
        with self._lock:
            self._revoked[jti] = expires_at.timestamp()
            self._maybe_sweep_locked()

    def is_revoked(self, jti: str) -> bool:
        with self._lock:
            expiry = self._revoked.get(jti)
            if expiry is None:
                return False
            if expiry <= time.time():
                # Naturally expired anyway — clean it up lazily and treat
                # it as no longer relevant (the JWT `exp` check would have
                # rejected it regardless).
                self._revoked.pop(jti, None)
                return False
            return True

    def _maybe_sweep_locked(self) -> None:
        """Periodically drop entries whose underlying token has already
        expired, so the dict doesn't grow forever. Caller must hold _lock.
        """
        now_monotonic = time.monotonic()
        if now_monotonic - self._last_sweep < self._sweep_interval_seconds:
            return
        self._last_sweep = now_monotonic
        now_ts = time.time()
        expired_jtis = [jti for jti, exp in self._revoked.items() if exp <= now_ts]
        for jti in expired_jtis:
            self._revoked.pop(jti, None)


# Process-wide singleton. See module docstring for the multi-instance caveat.
token_blacklist = InMemoryTokenBlacklist()


def revoke_token(jti: str, exp_timestamp: int) -> None:
    """Revoke a token given the raw `exp` (unix seconds) claim from its payload."""
    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    token_blacklist.revoke(jti, expires_at)


def is_token_revoked(jti: str | None) -> bool:
    if not jti:
        return False
    return token_blacklist.is_revoked(jti)
