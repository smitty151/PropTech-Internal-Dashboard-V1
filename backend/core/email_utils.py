"""Email helpers (Resend transactional)."""
import asyncio
import logging
import os
import secrets
from datetime import datetime, timezone, timedelta

import resend

logger = logging.getLogger(__name__)


def new_verification_token() -> tuple[str, str]:
    """Returns (token, expires_iso)."""
    return (
        secrets.token_urlsafe(32),
        (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
    )


async def send_verification_email(email: str, name: str, token: str) -> None:
    """Best-effort send. If API key missing, log and continue (dev mode)."""
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        logger.warning(
            f"RESEND_API_KEY not configured — verification link for {email}: "
            f"{os.environ.get('FRONTEND_URL', '')}/verify?token={token}"
        )
        return
    resend.api_key = api_key
    sender = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
    frontend = os.environ.get("FRONTEND_URL", "")
    verify_url = f"{frontend}/verify?token={token}"
    html = f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="font-family:Helvetica,Arial,sans-serif;background:#F7F7F4;padding:32px 0;">
      <tr><td align="center">
        <table width="520" cellpadding="0" cellspacing="0" style="background:#fff;border:1px solid #E5E5E0;">
          <tr><td style="padding:32px;">
            <div style="font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#9CA3AF;">PlaceHolder</div>
            <h1 style="font-size:24px;color:#0A0A0A;margin:12px 0 8px;">Confirm your email</h1>
            <p style="color:#4B5563;font-size:14px;line-height:1.6;">Hi {name}, welcome to PlaceHolder — India's real estate intelligence platform. Click the button below to verify <b>{email}</b> and unlock your dashboard.</p>
            <p style="margin:24px 0;"><a href="{verify_url}" style="background:#0A0A0A;color:#fff;text-decoration:none;padding:12px 22px;font-weight:600;display:inline-block;">Verify email</a></p>
            <p style="color:#9CA3AF;font-size:12px;line-height:1.6;">Or paste this link: <br/><span style="font-family:monospace;color:#4B5563;">{verify_url}</span></p>
            <p style="color:#9CA3AF;font-size:12px;margin-top:24px;">This link expires in 6 hours. If you didn't request this, ignore the email.</p>
          </td></tr>
        </table>
      </td></tr>
    </table>"""
    try:
        await asyncio.to_thread(resend.Emails.send, {
            "from": sender, "to": [email],
            "subject": "Verify your PlaceHolder email", "html": html,
        })
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {e}")


def verified_filter() -> dict:
    """A record is 'verified' when its source string starts with NHAI or Sub-Registrar."""
    return {"source": {"$regex": "^(NHAI|Sub-Registrar)"}}
