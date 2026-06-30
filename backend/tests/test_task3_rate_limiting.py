"""Task-3 rate limit (slowapi) tests.

Limits under test:
- /api/auth/*  : 5/minute per IP (decorator on each mutating route)
- /api/valuation-memo : 5/minute per authenticated user (user-id key)
- global default : 60/minute per IP

Each rate-bucket test sleeps ~65s after triggering 429 so the next test starts
with a fresh sliding window. Avoid running these in parallel.
"""
import os
import time
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "http://localhost:8001"
ADMIN_EMAIL = "admin@placeholder.in"
ADMIN_PASSWORD = "admin123"

WAIT_AFTER_429 = 65  # seconds — sliding-window reset


def _assert_429_json(r):
    """A clean 429 must be application/json and have {error, detail}."""
    assert r.status_code == 429, f"expected 429, got {r.status_code}: {r.text[:200]}"
    ctype = r.headers.get("content-type", "")
    assert "application/json" in ctype, f"content-type not json: {ctype!r}"
    body = r.json()
    assert body.get("error") == "rate_limit_exceeded", body
    assert isinstance(body.get("detail"), str) and "5 per 1 minute" in body["detail"] \
        or "60 per 1 minute" in body.get("detail", ""), body


# ---------- /api/auth/login rate-limit ----------
class TestAuthLoginRateLimit:
    """6 rapid POSTs to /api/auth/login => 6th returns 429 JSON."""

    def test_login_6th_call_returns_429_json(self):
        # Wait to ensure fresh window from prior tests (best-effort).
        time.sleep(WAIT_AFTER_429)
        s = requests.Session()
        last = None
        for i in range(5):
            last = s.post(f"{BASE_URL}/api/auth/login",
                          json={"email": f"nobody+{uuid.uuid4().hex[:6]}@example.com",
                                "password": "wrong"}, timeout=15)
            assert last.status_code in (401, 403), f"call {i}: {last.status_code} {last.text[:120]}"
        # 6th must be 429 (5/min)
        r = s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": "anyone@example.com", "password": "x"}, timeout=15)
        _assert_429_json(r)
        # Even with VALID admin creds, 6th call from same IP must still 429.
        r2 = s.post(f"{BASE_URL}/api/auth/login",
                    json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
        assert r2.status_code == 429, f"valid creds should still 429: {r2.status_code}"


# ---------- /api/auth/me is NOT rate-limited at 5/min bucket ----------
class TestAuthMeNotRateLimited:
    """/api/auth/me (GET, read-only) is only subject to global 60/min, not 5/min auth bucket."""

    def test_auth_me_allows_more_than_5_per_minute(self):
        time.sleep(WAIT_AFTER_429)
        # Login once (consumes 1 of the 5/min auth bucket)
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
        assert r.status_code == 200, r.text
        # 8 GETs to /me — none should be 429 from the 5/min auth bucket.
        for i in range(8):
            r = s.get(f"{BASE_URL}/api/auth/me", timeout=15)
            assert r.status_code == 200, f"call {i}: {r.status_code} {r.text[:120]}"


# ---------- /api/auth/* mutating endpoints (register / resend / logout) ----------
class TestAuthRegisterRateLimit:
    """6 rapid registers from same IP => 6th 429."""

    def test_register_5_then_429(self):
        time.sleep(WAIT_AFTER_429)
        s = requests.Session()
        last = None
        for i in range(5):
            payload = {
                "email": f"t3_{uuid.uuid4().hex[:10]}@example.com",
                "password": "abcdef",
                "name": "T3",
            }
            last = s.post(f"{BASE_URL}/api/auth/register", json=payload, timeout=15)
            assert last.status_code in (200, 201), f"call {i}: {last.status_code} {last.text[:120]}"
        r = s.post(f"{BASE_URL}/api/auth/register",
                   json={"email": f"t3_{uuid.uuid4().hex[:10]}@example.com",
                         "password": "abcdef", "name": "T3"}, timeout=15)
        _assert_429_json(r)


class TestAuthResendRateLimit:
    def test_resend_5_then_429(self):
        time.sleep(WAIT_AFTER_429)
        s = requests.Session()
        for i in range(5):
            r = s.post(f"{BASE_URL}/api/auth/resend-verification",
                       json={"email": f"nobody+{i}@example.com"}, timeout=15)
            assert r.status_code == 200, f"call {i}: {r.status_code}"
        r = s.post(f"{BASE_URL}/api/auth/resend-verification",
                   json={"email": "z@example.com"}, timeout=15)
        _assert_429_json(r)


class TestAuthLogoutRateLimit:
    def test_logout_5_then_429(self):
        time.sleep(WAIT_AFTER_429)
        s = requests.Session()
        for i in range(5):
            r = s.post(f"{BASE_URL}/api/auth/logout", timeout=15)
            assert r.status_code == 200, f"call {i}: {r.status_code}"
        r = s.post(f"{BASE_URL}/api/auth/logout", timeout=15)
        _assert_429_json(r)


# ---------- /api/valuation-memo per-user rate-limit ----------
class TestValuationMemoUserRateLimit:
    """6 rapid POSTs by admin => 6th 429. Key is user-id, NOT IP."""

    def test_admin_memo_5_then_429(self):
        time.sleep(WAIT_AFTER_429)
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
        assert r.status_code == 200, r.text
        body = {"city": "Mumbai", "size_sqft": 1000.0, "verified_only": False}
        last = None
        for i in range(5):
            last = s.post(f"{BASE_URL}/api/valuation-memo", json=body, timeout=60)
            # Memo route must still return PDF for valid calls
            assert last.status_code == 200, f"call {i}: {last.status_code} {last.text[:200]}"
            assert last.headers.get("content-type", "").startswith("application/pdf"), \
                f"call {i} not pdf: {last.headers.get('content-type')}"
            assert len(last.content) > 100, f"call {i}: pdf too small"
        r = s.post(f"{BASE_URL}/api/valuation-memo", json=body, timeout=60)
        _assert_429_json(r)


# ---------- global default 60/minute on unauthenticated GET ----------
class TestGlobalDefaultRateLimit:
    """61 rapid GETs to /api/markets => 61st 429."""

    def test_markets_60_then_429(self):
        time.sleep(WAIT_AFTER_429)
        s = requests.Session()
        for i in range(60):
            r = s.get(f"{BASE_URL}/api/markets", timeout=15)
            assert r.status_code == 200, f"call {i}: {r.status_code} {r.text[:120]}"
        r = s.get(f"{BASE_URL}/api/markets", timeout=15)
        _assert_429_json(r)


# ---------- sliding-window reset ----------
class TestRateLimitWindowReset:
    """After 60s, the previously-blocked bucket allows requests again."""

    def test_login_window_resets_after_60s(self):
        time.sleep(WAIT_AFTER_429)
        s = requests.Session()
        # Burn the bucket
        for _ in range(5):
            s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": "x@example.com", "password": "x"}, timeout=15)
        r = s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": "x@example.com", "password": "x"}, timeout=15)
        assert r.status_code == 429
        # Wait for sliding window to reset
        time.sleep(WAIT_AFTER_429)
        r2 = s.post(f"{BASE_URL}/api/auth/login",
                    json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
        assert r2.status_code == 200, f"after reset expected 200, got {r2.status_code}: {r2.text[:200]}"
        # Verify cookies still set on success — decorator must not break response.
        assert "access_token" in s.cookies, "access_token cookie missing after rate-window reset"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-n", "0"])
