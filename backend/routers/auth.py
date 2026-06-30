"""Auth endpoints: register, login, logout, verify-email, resend-verification, me."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Response, Depends
from pydantic import BaseModel, EmailStr, Field

from core.db import db
from core.email_utils import new_verification_token, send_verification_email
from core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, set_auth_cookies,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)
    company: Optional[str] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ResendIn(BaseModel):
    email: EmailStr


@router.post("/register")
async def register(payload: RegisterIn, response: Response):
    email = payload.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    token, expires = new_verification_token()
    doc = {
        "email": email,
        "password_hash": hash_password(payload.password),
        "name": payload.name,
        "company": payload.company,
        "role": "user",
        "email_verified": False,
        "verification_token": token,
        "verification_expires": expires,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(doc)
    await send_verification_email(email, payload.name, token)
    return {
        "ok": True,
        "email": email,
        "email_verified": False,
        "message": "Account created. Please check your email for a verification link.",
    }


@router.post("/login")
async def login(payload: LoginIn, response: Response):
    email = payload.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.get("email_verified", False) and user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before signing in. Check your inbox or request a new link.",
        )
    uid = str(user["_id"])
    set_auth_cookies(response, create_access_token(uid, email), create_refresh_token(uid))
    return {
        "id": uid,
        "email": user["email"],
        "name": user.get("name", ""),
        "company": user.get("company"),
        "role": user.get("role", "user"),
        "email_verified": user.get("email_verified", False),
    }


@router.get("/verify-email")
async def verify_email(token: str):
    user = await db.users.find_one({"verification_token": token})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or already-used verification link.")
    expires = user.get("verification_expires")
    if expires and datetime.fromisoformat(expires) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This verification link has expired. Please request a new one.")
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"email_verified": True},
         "$unset": {"verification_token": "", "verification_expires": ""}},
    )
    return {"ok": True, "email": user["email"]}


@router.post("/resend-verification")
async def resend_verification(payload: ResendIn):
    user = await db.users.find_one({"email": payload.email.lower()})
    # Always respond ok to avoid email enumeration
    if not user or user.get("email_verified"):
        return {"ok": True}
    token, expires = new_verification_token()
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"verification_token": token, "verification_expires": expires}},
    )
    await send_verification_email(user["email"], user.get("name", ""), token)
    return {"ok": True}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"ok": True}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user
