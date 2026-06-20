import asyncio
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import spotipy
import httpx

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.oauth_account import OAuthAccount
from app.services.oauth_utils import ensure_token_valid
from app.services.youtube_playlists import get_youtube_playlist_items
from app.services.youtube_parse import parse_title, normalize_title

YOUTUBE_BASE = "https://www.googleapis.com/youtube/v3"

async def get_spotify_tracks(access_token: str, playlist_id: str):
    sp = spotipy.Spotify(auth=access_token)
    tracks = []
    results = sp.playlist_items(playlist_id, limit=100)
    while results:
        for item in results["items"]:
            track = item.get("track") or item.get("item")
            if not track:
                continue
            tracks.append({
                "name": track["name"],
                "artist": track["artists"][0]["name"],
            })
        results = sp.next(results) if results["next"] else None
    return tracks

async def youtube_search(access_token: str, title: str, artist: str):
    queries = [f"{title} {artist}"]
    async with httpx.AsyncClient() as client:
        for q in queries:
            r = await client.get(
                f"{YOUTUBE_BASE}/search",
                params={"part": "snippet", "q": q, "type": "video", "maxResults": 5},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            data = r.json()
            items = data.get("items", [])
            if not items:
                continue
            best_id = None
            best_ratio = 0.0
            target_str = f"{title} {artist}".lower()
            for item in items:
                yt_title = item["snippet"]["title"].lower()
                target_words = set(target_str.split())
                yt_words = set(yt_title.split())
                if not target_words:
                    continue
                overlap = len(target_words.intersection(yt_words)) / len(target_words)
                if overlap > best_ratio:
                    best_ratio = overlap
                    best_id = item["id"]["videoId"]
            if best_ratio > 0.5:
                return best_id
            elif items:
                return items[0]["id"]["videoId"]
    return None

async def create_youtube_playlist(access_token: str, title: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{YOUTUBE_BASE}/playlists",
            params={"part": "snippet,status"},
            json={"snippet": {"title": title}, "status": {"privacyStatus": "private"}},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return r.json()["id"]

async def add_video_to_playlist(access_token: str, playlist_id: str, video_id: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{YOUTUBE_BASE}/playlistItems",
            params={"part": "snippet"},
            json={"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}},
            headers={"Authorization": f"Bearer {access_token}"},
        )

async def _transfer_spotify_to_youtube_async(user_id: int, playlist_id: str, target_title: str):
    async with AsyncSessionLocal() as db:
        spotify = await db.execute(select(OAuthAccount).where(OAuthAccount.user_id == user_id, OAuthAccount.provider == "spotify"))
        youtube = await db.execute(select(OAuthAccount).where(OAuthAccount.user_id == user_id, OAuthAccount.provider == "youtube"))
        
        spotify_acc = spotify.scalar_one_or_none()
        youtube_acc = youtube.scalar_one_or_none()
        if not spotify_acc or not youtube_acc:
            return {"error": "Missing connected accounts"}

        spotify_acc = await ensure_token_valid(db, spotify_acc)
        youtube_acc = await ensure_token_valid(db, youtube_acc)

        tracks = await get_spotify_tracks(spotify_acc.access_token, playlist_id)
        yt_playlist_id = await create_youtube_playlist(youtube_acc.access_token, target_title)

        matched, skipped = 0, 0
        errors = []
        for t in tracks:
            video_id = await youtube_search(youtube_acc.access_token, t["name"], t["artist"])
            if not video_id:
                skipped += 1
                continue
            try:
                await add_video_to_playlist(youtube_acc.access_token, yt_playlist_id, video_id)
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

@celery_app.task(bind=True)
def transfer_spotify_to_youtube_task(self, user_id: int, playlist_id: str, target_title: str):
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_transfer_spotify_to_youtube_async(user_id, playlist_id, target_title))

# --- YouTube to Spotify logic ---

def spotify_search(sp: spotipy.Spotify, track: str, artist: str):
    q = f"{track} {artist}"
    res = sp.search(q=q, type="track", limit=10)
    items = res["tracks"]["items"]
    best_uri = None
    best_ratio = 0.0
    for item in items:
        normal_title = normalize_title(item["name"])
        normal_track = normalize_title(track)
        if normal_title == normal_track:
            return item["uri"]
        target_words = set(normal_track.split())
        title_words = set(normal_title.split())
        if not target_words:
            continue
        ratio = len(target_words.intersection(title_words)) / len(target_words)
        if ratio > best_ratio:
            best_ratio = ratio
            best_uri = item["uri"]
    if best_ratio > 0.5:
        return best_uri
    return None

def create_spotify_playlist(access_token: str, user_id: str, name: str):
    sp = spotipy.Spotify(auth=access_token)
    data = {"name": name, "public": False, "collaborative": False, "description": ""}
    playlist = sp._post("me/playlists", payload=data)
    return playlist["id"]

async def _transfer_youtube_to_spotify_async(user_id: int, playlist_id: str, target_title: str):
    async with AsyncSessionLocal() as db:
        yt = await db.execute(select(OAuthAccount).where(OAuthAccount.user_id == user_id, OAuthAccount.provider == "youtube"))
        sp_acc = await db.execute(select(OAuthAccount).where(OAuthAccount.user_id == user_id, OAuthAccount.provider == "spotify"))
        
        yt_acc = yt.scalar_one_or_none()
        spotify_acc = sp_acc.scalar_one_or_none()
        if not yt_acc or not spotify_acc:
            return {"error": "Missing connected accounts"}

        yt_acc = await ensure_token_valid(db, yt_acc)
        spotify_acc = await ensure_token_valid(db, spotify_acc)

        titles = await get_youtube_playlist_items(yt_acc.access_token, playlist_id)
        sp = spotipy.Spotify(auth=spotify_acc.access_token)
        me = sp.me()
        
        playlist_id_sp = create_spotify_playlist(spotify_acc.access_token, me["id"], target_title)

        matched, skipped = 0, 0
        uris = []
        for title in titles:
            metadata = parse_title(title)
            artist = metadata["artist"]
            track = metadata["track"]
            if not track:
                skipped += 1
                continue
            uri = spotify_search(sp, track, artist)
            if uri:
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

@celery_app.task(bind=True)
def transfer_youtube_to_spotify_task(self, user_id: int, playlist_id: str, target_title: str):
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_transfer_youtube_to_spotify_async(user_id, playlist_id, target_title))
