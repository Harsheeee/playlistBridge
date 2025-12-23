from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from jose import jwt, JWTError

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/me")
async def me(
    token: str | None = Cookie(default=None, alias="access_token"),
    db: AsyncSession = Depends(get_db),
):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        
        "picture": payload.get("picture"),
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    return {"detail": "logged out"}
