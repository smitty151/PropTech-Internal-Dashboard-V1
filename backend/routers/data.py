"""Read-only data endpoints: markets, developments, comps, reits."""
from typing import Optional

from fastapi import APIRouter, Depends

from core.db import db
from core.email_utils import verified_filter
from core.security import get_current_user

router = APIRouter(tags=["data"])


@router.get("/markets")
async def list_markets():
    return await db.markets.find({}, {"_id": 0}).to_list(100)


@router.get("/developments")
async def list_developments(
    city: Optional[str] = None,
    type: Optional[str] = None,
    verified_only: bool = False,
    user: dict = Depends(get_current_user),
):
    q: dict = {}
    if city and city != "all":
        q["city"] = city
    if type and type != "all":
        q["type"] = type
    if verified_only:
        q.update(verified_filter())
    return await db.developments.find(q, {"_id": 0}).to_list(2000)


@router.get("/developments/stats")
async def developments_stats(user: dict = Depends(get_current_user)):
    total = await db.developments.count_documents({})
    by_type = [
        {"type": d["_id"], "count": d["count"], "value": d["value"]}
        async for d in db.developments.aggregate([
            {"$group": {"_id": "$type", "count": {"$sum": 1}, "value": {"$sum": "$investment_inr_cr"}}}
        ])
    ]
    by_city = [
        {"city": d["_id"], "count": d["count"]}
        async for d in db.developments.aggregate([{"$group": {"_id": "$city", "count": {"$sum": 1}}}])
    ]
    return {"total": total, "by_type": by_type, "by_city": by_city}


@router.get("/comps")
async def list_comps(
    city: Optional[str] = None,
    submarket: Optional[str] = None,
    property_type: Optional[str] = None,
    transaction_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    verified_only: bool = False,
    user: dict = Depends(get_current_user),
):
    q: dict = {}
    if city and city != "all":
        q["city"] = city
    if submarket and submarket != "all":
        q["submarket"] = submarket
    if property_type and property_type != "all":
        q["property_type"] = property_type
    if transaction_type and transaction_type != "all":
        q["transaction_type"] = transaction_type
    if min_price is not None or max_price is not None:
        rng: dict = {}
        if min_price is not None:
            rng["$gte"] = min_price
        if max_price is not None:
            rng["$lte"] = max_price
        q["sold_price_inr"] = rng
    if verified_only:
        q.update(verified_filter())
    return await db.comps.find(q, {"_id": 0}).limit(500).to_list(500)


@router.get("/comps/stats")
async def comps_stats(user: dict = Depends(get_current_user)):
    total = await db.comps.count_documents({})
    sale_total = await db.comps.count_documents({"transaction_type": "Sale"})
    rent_total = await db.comps.count_documents({"transaction_type": "Rent"})
    by_city = [
        {"city": d["_id"], "avg_psf": d["avg_psf"], "count": d["count"]}
        async for d in db.comps.aggregate([
            {"$group": {"_id": "$city", "avg_psf": {"$avg": "$price_per_sqft"}, "count": {"$sum": 1}}}
        ])
    ]
    return {"total": total, "sale": sale_total, "rent": rent_total, "by_city": by_city}


@router.get("/reits")
async def list_reits(user: dict = Depends(get_current_user)):
    return await db.reits.find({}, {"_id": 0}).to_list(100)
