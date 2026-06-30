"""Valuation memo (PDF) + memo history endpoints."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from core.db import db
from core.email_utils import verified_filter
from core.security import get_current_user

router = APIRouter(tags=["memo"])


class MemoIn(BaseModel):
    city: str
    submarket: Optional[str] = None
    property_type: Optional[str] = None
    size_sqft: float
    verified_only: bool = True


@router.post("/valuation-memo")
async def valuation_memo(payload: MemoIn, user: dict = Depends(get_current_user)):
    from valuation_memo import build_valuation_memo
    cq: dict = {"city": payload.city}
    if payload.submarket:
        cq["submarket"] = payload.submarket
    if payload.property_type:
        cq["property_type"] = payload.property_type
    if payload.verified_only:
        cq.update(verified_filter())
    comps = await db.comps.find(cq, {"_id": 0}).limit(200).to_list(200)

    dq: dict = {"city": payload.city}
    if payload.verified_only:
        dq.update(verified_filter())
    developments = await db.developments.find(dq, {"_id": 0}).limit(50).to_list(50)

    pdf = build_valuation_memo(payload.model_dump(), comps, developments, user)
    fname = f"memo_{payload.city.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    psfs = [c["price_per_sqft"] for c in comps if c.get("price_per_sqft")]
    avg_psf = sum(psfs) / len(psfs) if psfs else 0
    await db.memos.insert_one({
        "user_id": user["id"], "user_email": user["email"],
        "city": payload.city, "submarket": payload.submarket,
        "property_type": payload.property_type, "size_sqft": payload.size_sqft,
        "verified_only": payload.verified_only,
        "comps_count": len(comps), "developments_count": len(developments),
        "avg_psf": avg_psf, "indicative_value": avg_psf * payload.size_sqft,
        "filename": fname, "generated_at": datetime.now(timezone.utc).isoformat(),
    })
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={fname}"})


@router.get("/memos")
async def list_memos(user: dict = Depends(get_current_user)):
    return await db.memos.find({"user_id": user["id"]}, {"_id": 0}).sort("generated_at", -1).limit(50).to_list(50)
