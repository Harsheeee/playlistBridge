import time
import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.oauth_account import OAuthAccount


async def refresh_access_token(db: AsyncSession, account: OAuthAccount) -> OAuthAccount:
    """Refresh provider access token using the stored refresh token."""
    if not account.refresh_token:
        raise HTTPException(
            status_code=401,
            detail=f"{account.provider} token expired. Reconnect account.",
        )

    if account.provider == "spotify":
        token_url = "https://accounts.spotify.com/api/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": account.refresh_token,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        }
    elif account.provider == "youtube":
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": account.refresh_token,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
        }
    else:
        raise HTTPException(400, f"Unsupported provider {account.provider}")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            token_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    data = resp.json()
    if resp.status_code != 200 or "access_token" not in data:
        raise HTTPException(
            status_code=401,
            detail=f"Failed to refresh {account.provider} token",
        )

    account.access_token = data["access_token"]
    # Some providers (YouTube) may not return expires_in; default to 1 hour
    expires_in = data.get("expires_in", 3600)
    account.expires_at = int(time.time()) + int(expires_in)
    # Spotify may return a new refresh_token; keep latest
    if data.get("refresh_token"):
        account.refresh_token = data["refresh_token"]

    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def ensure_token_valid(db: AsyncSession, account: OAuthAccount) -> OAuthAccount:
    """Return a valid account, refreshing access token if it is expired."""
    if account.expires_at and account.expires_at < int(time.time()) + 60:
        return await refresh_access_token(db, account)
    return account
