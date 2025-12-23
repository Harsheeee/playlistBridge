from fastapi import Cookie, HTTPException
from jose import jwt, JWTError
from app.core.config import settings

def get_current_user(token: str | None = Cookie(default=None, alias="access_token")):

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
