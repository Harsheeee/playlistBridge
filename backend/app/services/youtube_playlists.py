import httpx
from fastapi import HTTPException

BASE = "https://www.googleapis.com/youtube/v3"

async def get_youtube_playlist_items(access_token: str, playlist_id: str):
    videos = []
    page_token = None

    async with httpx.AsyncClient() as client:
        while True:
            r = await client.get(
                f"{BASE}/playlistItems",
                params={
                    "part": "snippet",
                    "playlistId": playlist_id,
                    "maxResults": 50,
                    "pageToken": page_token,
                },
                headers={
                    "Authorization": f"Bearer {access_token}"
                },
            )

            data = r.json()

            if "error" in data:
                #print("YOUTUBE RESPONSE:", data)
                raise HTTPException(
                    status_code=400,
                    detail=f"YouTube API error: {data['error']['message']}",
                )

            items = data.get("items", [])
            for item in items:
                videos.append(item["snippet"]["title"])

            page_token = data.get("nextPageToken")
            if not page_token:
                break

    return videos
