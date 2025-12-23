import httpx

BASE_URL = "https://www.googleapis.com/youtube/v3"

async def search_video(access_token: str, query: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/search",
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": 1,
            },
            headers={
                "Authorization": f"Bearer {access_token}"
            },
        )
        data = resp.json()
        return data["items"][0]["id"]["videoId"]
