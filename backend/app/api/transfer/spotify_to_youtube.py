from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.tasks.transfer_tasks import transfer_spotify_to_youtube_task

router = APIRouter()

class TransferRequest(BaseModel):
    title: str | None = None

@router.post("/spotify-to-youtube/{playlist_id}")
async def transfer_spotify_to_youtube(
    playlist_id: str,
    payload: TransferRequest | None = None,
    user_id: str = Depends(get_current_user),
):
    target_title = (payload.title.strip() if payload and payload.title else None) or "Transferred from Spotify"
    task = transfer_spotify_to_youtube_task.delay(int(user_id), playlist_id, target_title)
    return {"task_id": task.id, "status": "Processing"}
