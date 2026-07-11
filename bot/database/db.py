import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.config import config
from bot.database.models import Base

DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)

engine = create_async_engine(config.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db(reset: bool = False):
    if reset:
        db_path = DB_DIR / "bot.db"
        if db_path.exists():
            db_path.unlink()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def reset_database():
    db_path = DB_DIR / "bot.db"
    if db_path.exists():
        db_path.unlink()
    await init_db(reset=False)
