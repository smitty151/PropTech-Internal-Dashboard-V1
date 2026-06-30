"""slowapi rate-limit configuration.

- Global default: 60 req/min per IP
- /api/auth/*: 5 req/min per IP (decorator on each auth route)
- /api/valuation-memo: 5 req/min per user (decorator using user-id key)
- 429 responses are returned as clean JSON.

Set `LIMITER_ENABLED=false` in the env to bypass rate limiting (used by the
test suite so back-to-back regression runs aren't throttled).
"""
import os

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def _user_or_ip_key(request: Request) -> str:
    """Prefer authenticated user-id (sub-claim) when available; else remote IP."""
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if token:
        try:
            payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except jwt.PyJWTError:
            pass
    return f"ip:{get_remote_address(request)}"


_ENABLED = os.environ.get("LIMITER_ENABLED", "true").lower() != "false"

# Single shared limiter — global default applied via middleware in server.py.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"] if _ENABLED else [],
    headers_enabled=False,
    enabled=_ENABLED,
)


def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Clean JSON 429 response (slowapi's default returns a bare 'error' message).

    NOTE: Must be a sync function so slowapi's middleware (sync_check_limits)
    can call it directly for global-default limits. Async handlers are silently
    dropped by slowapi and replaced with its own default response.
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": f"Rate limit exceeded: {exc.detail}. Please try again shortly.",
        },
        headers={"Retry-After": "60"},
    )
