"""Valuation memo (PDF) + memo history endpoints.

/valuation-memo is rate-limited at 5/minute per authenticated user (or IP when anonymous).
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel

from core.db import db
from core.email_utils import verified_filter
from core.rate_limit import limiter, _user_or_ip_key
from core.security import get_current_user
from models import Comp, Development, Memo

router = APIRouter(tags=["memo"])


class MemoIn(BaseModel):
    city: str
    submarket: Optional[str] = None
    property_type: Optional[str] = None
    size_sqft: float
    verified_only: bool = True


@router.post("/valuation-memo")
@limiter.limit("5/minute", key_func=_user_or_ip_key)
async def valuation_memo(request: Request, payload: MemoIn, user: dict = Depends(get_current_user)):
    from valuation_memo import build_valuation_memo
    cq: dict = {"city": payload.city}
    if payload.submarket:
        cq["submarket"] = payload.submarket
    if payload.property_type:
        cq["property_type"] = payload.property_type
    if payload.verified_only:
        cq.update(verified_filter())
    raw_comps = await db.comps.find(cq).limit(200).to_list(200)
    comps = [Comp.from_mongo(c).model_dump(exclude={"id"}) for c in raw_comps]

    dq: dict = {"city": payload.city}
    if payload.verified_only:
        dq.update(verified_filter())
    raw_devs = await db.developments.find(dq).limit(50).to_list(50)
    developments = [Development.from_mongo(d).model_dump(exclude={"id"}) for d in raw_devs]

    pdf = build_valuation_memo(payload.model_dump(), comps, developments, user)
    fname = f"memo_{payload.city.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

    psfs = [c["price_per_sqft"] for c in comps if c.get("price_per_sqft")]
    avg_psf = sum(psfs) / len(psfs) if psfs else 0
    memo = Memo(
        user_id=user["id"],
        user_email=user["email"],
        city=payload.city,
        submarket=payload.submarket,
        property_type=payload.property_type,
        size_sqft=payload.size_sqft,
        verified_only=payload.verified_only,
        comps_count=len(comps),
        developments_count=len(developments),
        avg_psf=avg_psf,
        indicative_value=avg_psf * payload.size_sqft,
        filename=fname,
    )
    await db.memos.insert_one(memo.to_mongo())
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={fname}"})


@router.get("/memos")
async def list_memos(user: dict = Depends(get_current_user)):
    docs = await db.memos.find({"user_id": user["id"]}).sort("generated_at", -1).limit(50).to_list(50)
    return [Memo.from_mongo(d).model_dump(exclude={"id"}) for d in docs]
