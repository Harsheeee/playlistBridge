from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.core.database import AsyncSessionLocal
from app.models.oauth_account import OAuthAccount
from app.api.deps import get_current_user
from app.services.oauth_utils import ensure_token_valid

router = APIRouter()

YOUTUBE_BASE = "https://www.googleapis.com/youtube/v3"

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/playlists")
async def get_youtube_playlists(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == int(user_id),
            OAuthAccount.provider == "youtube",
        )
    )
    yt_acc = result.scalar_one_or_none()

    if not yt_acc:
        raise HTTPException(400, "YouTube not connected")

    yt_acc = await ensure_token_valid(db, yt_acc)

    playlists = []
    page_token = None

    async with httpx.AsyncClient() as client:
        while True:
            r = await client.get(
                f"{YOUTUBE_BASE}/playlists",
                params={
                    "part": "snippet,contentDetails",
                    "mine": "true",
                    "maxResults": 50,
                    "pageToken": page_token,
                },
                headers={
                    "Authorization": f"Bearer {yt_acc.access_token}"
                },
            )
            data = r.json()

            if "error" in data:
                print("YOUTUBE RESPONSE:", data)
                raise HTTPException(
                    status_code=400,
                    detail=f"YouTube API error: {data['error']['message']}",
                )

            for item in data["items"]:
                playlists.append({
                    "id": item["id"],
                    "name": item["snippet"]["title"],
                    "count": item["contentDetails"]["itemCount"],
                })

            page_token = data.get("nextPageToken")
            if not page_token:
                break

    return playlists
