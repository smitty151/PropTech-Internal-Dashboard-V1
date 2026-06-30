"""End-to-end backend regression tests for PlaceHolder PropTech post-router refactor.

Covers: auth (register/login/logout/me/resend), data (markets/developments/comps/reits),
calculator (WACC), data-sources (NHAI/Sub-Registrar/CSV template/list), memo (PDF + history),
and unauthenticated access protection.
"""
import os
import secrets
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or \
    "https://76783c70-c695-445e-8750-f468bddea4e1.preview.emergentagent.com"

ADMIN_EMAIL = "admin@placeholder.in"
ADMIN_PASSWORD = "admin123"


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    assert "access_token" in s.cookies, "access_token cookie not set"
    assert "refresh_token" in s.cookies, "refresh_token cookie not set"
    return s


@pytest.fixture(scope="session")
def random_email():
    return f"test_{uuid.uuid4().hex[:10]}@example.com"


# ---------- auth ----------
class TestAuth:
    def test_admin_login_sets_cookies_and_returns_user(self):
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        assert data["email_verified"] is True
        assert "id" in data
        assert "access_token" in s.cookies
        assert "refresh_token" in s.cookies

    def test_me_returns_admin(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/auth/me", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        assert "id" in data
        # password_hash + verification_token must be stripped
        assert "password_hash" not in data
        assert "verification_token" not in data
        assert "_id" not in data

    def test_logout_clears_cookies(self):
        s = requests.Session()
        s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
        r = s.post(f"{BASE_URL}/api/auth/logout", timeout=30)
        assert r.status_code == 200
        assert r.json().get("ok") is True
        # After logout the /me call should fail
        r2 = s.get(f"{BASE_URL}/api/auth/me", timeout=30)
        assert r2.status_code == 401

    def test_register_creates_unverified_user(self, random_email):
        r = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": random_email, "password": "secret123",
            "name": "Reg Test", "company": "Acme",
        }, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        assert data["email"] == random_email.lower()
        assert data["email_verified"] is False

    def test_register_duplicate_rejected(self, random_email):
        r = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": random_email, "password": "secret123",
            "name": "Dup", "company": "Acme",
        }, timeout=30)
        assert r.status_code == 400

    def test_unverified_user_cannot_login(self, random_email):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": random_email, "password": "secret123"}, timeout=30)
        assert r.status_code == 403, r.text
        assert "verify" in r.json().get("detail", "").lower()

    def test_login_invalid_password(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": ADMIN_EMAIL, "password": "wrong_pw"}, timeout=30)
        assert r.status_code == 401

    def test_resend_verification_returns_ok_for_anything(self):
        # existing email
        r = requests.post(f"{BASE_URL}/api/auth/resend-verification",
                          json={"email": "noone_xyz@example.com"}, timeout=30)
        assert r.status_code == 200
        assert r.json().get("ok") is True


# ---------- data ----------
class TestData:
    def test_markets_authenticated(self, admin_session):
        # markets is currently NOT auth-protected, but admin session is fine
        r = admin_session.get(f"{BASE_URL}/api/markets", timeout=30)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_developments(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/developments", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)

    def test_developments_stats(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/developments/stats", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "total" in data and "by_type" in data and "by_city" in data
        assert isinstance(data["total"], int)

    def test_comps(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/comps", timeout=30)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_comps_stats(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/comps/stats", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        for key in ("total", "sale", "rent", "by_city"):
            assert key in data

    def test_reits(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/reits", timeout=30)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_developments_verified_only_filter(self, admin_session):
        r_all = admin_session.get(f"{BASE_URL}/api/developments", timeout=30).json()
        r_v = admin_session.get(f"{BASE_URL}/api/developments?verified_only=true", timeout=30)
        assert r_v.status_code == 200
        rows = r_v.json()
        assert isinstance(rows, list)
        assert len(rows) <= len(r_all)
        for d in rows:
            src = d.get("source", "")
            assert src.startswith("NHAI") or src.startswith("Sub-Registrar"), f"unverified slipped through: {src!r}"

    def test_comps_verified_only_filter(self, admin_session):
        r_all = admin_session.get(f"{BASE_URL}/api/comps", timeout=30).json()
        r_v = admin_session.get(f"{BASE_URL}/api/comps?verified_only=true", timeout=30)
        assert r_v.status_code == 200
        rows = r_v.json()
        assert len(rows) <= len(r_all)
        for c in rows:
            src = c.get("source", "")
            assert src.startswith("NHAI") or src.startswith("Sub-Registrar")


# ---------- calculator ----------
class TestCalculator:
    def test_wacc(self, admin_session):
        payload = {
            "equity_amount": 100.0,
            "cost_of_equity": 15.0,
            "tax_rate": 25.17,
            "debt": [
                {"name": "Sr Debt", "amount": 60.0, "rate": 10.0},
                {"name": "Mezz", "amount": 40.0, "rate": 14.0},
            ],
        }
        r = admin_session.post(f"{BASE_URL}/api/calculator/wacc", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("weights", "weighted_cost_of_debt", "after_tax_cost_of_debt",
                  "cost_of_equity", "wacc", "discount_rate", "total_capital_inr_cr"):
            assert k in d
        # weights add to ~1
        assert abs(d["weights"]["equity"] + d["weights"]["debt"] - 1.0) < 1e-6
        # weighted Kd = (60*10 + 40*14)/100 = 11.6
        assert abs(d["weighted_cost_of_debt"] - 11.6) < 1e-6
        assert d["cost_of_equity"] == 15.0
        assert d["total_capital_inr_cr"] == 200.0
        # wacc = 0.5*15 + 0.5*11.6*(1-0.2517) ≈ 11.84
        assert 11.0 < d["wacc"] < 13.0


# ---------- data sources ----------
class TestDataSources:
    def test_nhai_refresh(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/data-sources/nhai/refresh", timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["source"] == "NHAI / data.gov.in"
        assert isinstance(d["ingested"], int)

    def test_sub_registrar_refresh(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/data-sources/sub_registrar/refresh", timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["source"] == "Maharashtra IGR + Delhi DORIS"
        assert isinstance(d["ingested"], int)

    def test_list_data_sources(self, admin_session):
        # depends on prior refresh runs writing last_run docs
        r = admin_session.get(f"{BASE_URL}/api/data-sources", timeout=30)
        assert r.status_code == 200, r.text
        sources = r.json()
        assert isinstance(sources, list)
        assert len(sources) == 3
        by_key = {s["key"]: s for s in sources}
        assert {"nhai", "sub_registrar", "csv_import"} == set(by_key.keys())
        # After running refresh in this run, both nhai + sub_registrar should have last_run
        assert by_key["nhai"].get("last_run") is not None
        assert by_key["sub_registrar"].get("last_run") is not None

    def test_csv_template(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/data-sources/csv/template", timeout=30)
        assert r.status_code == 200, r.text
        ct = r.headers.get("content-type", "")
        assert "text/csv" in ct, ct
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd and "comps_template.csv" in cd
        assert "city,submarket" in r.text


# ---------- memo ----------
class TestMemo:
    def test_valuation_memo_returns_pdf_and_persists(self, admin_session):
        payload = {
            "city": "Mumbai",
            "size_sqft": 1500.0,
            "verified_only": False,  # ensure comps exist even before refresh in fresh DBs
        }
        before = admin_session.get(f"{BASE_URL}/api/memos", timeout=30).json()
        r = admin_session.post(f"{BASE_URL}/api/valuation-memo", json=payload, timeout=120)
        assert r.status_code == 200, r.text[:500]
        assert r.headers.get("content-type", "").startswith("application/pdf"), r.headers
        assert r.content[:4] == b"%PDF", f"Not a PDF: {r.content[:20]!r}"
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd and ".pdf" in cd

        after = admin_session.get(f"{BASE_URL}/api/memos", timeout=30)
        assert after.status_code == 200
        after_list = after.json()
        assert isinstance(after_list, list)
        assert len(after_list) >= len(before) + 1
        latest = after_list[0]
        assert latest["city"] == "Mumbai"
        assert latest["size_sqft"] == 1500.0
        assert "filename" in latest and latest["filename"].endswith(".pdf")


# ---------- unauthenticated protection ----------
class TestUnauth:
    @pytest.mark.parametrize("path,method,body", [
        ("/api/auth/me", "GET", None),
        ("/api/developments", "GET", None),
        ("/api/developments/stats", "GET", None),
        ("/api/comps", "GET", None),
        ("/api/comps/stats", "GET", None),
        ("/api/reits", "GET", None),
        ("/api/data-sources", "GET", None),
        ("/api/data-sources/csv/template", "GET", None),
        ("/api/data-sources/nhai/refresh", "POST", {}),
        ("/api/data-sources/sub_registrar/refresh", "POST", {}),
        ("/api/calculator/wacc", "POST", {
            "equity_amount": 1, "cost_of_equity": 10,
            "debt": [{"name": "x", "amount": 1, "rate": 5}],
        }),
        ("/api/valuation-memo", "POST", {"city": "Mumbai", "size_sqft": 1000}),
        ("/api/memos", "GET", None),
    ])
    def test_protected_endpoints_require_auth(self, path, method, body):
        r = requests.request(method, f"{BASE_URL}{path}", json=body, timeout=30)
        assert r.status_code == 401, f"{method} {path} => {r.status_code} (expected 401)"
