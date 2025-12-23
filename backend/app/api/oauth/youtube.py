from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.oauth_account import OAuthAccount
from app.api.deps import get_current_user
import time

router = APIRouter()

oauth = OAuth()
oauth.register(
    name="youtube",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "https://www.googleapis.com/auth/youtube"
    },
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/login")
async def youtube_login(request: Request):
    redirect_uri = "http://127.0.0.1:8000/api/oauth/youtube/callback"
    return await oauth.youtube.authorize_redirect(request, redirect_uri, prompt="consent", access_type="offline")

@router.get("/callback")
async def youtube_callback(
    request: Request,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token = await oauth.youtube.authorize_access_token(request)
    expires_at = int(time.time()) + token["expires_in"]

    stmt = select(OAuthAccount).where(
        OAuthAccount.user_id == int(user_id),
        OAuthAccount.provider == "youtube",
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if account:
        account.access_token = token["access_token"]
        account.refresh_token = token.get("refresh_token", account.refresh_token)
        account.expires_at = expires_at
    else:
        db.add(OAuthAccount(
            user_id=int(user_id),
            provider="youtube",
            access_token=token["access_token"],
            refresh_token=token.get("refresh_token"),
            expires_at=expires_at,
        ))

    await db.commit()
    return RedirectResponse(settings.FRONTEND_URL)
