import asyncio
from app.core.database import engine
from app.models.user import Base
from app.models.oauth_account import OAuthAccount

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(init())
