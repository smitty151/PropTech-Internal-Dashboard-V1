"""Task-2 specific tests: validate PyObjectId + BaseDocument migration.

Covers the migration-specific contract:
- List endpoints DO NOT leak `_id` or `id` in response payloads.
- Writes go through Model.to_mongo() — register persists expected fields, no `id` string key.
- NHAI refresh upserts Development docs with all expected keys.
- Sub-Registrar refresh upserts Comp docs with all expected keys.
- valuation-memo persists a Memo doc with all expected keys.
- /data-sources/*/refresh upserts data_source_runs correctly.
- GET /api/auth/me strips password_hash / verification_token / verification_expires.
"""
import os
import uuid

import pytest
import requests
from bson import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv

# Load backend .env so MONGO_URL + DB_NAME are available.
load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or \
    "https://76783c70-c695-445e-8750-f468bddea4e1.preview.emergentagent.com"
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

ADMIN_EMAIL = "admin@placeholder.in"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def mongo_db():
    client = MongoClient(MONGO_URL)
    yield client[DB_NAME]
    client.close()


@pytest.fixture(scope="module")
def admin_session():
    import time
    s = requests.Session()
    # Auth is rate-limited at 5/min per IP; back off if exhausted by prior test files.
    for _ in range(3):
        r = s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
        if r.status_code == 429:
            time.sleep(65)
            continue
        break
    assert r.status_code == 200, r.text
    return s


# ---------- response-shape contract ----------

class TestListEndpointsNoIdLeak:
    """List endpoints must NOT expose `_id` (Mongo) or `id` (model alias)."""

    def test_developments_no_id_or_mongo_id(self, admin_session, mongo_db):
        # First trigger NHAI refresh so at least 1 NHAI doc (with valid model fields) exists.
        admin_session.post(f"{BASE_URL}/api/data-sources/nhai/refresh", timeout=60)
        # filter to verified_only so we ONLY hit NHAI/registrar docs that have valid model fields
        # (legacy seed docs are missing `source` and break the model — see test_proptech_backend
        #  regression — that's a separate bug filed against seed_data.py).
        r = admin_session.get(f"{BASE_URL}/api/developments?verified_only=true", timeout=30)
        assert r.status_code == 200, r.text
        rows = r.json()
        assert isinstance(rows, list) and len(rows) > 0
        for row in rows:
            assert "_id" not in row, f"leaked _id: {row}"
            assert "id" not in row, f"leaked id: {row}"
            # And model fields present
            for key in ("name", "type", "city", "source"):
                assert key in row, f"missing {key} in {row}"

    def test_comps_no_id_or_mongo_id(self, admin_session):
        admin_session.post(f"{BASE_URL}/api/data-sources/sub_registrar/refresh", timeout=60)
        r = admin_session.get(f"{BASE_URL}/api/comps?verified_only=true", timeout=30)
        assert r.status_code == 200, r.text
        rows = r.json()
        assert isinstance(rows, list) and len(rows) > 0
        for row in rows:
            assert "_id" not in row
            assert "id" not in row
            for key in ("city", "property_type", "transaction_type", "size_sqft", "source"):
                assert key in row

    def test_reits_no_id_or_mongo_id(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/reits", timeout=30)
        assert r.status_code == 200, r.text
        rows = r.json()
        assert isinstance(rows, list)
        for row in rows:
            assert "_id" not in row
            assert "id" not in row
            assert "symbol" in row
            assert "dividend_yield" in row

    def test_memos_no_id_or_mongo_id(self, admin_session):
        # ensure at least one memo exists
        admin_session.post(f"{BASE_URL}/api/valuation-memo",
                           json={"city": "Mumbai", "size_sqft": 1200, "verified_only": False},
                           timeout=120)
        r = admin_session.get(f"{BASE_URL}/api/memos", timeout=30)
        assert r.status_code == 200, r.text
        rows = r.json()
        assert isinstance(rows, list) and len(rows) > 0
        for row in rows:
            assert "_id" not in row
            assert "id" not in row
            for key in ("user_id", "user_email", "city", "size_sqft", "filename", "generated_at"):
                assert key in row


# ---------- register persists via User.to_mongo() ----------

class TestRegisterPersistsViaModel:
    def test_register_user_mongo_doc_shape(self, mongo_db):
        email = f"test_task2_{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email, "password": "secret123", "name": "T2 User", "company": "T2",
        }, timeout=30)
        assert r.status_code == 200, r.text

        doc = mongo_db.users.find_one({"email": email})
        assert doc is not None, "user not persisted"
        # Mongo `_id` must be ObjectId (auto-generated by Mongo, not a string).
        assert isinstance(doc["_id"], ObjectId), f"_id is {type(doc['_id'])}, expected ObjectId"
        # The model maps id<->_id; the persisted doc must NOT carry a redundant string `id` field.
        assert "id" not in doc, "redundant 'id' key found in Mongo doc — to_mongo should pop it"
        # All required model fields present
        for key in ("email", "password_hash", "name", "role", "email_verified", "created_at"):
            assert key in doc, f"missing {key} in persisted user doc"
        assert doc["email"] == email
        assert doc["role"] == "user"
        assert doc["email_verified"] is False
        # cleanup
        mongo_db.users.delete_one({"email": email})


# ---------- NHAI / Sub-Registrar refresh persistence ----------

class TestRefreshUpserts:
    def test_nhai_refresh_dev_doc_shape(self, admin_session, mongo_db):
        r = admin_session.post(f"{BASE_URL}/api/data-sources/nhai/refresh", timeout=60)
        assert r.status_code == 200, r.text
        # Spot-check one NHAI-sourced development doc
        doc = mongo_db.developments.find_one({"source": "NHAI / data.gov.in"})
        assert doc is not None, "no NHAI dev persisted"
        assert isinstance(doc["_id"], ObjectId)
        assert "id" not in doc
        for key in ("external_id", "name", "type", "status", "city",
                    "lat", "lng", "developer", "investment_inr_cr",
                    "size", "completion_year", "description", "source", "ingested_at"):
            assert key in doc, f"missing {key} on NHAI dev"
        assert doc["type"] == "Highway"
        assert doc["developer"] == "NHAI / MoRTH"

    def test_sub_registrar_refresh_comp_doc_shape(self, admin_session, mongo_db):
        r = admin_session.post(f"{BASE_URL}/api/data-sources/sub_registrar/refresh", timeout=60)
        assert r.status_code == 200, r.text
        doc = mongo_db.comps.find_one({"source": {"$regex": "^Sub-Registrar"}})
        assert doc is not None, "no Sub-Registrar comp persisted"
        assert isinstance(doc["_id"], ObjectId)
        assert "id" not in doc
        for key in ("external_id", "city", "submarket", "address", "property_type",
                    "transaction_type", "size_sqft", "building_age_yrs",
                    "asking_price_inr", "sold_price_inr", "price_per_sqft",
                    "owner", "transaction_date", "source", "ingested_at"):
            assert key in doc, f"missing {key} on Sub-Registrar comp"

    def test_data_source_runs_upsert(self, admin_session, mongo_db):
        admin_session.post(f"{BASE_URL}/api/data-sources/nhai/refresh", timeout=60)
        admin_session.post(f"{BASE_URL}/api/data-sources/sub_registrar/refresh", timeout=60)
        for key in ("nhai", "sub_registrar"):
            doc = mongo_db.data_source_runs.find_one({"key": key})
            assert doc is not None, f"no run doc for {key}"
            assert isinstance(doc["_id"], ObjectId)
            assert "id" not in doc
            for field in ("key", "last_run_at", "records_ingested", "last_action"):
                assert field in doc, f"missing {field} on data_source_runs[{key}]"
            assert doc["key"] == key
            assert doc["last_action"] == "refresh"
            assert isinstance(doc["records_ingested"], int)


# ---------- valuation memo persistence ----------

class TestMemoPersistence:
    def test_memo_doc_shape(self, admin_session, mongo_db):
        # ensure comps + devs exist
        admin_session.post(f"{BASE_URL}/api/data-sources/nhai/refresh", timeout=60)
        admin_session.post(f"{BASE_URL}/api/data-sources/sub_registrar/refresh", timeout=60)
        r = admin_session.post(f"{BASE_URL}/api/valuation-memo",
                               json={"city": "Mumbai", "size_sqft": 1500.0, "verified_only": False},
                               timeout=120)
        assert r.status_code == 200, r.text[:300]
        # Newest memo for admin
        doc = mongo_db.memos.find_one({"user_email": ADMIN_EMAIL, "city": "Mumbai"},
                                       sort=[("generated_at", -1)])
        assert doc is not None, "memo not persisted"
        assert isinstance(doc["_id"], ObjectId)
        assert "id" not in doc
        for key in ("user_id", "user_email", "city", "size_sqft", "verified_only",
                    "comps_count", "developments_count", "avg_psf", "indicative_value",
                    "filename", "generated_at"):
            assert key in doc, f"missing {key} on memo"
        assert doc["city"] == "Mumbai"
        assert doc["size_sqft"] == 1500.0
        assert doc["filename"].endswith(".pdf")


# ---------- /me strips sensitive fields ----------

class TestMeStripsSensitive:
    def test_me_no_sensitive_fields(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/auth/me", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        for forbidden in ("password_hash", "verification_token", "verification_expires", "_id"):
            assert forbidden not in data, f"/me leaked {forbidden}: {data}"
        # Useful fields present
        for ok_field in ("id", "email", "role"):
            assert ok_field in data
        assert data["email"] == ADMIN_EMAIL
