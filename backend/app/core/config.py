from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "PlaylistBridge"
    FRONTEND_URL: str = "http://127.0.0.1:5173"
    BACKEND_URL: str = "https://playlistbridge-backend-4wga.onrender.com"

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    SECRET_KEY : str

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str

    YOUTUBE_CLIENT_ID: str
    YOUTUBE_CLIENT_SECRET: str

    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        extra = "forbid"


settings = Settings()
