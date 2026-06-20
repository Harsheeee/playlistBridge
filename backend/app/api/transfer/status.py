from fastapi import APIRouter, Depends
from celery.result import AsyncResult
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/status/{task_id}")
async def get_transfer_status(
    task_id: str,
    user_id: str = Depends(get_current_user),
):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result if task_result.ready() else None
    }
    return result
