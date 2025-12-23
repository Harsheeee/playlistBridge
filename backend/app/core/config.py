from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "PlaylistBridge"
    FRONTEND_URL: str = "http://127.0.0.1:5173"

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str

    YOUTUBE_CLIENT_ID: str
    YOUTUBE_CLIENT_SECRET: str

    class Config:
        env_file = ".env"
        extra = "forbid"


settings = Settings()
