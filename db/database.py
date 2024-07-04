from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import models


DB_NAME = "db.sqlite3"


async_engine = create_async_engine(f"sqlite+aiosqlite:///{DB_NAME}", echo=True)
async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def init_models():
    async with async_engine.begin() as conn:
        existing_tables = await conn.run_sync(models.Base.metadata.reflect)
        if not existing_tables:
            await conn.run_sync(models.Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
