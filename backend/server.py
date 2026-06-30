"""Thin FastAPI entrypoint — mounts routers, configures middleware & startup."""
from dotenv import load_dotenv
load_dotenv()

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from core.db import db, client
from core.security import hash_password, verify_password
from models import User
from routers import auth as auth_router
from routers import data as data_router
from routers import memo as memo_router
from routers import calc as calc_router
from routers import sources as sources_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="PlaceHolder PropTech API")

# Single /api umbrella that mounts every router
api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"name": "PlaceHolder API", "status": "ok"}


api_router.include_router(auth_router.router)
api_router.include_router(data_router.router)
api_router.include_router(memo_router.router)
api_router.include_router(calc_router.router)
api_router.include_router(sources_router.router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await db.users.create_index("email", unique=True)
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@placeholder.in")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        admin = User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            name="Admin",
            company="PlaceHolder",
            role="admin",
            email_verified=True,
        )
        await db.users.insert_one(admin.to_mongo())
        logger.info(f"Seeded admin {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password), "email_verified": True}},
        )
    elif not existing.get("email_verified"):
        await db.users.update_one({"email": admin_email}, {"$set": {"email_verified": True}})

    if await db.markets.count_documents({}) == 0:
        from seed_data import seed_all
        await seed_all(db)
        logger.info("Seeded demo PropTech data")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
