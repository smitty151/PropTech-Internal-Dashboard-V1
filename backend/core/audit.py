"""Audit log helper — records auth + data-mutation events to db.audit_logs.

Events tracked: login, logout, memo_generated, data_source_refresh,
verification_email_sent. Each entry includes user_id (if known), user_email,
action, ip, payload, timestamp (UTC ISO).
"""
import logging
from typing import Optional

from fastapi import Request

from core.db import db
from models import AuditLog

logger = logging.getLogger(__name__)


def _client_ip(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


async def record_audit(
    action: str,
    request: Optional[Request] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    payload: Optional[dict] = None,
) -> None:
    """Best-effort write to db.audit_logs. Never raises into the caller."""
    try:
        entry = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            ip=_client_ip(request),
            payload=payload or {},
        )
        doc = entry.to_mongo()
        doc.pop("_id", None)
        await db.audit_logs.insert_one(doc)
    except Exception as e:  # pragma: no cover — audit must never break the request
        logger.warning(f"audit_log write failed (action={action}): {e}")
