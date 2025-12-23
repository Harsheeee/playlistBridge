from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import spotipy
from app.models.oauth_account import OAuthAccount
from app.core.database import AsyncSessionLocal
from app.api.deps import get_current_user
from app.services.oauth_utils import ensure_token_valid

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/playlists")
async def get_playlists(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(OAuthAccount).where(
        OAuthAccount.user_id == int(user_id),
        OAuthAccount.provider == "spotify",
    )
    result = await db.execute(stmt)
    account = result.scalar_one()

    account = await ensure_token_valid(db, account)

    sp = spotipy.Spotify(auth=account.access_token)
    playlists = sp.current_user_playlists(limit=50)

    return playlists["items"]
