"""Data source connectors: list, NHAI refresh, Sub-Registrar refresh, CSV upload/template."""
import csv
import io
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile

from core.db import db
from core.audit import record_audit
from core.security import get_current_user
from models import Comp, DataSourceRun, Development

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


DATA_SOURCES = [
    {"key": "nhai", "name": "NHAI / MoRTH Highways",
     "attribution": "data.gov.in · NHAI Awarded Projects · BharatMala Pariyojana",
     "target": "developments", "type": "infrastructure"},
    {"key": "sub_registrar", "name": "Sub-Registrar Transactions",
     "attribution": "Maharashtra IGR · Delhi DORIS",
     "target": "comps", "type": "comps_sold"},
    {"key": "csv_import", "name": "CSV / Excel Bulk Import",
     "attribution": "User-provided proprietary data",
     "target": "comps", "type": "user_upload"},
]

CSV_REQUIRED = ["city", "submarket", "property_type", "transaction_type",
                "size_sqft", "asking_price_inr", "sold_price_inr"]


async def _record_run(key: str, count: int, action: str = "refresh") -> None:
    run = DataSourceRun(
        key=key,
        last_run_at=datetime.now(timezone.utc).isoformat(),
        records_ingested=count,
        last_action=action,
    )
    payload = run.to_mongo()
    payload.pop("_id", None)  # always upsert by `key`, never overwrite Mongo's `_id`
    await db.data_source_runs.update_one({"key": key}, {"$set": payload}, upsert=True)


@router.get("")
async def list_data_sources(user: dict = Depends(get_current_user)):
    runs: dict[str, dict] = {}
    async for d in db.data_source_runs.find({}):
        run = DataSourceRun.from_mongo(d).model_dump(exclude={"id"})
        runs[run["key"]] = run
    return [{**s, "last_run": runs.get(s["key"])} for s in DATA_SOURCES]


@router.post("/nhai/refresh")
async def refresh_nhai(request: Request, user: dict = Depends(get_current_user)):
    from data_sources.nhai_data import NHAI_PROJECTS
    count = 0
    for p in NHAI_PROJECTS:
        dev = Development(
            external_id=p["external_id"],
            name=p["name"],
            type="Highway",
            status=p["status"],
            city=p["city"],
            submarket=p["submarket"],
            lat=p["lat"],
            lng=p["lng"],
            developer="NHAI / MoRTH",
            investment_inr_cr=p["investment_inr_cr"],
            size=p["length_km"],
            completion_year=p["completion_year"],
            description=p["description"],
            source="NHAI / data.gov.in",
        )
        update = dev.to_mongo()
        update.pop("_id", None)
        res = await db.developments.update_one(
            {"external_id": p["external_id"]}, {"$set": update}, upsert=True
        )
        if res.upserted_id or res.modified_count:
            count += 1
    await _record_run("nhai", count)
    await record_audit(
        "data_source_refresh", request=request,
        user_id=user["id"], user_email=user["email"],
        payload={"source": "nhai", "ingested": count},
    )
    return {"ok": True, "ingested": count, "source": "NHAI / data.gov.in"}


@router.post("/sub_registrar/refresh")
async def refresh_sub_registrar(request: Request, user: dict = Depends(get_current_user)):
    from data_sources.registrar_data import SUB_REGISTRAR_RECORDS
    count = 0
    for r in SUB_REGISTRAR_RECORDS:
        psf = round(r["sold_price_inr"] / r["size_sqft"], 0) if r["size_sqft"] else 0
        comp = Comp(
            external_id=r["external_id"],
            city=r["city"],
            submarket=r["submarket"],
            address=r["address"],
            property_type=r["property_type"],
            transaction_type=r["transaction_type"],
            size_sqft=r["size_sqft"],
            building_age_yrs=r["building_age_yrs"],
            asking_price_inr=r["asking_price_inr"],
            sold_price_inr=r["sold_price_inr"],
            price_per_sqft=psf,
            owner=r["owner"],
            transaction_date=r["transaction_date"],
            source=f"Sub-Registrar: {r['source_office']}",
            doc_no=r.get("doc_no"),
        )
        update = comp.to_mongo()
        update.pop("_id", None)
        res = await db.comps.update_one(
            {"external_id": r["external_id"]}, {"$set": update}, upsert=True
        )
        if res.upserted_id or res.modified_count:
            count += 1
    await _record_run("sub_registrar", count)
    await record_audit(
        "data_source_refresh", request=request,
        user_id=user["id"], user_email=user["email"],
        payload={"source": "sub_registrar", "ingested": count},
    )
    return {"ok": True, "ingested": count, "source": "Maharashtra IGR + Delhi DORIS"}


@router.post("/csv/upload")
async def upload_csv_comps(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")
    raw = (await file.read()).decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))
    headers = reader.fieldnames or []
    missing = [c for c in CSV_REQUIRED if c not in headers]
    if missing:
        raise HTTPException(status_code=400,
                            detail=f"Missing required columns: {', '.join(missing)}")

    count = 0
    errors: List[str] = []
    for i, row in enumerate(reader, start=2):
        try:
            size = float(row["size_sqft"] or 0)
            sold = float(row["sold_price_inr"] or 0)
            asking = float(row["asking_price_inr"] or sold)
            comp = Comp(
                city=row["city"].strip(),
                submarket=row["submarket"].strip(),
                address=row.get("address", "").strip(),
                property_type=row["property_type"].strip(),
                transaction_type=row["transaction_type"].strip(),
                size_sqft=size,
                building_age_yrs=int(row.get("building_age_yrs") or 0),
                land_size_acres=float(row["land_size_acres"]) if row.get("land_size_acres") else None,
                asking_price_inr=asking,
                sold_price_inr=sold,
                price_per_sqft=round(sold / size, 0) if size else 0,
                owner=row.get("owner", "Private").strip() or "Private",
                transaction_date=row.get("transaction_date", "").strip(),
                source=f"CSV upload · {file.filename} · by {user['email']}",
            )
            await db.comps.insert_one(comp.to_mongo())
            count += 1
        except (ValueError, KeyError) as e:
            errors.append(f"Row {i}: {e}")

    await _record_run("csv_import", count, action=f"upload:{file.filename}")
    return {"ok": True, "ingested": count, "errors": errors[:10], "filename": file.filename}


@router.get("/csv/template")
async def csv_template(user: dict = Depends(get_current_user)):
    sample = (
        "city,submarket,address,property_type,transaction_type,size_sqft,building_age_yrs,"
        "land_size_acres,asking_price_inr,sold_price_inr,owner,transaction_date\n"
        "Bengaluru,Whitefield,\"Sample Tower, Tower B\",Apartment,Sale,1250,3,,12500000,12000000,Private Owner,2025-08-15\n"
    )
    return Response(content=sample, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=comps_template.csv"})
