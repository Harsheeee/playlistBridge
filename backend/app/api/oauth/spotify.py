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
    name="spotify",
    client_id=settings.SPOTIFY_CLIENT_ID,
    client_secret=settings.SPOTIFY_CLIENT_SECRET,
    authorize_url="https://accounts.spotify.com/authorize",
    access_token_url="https://accounts.spotify.com/api/token",
    client_kwargs={
    "scope": (
        "playlist-read-private "
        "playlist-read-collaborative "
        "playlist-modify-private "
        "playlist-modify-public"
    ),
    }
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/login")
async def spotify_login(request: Request):
    redirect_uri = "http://127.0.0.1:8000/api/oauth/spotify/callback"
    return await oauth.spotify.authorize_redirect(request, redirect_uri, show_dialog=True)

@router.get("/callback")
async def spotify_callback(
    request: Request,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token = await oauth.spotify.authorize_access_token(request)

    expires_at = int(time.time()) + token["expires_in"]

    stmt = select(OAuthAccount).where(
        OAuthAccount.user_id == int(user_id),
        OAuthAccount.provider == "spotify",
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if account:
        account.access_token = token["access_token"]
        account.refresh_token = token["refresh_token"]
        account.expires_at = expires_at
    else:
        account = OAuthAccount(
            user_id=int(user_id),
            provider="spotify",
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            expires_at=expires_at,
        )
        db.add(account)

    await db.commit()
    

    return RedirectResponse(settings.FRONTEND_URL)
