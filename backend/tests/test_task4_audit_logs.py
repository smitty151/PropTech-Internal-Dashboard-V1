"""Task 4 — Audit log backend verification.

Verifies db.audit_logs entries for the following actions:
  - login
  - logout
  - memo_generated
  - data_source_refresh (nhai + sub_registrar)
  - verification_email_sent (register + resend)
Plus regression: AUDIT writes are best-effort (record_audit catches all exceptions).
"""
import os
import time
import uuid
from datetime import datetime, timezone

import pytest
import requests
from pymongo import MongoClient

# Hit localhost backend to avoid Cloudflare interference (per agent_to_agent_context_note)
BASE_URL = "http://localhost:8001"
ADMIN_EMAIL = "admin@placeholder.in"
ADMIN_PASSWORD = "admin123"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "placeholder_proptech")


@pytest.fixture(scope="module")
def db():
    client = MongoClient(MONGO_URL)
    return client[DB_NAME]


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
               timeout=10)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return s


def _latest(db, action: str, filt: dict | None = None):
    q = {"action": action}
    if filt:
        q.update(filt)
    return db.audit_logs.find_one(q, sort=[("timestamp", -1)])


def _is_iso_utc(ts: str) -> bool:
    try:
        # Must be parseable AND tz-aware
        dt = datetime.fromisoformat(ts)
        return dt.tzinfo is not None
    except Exception:
        return False


# ---------- 1. login ----------
def test_login_audit_entry(db):
    before = db.audit_logs.count_documents({"action": "login"})
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
               timeout=10)
    assert r.status_code == 200
    time.sleep(0.3)
    after = db.audit_logs.count_documents({"action": "login"})
    assert after >= before + 1, "login did not insert audit_log doc"

    doc = _latest(db, "login", {"user_email": ADMIN_EMAIL})
    assert doc is not None
    assert doc["action"] == "login"
    assert doc["user_email"] == ADMIN_EMAIL
    assert doc.get("user_id"), "user_id must be populated on login"
    assert isinstance(doc.get("ip"), str) and len(doc["ip"]) > 0
    assert _is_iso_utc(doc["timestamp"]), f"timestamp not ISO UTC: {doc['timestamp']}"
    payload = doc.get("payload") or {}
    assert payload.get("role") == "admin"


# ---------- 2. logout ----------
def test_logout_audit_entry(db):
    s = requests.Session()
    s.post(f"{BASE_URL}/api/auth/login",
           json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=10)
    before = db.audit_logs.count_documents({"action": "logout"})
    r = s.post(f"{BASE_URL}/api/auth/logout", timeout=10)
    assert r.status_code == 200
    time.sleep(0.3)
    after = db.audit_logs.count_documents({"action": "logout"})
    assert after >= before + 1

    doc = _latest(db, "logout")
    assert doc is not None
    # logout while token is still valid => user_id + user_email populated
    assert doc.get("user_email") == ADMIN_EMAIL
    assert doc.get("user_id")
    assert isinstance(doc.get("ip"), str) and len(doc["ip"]) > 0
    assert _is_iso_utc(doc["timestamp"])


# ---------- 3. memo_generated ----------
def test_memo_generated_audit_entry(db, admin_session):
    # Ensure comps + developments exist (idempotent refreshes)
    admin_session.post(f"{BASE_URL}/api/data-sources/nhai/refresh", timeout=20)
    admin_session.post(f"{BASE_URL}/api/data-sources/sub_registrar/refresh", timeout=20)
    time.sleep(0.5)

    before = db.audit_logs.count_documents({"action": "memo_generated"})
    payload = {"city": "Bengaluru", "size_sqft": 1200, "verified_only": False}
    r = admin_session.post(f"{BASE_URL}/api/valuation-memo", json=payload, timeout=30)
    assert r.status_code == 200, f"memo failed: {r.status_code} {r.text[:200]}"
    time.sleep(0.4)

    after = db.audit_logs.count_documents({"action": "memo_generated"})
    assert after == before + 1

    doc = _latest(db, "memo_generated", {"user_email": ADMIN_EMAIL})
    assert doc is not None
    assert doc["user_email"] == ADMIN_EMAIL
    assert doc.get("user_id")
    p = doc.get("payload") or {}
    for key in ("city", "size_sqft", "comps_count", "developments_count",
                "filename", "indicative_value"):
        assert key in p, f"missing payload key: {key}"
    assert p["city"] == "Bengaluru"
    assert p["size_sqft"] == 1200
    assert isinstance(p["comps_count"], int)
    assert isinstance(p["developments_count"], int)
    assert p["filename"].startswith("memo_Bengaluru_") and p["filename"].endswith(".pdf")
    assert _is_iso_utc(doc["timestamp"])


# ---------- 4a. data_source_refresh : nhai ----------
def test_data_source_refresh_nhai_audit(db, admin_session):
    before = db.audit_logs.count_documents(
        {"action": "data_source_refresh", "payload.source": "nhai"})
    r = admin_session.post(f"{BASE_URL}/api/data-sources/nhai/refresh", timeout=30)
    assert r.status_code == 200
    time.sleep(0.4)
    after = db.audit_logs.count_documents(
        {"action": "data_source_refresh", "payload.source": "nhai"})
    assert after == before + 1

    doc = _latest(db, "data_source_refresh", {"payload.source": "nhai"})
    assert doc["payload"]["source"] == "nhai"
    assert isinstance(doc["payload"]["ingested"], int)
    assert doc["user_email"] == ADMIN_EMAIL
    assert _is_iso_utc(doc["timestamp"])


# ---------- 4b. data_source_refresh : sub_registrar ----------
def test_data_source_refresh_sub_registrar_audit(db, admin_session):
    before = db.audit_logs.count_documents(
        {"action": "data_source_refresh", "payload.source": "sub_registrar"})
    r = admin_session.post(f"{BASE_URL}/api/data-sources/sub_registrar/refresh", timeout=30)
    assert r.status_code == 200
    time.sleep(0.4)
    after = db.audit_logs.count_documents(
        {"action": "data_source_refresh", "payload.source": "sub_registrar"})
    assert after == before + 1

    doc = _latest(db, "data_source_refresh", {"payload.source": "sub_registrar"})
    assert doc["payload"]["source"] == "sub_registrar"
    assert isinstance(doc["payload"]["ingested"], int)
    assert doc["user_email"] == ADMIN_EMAIL


# ---------- 5. verification_email_sent : register ----------
def test_register_emits_verification_email_audit(db):
    # Backend stores email lowercased; use lowercase to match
    transient_email = f"test_audit_{uuid.uuid4().hex[:10]}@example.com"
    before = db.audit_logs.count_documents(
        {"action": "verification_email_sent", "user_email": transient_email})
    r = requests.post(f"{BASE_URL}/api/auth/register",
                      json={"email": transient_email,
                            "password": "pw123456",
                            "name": "Audit Test"}, timeout=10)
    # register may return 200 or 201 — both fine
    assert r.status_code in (200, 201), f"register failed: {r.status_code} {r.text}"
    time.sleep(0.5)
    after = db.audit_logs.count_documents(
        {"action": "verification_email_sent", "user_email": transient_email})
    assert after == before + 1, f"expected +1 audit doc, got before={before} after={after}"

    doc = _latest(db, "verification_email_sent", {"user_email": transient_email})
    assert doc is not None
    p = doc.get("payload") or {}
    assert p.get("reason") == "register"
    # Email is the user_email field; also confirm it is the one we registered
    assert doc["user_email"] == transient_email
    assert _is_iso_utc(doc["timestamp"])

    # cleanup
    try:
        from pymongo import MongoClient
        MongoClient(MONGO_URL)[DB_NAME].users.delete_one({"email": transient_email})
    except Exception:
        pass


# ---------- 6. verification_email_sent : resend ----------
def test_resend_verification_emits_audit(db):
    # Register a fresh transient user first (so it exists and is unverified)
    transient_email = f"test_audit_resend_{uuid.uuid4().hex[:10]}@example.com"
    rr = requests.post(f"{BASE_URL}/api/auth/register",
                       json={"email": transient_email,
                             "password": "pw123456",
                             "name": "Audit Resend"}, timeout=10)
    assert rr.status_code in (200, 201)
    time.sleep(0.4)

    before = db.audit_logs.count_documents(
        {"action": "verification_email_sent", "user_email": transient_email,
         "payload.reason": "resend"})
    r = requests.post(f"{BASE_URL}/api/auth/resend-verification",
                      json={"email": transient_email}, timeout=10)
    assert r.status_code == 200
    time.sleep(0.4)
    after = db.audit_logs.count_documents(
        {"action": "verification_email_sent", "user_email": transient_email,
         "payload.reason": "resend"})
    assert after == before + 1

    doc = _latest(db, "verification_email_sent",
                  {"user_email": transient_email, "payload.reason": "resend"})
    assert (doc.get("payload") or {}).get("reason") == "resend"
    assert doc["user_email"] == transient_email

    try:
        MongoClient(MONGO_URL)[DB_NAME].users.delete_one({"email": transient_email})
    except Exception:
        pass


# ---------- 7. Every audit doc has ISO UTC ts + non-empty ip (when accessible) ----------
def test_every_audit_doc_has_iso_utc_timestamp(db):
    docs = list(db.audit_logs.find({}).sort("timestamp", -1).limit(40))
    assert len(docs) >= 6
    for d in docs:
        assert _is_iso_utc(d["timestamp"]), f"bad ts: {d.get('timestamp')}"
        # ip should be a non-empty string when present (record_audit captures
        # x-forwarded-for or client.host; for localhost it's '127.0.0.1' or similar)
        assert d.get("ip") is None or isinstance(d["ip"], str)


# ---------- 8. Best-effort: audit failures must not propagate ----------
def test_record_audit_swallows_exceptions():
    """record_audit catches all exceptions internally — verify by source inspection."""
    with open("/app/backend/core/audit.py") as f:
        src = f.read()
    assert "try:" in src and "except Exception" in src, (
        "record_audit must wrap insert_one in try/except to be best-effort"
    )
    # And log on failure, not raise
    assert "logger.warning" in src or "logger.error" in src
    # Ensure no `raise` from within the except block
    after_except = src.split("except Exception")[1]
    assert "raise" not in after_except.split("\n\n")[0], (
        "record_audit must not re-raise; it should be best-effort"
    )
