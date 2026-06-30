"""Task-3 confirmatory rate-limit suite (lean).

Per E1's instructions:
- Hit http://localhost:8001 directly (bypass Cloudflare).
- Sleep 65s ONCE at the very start to clear any prior bucket, then run the
  three burst tests sequentially with 65s sleeps in-between.
- Only assert: status code on each call, JSON content-type on 429, body has
  'error' and 'detail' keys.

Limits under test:
  POST /api/auth/login    : 5/min per IP
  POST /api/valuation-memo: 5/min per authenticated user
  GET  /api/markets       : 60/min global default per IP
"""
import time
import requests

BASE_URL = "http://localhost:8001"
ADMIN_EMAIL = "admin@placeholder.in"
ADMIN_PASSWORD = "admin123"
WAIT = 65  # sliding-window reset

# Module-level session so we share IP-based bucket across calls in this process.
_session = requests.Session()


def _assert_clean_429(r):
    """A clean 429 must be application/json with {error, detail} keys."""
    assert r.status_code == 429, f"expected 429, got {r.status_code}: {r.text[:200]}"
    ctype = r.headers.get("content-type", "")
    assert "application/json" in ctype, f"content-type not json: {ctype!r}"
    body = r.json()
    assert "error" in body and "detail" in body, f"missing keys: {body}"
    assert body["error"] == "rate_limit_exceeded", body


def test_00_warmup_sleep():
    """Clear any pre-existing rate-limit bucket from manual main-agent checks."""
    time.sleep(WAIT)


def test_01_auth_login_5_per_min_per_ip():
    """6 rapid POSTs to /api/auth/login => 6th is 429 clean JSON."""
    s = requests.Session()
    for i in range(5):
        r = s.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "nobody@example.com", "password": "wrong"},
            timeout=15,
        )
        assert r.status_code in (200, 401, 403), f"call {i}: {r.status_code} {r.text[:120]}"
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "nobody@example.com", "password": "wrong"},
        timeout=15,
    )
    _assert_clean_429(r)
    # detail should reference the 5/min limit
    assert "5 per 1 minute" in r.json()["detail"], r.json()


def test_02_valuation_memo_5_per_min_per_user():
    """Wait for fresh window, log in as admin, 6 rapid POSTs => 6th 429 clean JSON."""
    time.sleep(WAIT)
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
    body = {"city": "Mumbai", "size_sqft": 1000.0, "verified_only": False}
    for i in range(5):
        r = s.post(f"{BASE_URL}/api/valuation-memo", json=body, timeout=60)
        assert r.status_code == 200, f"call {i}: {r.status_code} {r.text[:200]}"
    r = s.post(f"{BASE_URL}/api/valuation-memo", json=body, timeout=60)
    _assert_clean_429(r)
    assert "5 per 1 minute" in r.json()["detail"], r.json()


def test_03_global_60_per_min_on_markets():
    """Wait for fresh window, 61 rapid GETs to /api/markets => 61st 429 clean JSON."""
    time.sleep(WAIT)
    s = requests.Session()
    for i in range(60):
        r = s.get(f"{BASE_URL}/api/markets", timeout=15)
        assert r.status_code == 200, f"call {i}: {r.status_code} {r.text[:120]}"
    r = s.get(f"{BASE_URL}/api/markets", timeout=15)
    _assert_clean_429(r)
    assert "60 per 1 minute" in r.json()["detail"], r.json()
