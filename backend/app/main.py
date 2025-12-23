from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.api.health import router as health_router
from app.api.auth.google import router as google_auth_router
from app.api.users import router as users_router
from app.api.oauth.spotify import router as spotify_router
from app.api.spotify.playlists import router as spotify_playlists_router
from app.api.oauth.youtube import router as youtube_router
from app.api.transfer.spotify_to_youtube import router as transfer_router
from app.api.transfer.youtube_to_spotify import router as yt_spotify_router
from app.api.youtube.playlists import router as youtube_playlists_router







app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    https_only=False,  # set True in production
)

# Support both 127.0.0.1 and localhost during development so cookies work
frontend_origins = {settings.FRONTEND_URL, "http://127.0.0.1:5173", "http://localhost:5173"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(frontend_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(
    google_auth_router,
    prefix="/api/auth/google",
    tags=["auth"],
)
app.include_router(
    users_router,
    prefix="/api/users",
    tags=["users"],
)
app.include_router(
    spotify_router,
    prefix="/api/oauth/spotify",
    tags=["spotify"],
)
app.include_router(spotify_playlists_router, prefix="/api/spotify")

app.include_router(
    youtube_router,
    prefix="/api/oauth/youtube",
    tags=["youtube"],
)

app.include_router(
    transfer_router,
    prefix="/api/transfer",
    tags=["transfer"],
)

app.include_router(
    yt_spotify_router,
    prefix="/api/transfer",
    tags=["transfer"],
)


app.include_router(
    youtube_playlists_router,
    prefix="/api/youtube",
    tags=["youtube"],
)





