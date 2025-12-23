from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings
from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token

router = APIRouter()

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    scope= "openid email profile https://www.googleapis.com/auth/youtube"
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session



@router.get("/login")
async def google_login(request: Request):
    redirect_uri = "http://127.0.0.1:8000/api/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    token = await oauth.google.authorize_access_token(request)
    user_info = token["userinfo"]

    stmt = select(User).where(User.email == user_info["email"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=user_info["email"],
            name=user_info["name"],
            google_id=user_info["sub"],
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    jwt_token = create_access_token({
        "sub": str(user.id),
        "name": user.name,
        "email": user.email,
        "picture": user_info.get("picture"),
    })

    response = RedirectResponse(settings.FRONTEND_URL)
    response.set_cookie(
    key="access_token",
    value=jwt_token,
    httponly=True,
    samesite="lax",
    secure=False,
    path="/",
    )
    return response
