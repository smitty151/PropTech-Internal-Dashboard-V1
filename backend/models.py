"""MongoDB document models — PyObjectId + BaseDocument pattern.

All collections (users, memos, developments, comps, reits, data_source_runs, audit_logs)
share a single base that maps Mongo's `_id` <-> `id` (str) and provides
`from_mongo(doc)` for reads and `to_mongo()` for writes.

No router should construct raw dicts for inserts/updates — always go through
the typed models.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def _coerce_objectid(v: Any) -> Any:
    """Accept ObjectId, str, or None and return string form."""
    if v is None or v == "":
        return None
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, str):
        # If it's a valid hex ObjectId, normalise; else keep as-is (we sometimes
        # store user-defined IDs as plain strings).
        return v
    raise TypeError(f"Cannot coerce {type(v)} to ObjectId-string")


PyObjectId = Annotated[Optional[str], BeforeValidator(_coerce_objectid)]


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BaseDocument(BaseModel):
    """All Mongo-backed models inherit this.

    - `id` is the Python attribute; serialises to / loads from Mongo `_id`.
    - `from_mongo(doc)` lifts a raw Mongo dict into a typed model.
    - `to_mongo()` produces a dict ready for insert/update; `_id` is omitted
      when `id` is None so Mongo auto-generates an ObjectId on insert.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="allow",  # tolerate legacy fields in old documents
    )

    id: PyObjectId = Field(default=None, alias="_id")

    @classmethod
    def from_mongo(cls, doc: Optional[dict]):
        if doc is None:
            return None
        # Copy so we don't mutate the caller's dict.
        data = dict(doc)
        if "_id" in data:
            data["id"] = str(data.pop("_id"))
        return cls.model_validate(data)

    def to_mongo(self) -> dict:
        data = self.model_dump(by_alias=False, exclude_none=False)
        if data.get("id"):
            data["_id"] = ObjectId(data["id"]) if ObjectId.is_valid(data["id"]) else data["id"]
        data.pop("id", None)
        return data


# ---------- Collection-specific models ----------

class User(BaseDocument):
    email: str
    password_hash: str
    name: str = ""
    company: Optional[str] = None
    role: str = "user"
    email_verified: bool = False
    verification_token: Optional[str] = None
    verification_expires: Optional[str] = None
    created_at: str = Field(default_factory=utcnow_iso)


class Memo(BaseDocument):
    user_id: str
    user_email: str
    city: str
    submarket: Optional[str] = None
    property_type: Optional[str] = None
    size_sqft: float
    verified_only: bool = True
    comps_count: int = 0
    developments_count: int = 0
    avg_psf: float = 0.0
    indicative_value: float = 0.0
    filename: str
    generated_at: str = Field(default_factory=utcnow_iso)


class Development(BaseDocument):
    external_id: Optional[str] = None
    name: str
    type: str
    status: Optional[str] = None
    city: str
    submarket: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    developer: Optional[str] = None
    investment_inr_cr: Optional[float] = None
    size: Optional[float] = None
    completion_year: Optional[int] = None
    description: Optional[str] = None
    source: str
    ingested_at: str = Field(default_factory=utcnow_iso)


class Comp(BaseDocument):
    external_id: Optional[str] = None
    city: str
    submarket: Optional[str] = None
    address: str = ""
    property_type: str
    transaction_type: str
    size_sqft: float
    building_age_yrs: Optional[int] = None
    land_size_acres: Optional[float] = None
    asking_price_inr: Optional[float] = None
    sold_price_inr: Optional[float] = None
    price_per_sqft: float = 0.0
    owner: str = "Private"
    transaction_date: Optional[str] = None
    source: str
    doc_no: Optional[str] = None
    ingested_at: str = Field(default_factory=utcnow_iso)


class Reit(BaseDocument):
    symbol: str
    name: Optional[str] = None
    dividend_yield: float
    sector: Optional[str] = None


class DataSourceRun(BaseDocument):
    key: str
    last_run_at: str = Field(default_factory=utcnow_iso)
    records_ingested: int = 0
    last_action: str = "refresh"


class AuditLog(BaseDocument):
    """Records user activity for compliance & forensics (Task 4)."""
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str  # e.g. "login", "logout", "memo_generated", "data_source_refresh", "verification_email_sent"
    ip: Optional[str] = None
    payload: dict = Field(default_factory=dict)
    timestamp: str = Field(default_factory=utcnow_iso)
