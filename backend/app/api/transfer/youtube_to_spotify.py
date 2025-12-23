from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import spotipy

from app.core.database import AsyncSessionLocal
from app.models.oauth_account import OAuthAccount
from app.api.deps import get_current_user
from app.services.youtube_playlists import get_youtube_playlist_items
from app.services.youtube_parse import parse_title, normalize_title
from pydantic import BaseModel
from app.services.oauth_utils import ensure_token_valid

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def spotify_search(sp: spotipy.Spotify, track: str, artist: str):
    q = f"{track} {artist}"
    res = sp.search(q=q, type="track", limit=10)
    items = res["tracks"]["items"]
    for item in items:
        #print(f"Spotify Search Result: '{item['name']}'")
        normal_title = normalize_title(item["name"])
        normal_track = normalize_title(track)
        if normal_title == normal_track:
            return item["uri"]


def create_spotify_playlist(access_token: str, user_id: str, name: str):
    sp = spotipy.Spotify(auth=access_token)
    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=False,
    )
    return playlist["id"]

class TransferRequest(BaseModel):
    title: str | None = None

@router.post("/youtube-to-spotify/{playlist_id}")
async def transfer_youtube_to_spotify(
    playlist_id: str,
    payload: TransferRequest | None = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    yt = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == int(user_id),
            OAuthAccount.provider == "youtube",
        )
    )
    sp_acc = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.user_id == int(user_id),
            OAuthAccount.provider == "spotify",
        )
    )

    yt_acc = yt.scalar_one_or_none()
    spotify_acc = sp_acc.scalar_one_or_none()

    if not yt_acc or not spotify_acc:
        raise HTTPException(400, "Both YouTube and Spotify must be connected")

    yt_acc = await ensure_token_valid(db, yt_acc)
    spotify_acc = await ensure_token_valid(db, spotify_acc)

    titles = await get_youtube_playlist_items(
        yt_acc.access_token,
        playlist_id,
    )

    sp = spotipy.Spotify(auth=spotify_acc.access_token)
    me = sp.me()
    target_title = (payload.title.strip() if payload and payload.title else None) or "Transferred from YouTube"
    playlist_id_sp = create_spotify_playlist(
        spotify_acc.access_token,
        me["id"],
        target_title,
    )

    matched, skipped = 0, 0
    uris = []

    for title in titles:
        metadata = parse_title(title)
        artist = metadata["artist"]
        track = metadata["track"]
        if not track:
            skipped += 1
            continue

        #print(f"Searching for Track: {track}, Artist: {artist}")
        uri = spotify_search(sp, track, artist)
        if uri:
            print(f"Found URI: {uri}")
            uris.append(uri)
            matched += 1
        else:
            skipped += 1

    if uris:
        sp.playlist_add_items(playlist_id_sp, uris)

    return {
        "total": len(titles),
        "matched": matched,
        "skipped": skipped,
        "spotify_playlist_id": playlist_id_sp,
    }
