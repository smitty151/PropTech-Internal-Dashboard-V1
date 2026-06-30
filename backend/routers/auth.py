"""Auth endpoints: register, login, logout, verify-email, resend-verification, me.

Every /auth/* mutating endpoint is rate-limited at 5/minute per IP via slowapi.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel, EmailStr, Field

from core.db import db
from core.email_utils import new_verification_token, send_verification_email
from core.audit import record_audit
from core.rate_limit import limiter
from core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, set_auth_cookies,
    get_current_user,
)
from models import User

router = APIRouter(prefix="/auth", tags=["auth"])

AUTH_LIMIT = "5/minute"


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
@limiter.limit(AUTH_LIMIT)
async def register(request: Request, payload: RegisterIn, response: Response):
    email = payload.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    token, expires = new_verification_token()
    new_user = User(
        email=email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        company=payload.company,
        role="user",
        email_verified=False,
        verification_token=token,
        verification_expires=expires,
    )
    await db.users.insert_one(new_user.to_mongo())
    await send_verification_email(email, payload.name, token)
    await record_audit(
        "verification_email_sent", request=request,
        user_email=email, payload={"reason": "register", "name": payload.name},
    )
    return {
        "ok": True,
        "email": email,
        "email_verified": False,
        "message": "Account created. Please check your email for a verification link.",
    }


@router.post("/login")
@limiter.limit(AUTH_LIMIT)
async def login(request: Request, payload: LoginIn, response: Response):
    email = payload.email.lower()
    raw = await db.users.find_one({"email": email})
    if not raw or not verify_password(payload.password, raw["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user = User.from_mongo(raw)
    if not user.email_verified and user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before signing in. Check your inbox or request a new link.",
        )
    set_auth_cookies(response, create_access_token(user.id, email), create_refresh_token(user.id))
    await record_audit(
        "login", request=request,
        user_id=user.id, user_email=user.email, payload={"role": user.role},
    )
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "company": user.company,
        "role": user.role,
        "email_verified": user.email_verified,
    }


@router.get("/verify-email")
@limiter.limit(AUTH_LIMIT)
async def verify_email(request: Request, token: str):
    raw = await db.users.find_one({"verification_token": token})
    if not raw:
        raise HTTPException(status_code=400, detail="Invalid or already-used verification link.")
    user = User.from_mongo(raw)
    if user.verification_expires and datetime.fromisoformat(user.verification_expires) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This verification link has expired. Please request a new one.")
    await db.users.update_one(
        {"email": user.email},
        {"$set": {"email_verified": True},
         "$unset": {"verification_token": "", "verification_expires": ""}},
    )
    return {"ok": True, "email": user.email}


@router.post("/resend-verification")
@limiter.limit(AUTH_LIMIT)
async def resend_verification(request: Request, payload: ResendIn):
    raw = await db.users.find_one({"email": payload.email.lower()})
    # Always respond ok to avoid email enumeration
    if not raw:
        return {"ok": True}
    user = User.from_mongo(raw)
    if user.email_verified:
        return {"ok": True}
    token, expires = new_verification_token()
    await db.users.update_one(
        {"email": user.email},
        {"$set": {"verification_token": token, "verification_expires": expires}},
    )
    await send_verification_email(user.email, user.name, token)
    await record_audit(
        "verification_email_sent", request=request,
        user_email=user.email, payload={"reason": "resend"},
    )
    return {"ok": True}


@router.post("/logout")
@limiter.limit(AUTH_LIMIT)
async def logout(request: Request, response: Response):
    # Best-effort: capture who logged out (token may be missing / expired).
    user_id, user_email = None, None
    try:
        import jwt as _jwt, os as _os
        tok = request.cookies.get("access_token")
        if tok:
            data = _jwt.decode(tok, _os.environ["JWT_SECRET"], algorithms=["HS256"])
            user_id, user_email = data.get("sub"), data.get("email")
    except Exception:
        pass
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    await record_audit("logout", request=request, user_id=user_id, user_email=user_email)
    return {"ok": True}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user
