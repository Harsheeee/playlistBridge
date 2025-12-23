from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import spotipy
import httpx
from pydantic import BaseModel

from app.core.database import AsyncSessionLocal
from app.models.oauth_account import OAuthAccount
from app.api.deps import get_current_user
from app.services.oauth_utils import ensure_token_valid

router = APIRouter()

YOUTUBE_BASE = "https://www.googleapis.com/youtube/v3"


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_spotify_tracks(access_token: str, playlist_id: str):
    sp = spotipy.Spotify(auth=access_token)
    tracks = []
    results = sp.playlist_items(playlist_id, limit=100)

    while results:
        for item in results["items"]:
            track = item["track"]
            if not track:
                continue
            tracks.append({
                "name": track["name"],
                "artist": track["artists"][0]["name"],
            })
        results = sp.next(results) if results["next"] else None

    return tracks
async def youtube_search(access_token: str, title: str, artist: str):
    queries = [
        f"{title} {artist} official audio",
        f"{title} {artist}",
        f"{title}",
    ]

    async with httpx.AsyncClient() as client:
        for q in queries:
            r = await client.get(
                f"{YOUTUBE_BASE}/search",
                params={
                    "part": "snippet",
                    "q": q,
                    "type": "video",
                    "maxResults": 1,
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )
            data = r.json()
            if data.get("items"):
                return data["items"][0]["id"]["videoId"]

    return None


async def create_youtube_playlist(access_token: str, title: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{YOUTUBE_BASE}/playlists",
            params={"part": "snippet,status"},
            json={
                "snippet": {"title": title},
                "status": {"privacyStatus": "private"},
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return r.json()["id"]

async def add_video_to_playlist(access_token: str, playlist_id: str, video_id: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{YOUTUBE_BASE}/playlistItems",
            params={"part": "snippet"},
            json={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                }
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )

class TransferRequest(BaseModel):
    title: str | None = None


@router.post("/spotify-to-youtube/{playlist_id}")
async def transfer_spotify_to_youtube(
    playlist_id: str,
    payload: TransferRequest | None = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    spotify = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == int(user_id),
            OAuthAccount.provider == "spotify",
        )
    )
    youtube = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == int(user_id),
            OAuthAccount.provider == "youtube",
        )
    )

    spotify_acc = spotify.scalar_one_or_none()
    youtube_acc = youtube.scalar_one_or_none()

    if not spotify_acc or not youtube_acc:
        raise HTTPException(400, "Spotify and YouTube must both be connected")

    spotify_acc = await ensure_token_valid(db, spotify_acc)
    youtube_acc = await ensure_token_valid(db, youtube_acc)

    tracks = await get_spotify_tracks(
        spotify_acc.access_token,
        playlist_id,
    )

    target_title = (payload.title.strip() if payload and payload.title else None) or "Transferred from Spotify"
    yt_playlist_id = await create_youtube_playlist(
        youtube_acc.access_token,
        target_title,
    )

    matched, skipped = 0, 0
    errors = []

    for t in tracks:
        video_id = await youtube_search(
            youtube_acc.access_token,
            t["name"],
            t["artist"],
        )
        if not video_id:
            skipped += 1
            continue

        try:
            await add_video_to_playlist(
                youtube_acc.access_token,
                yt_playlist_id,
                video_id,
            )
            matched += 1
        except Exception as e:
            skipped += 1
            errors.append(str(e))

    return {
        "total": len(tracks),
        "matched": matched,
        "skipped": skipped,
        "youtube_playlist_id": yt_playlist_id,
        "errors": errors[:5],
    }
