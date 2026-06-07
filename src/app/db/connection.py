from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import DATABASE_URL, ADMIN_DATABASE_URL


def _build_async_url(url: str) -> str:
    if url.startswith('postgresql://'):
        return url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    return url

admin_engine = create_engine(ADMIN_DATABASE_URL)
engine = create_engine(DATABASE_URL)
async_engine = create_async_engine(_build_async_url(DATABASE_URL), future=True)


def get_session():
    with Session(engine) as session:
        yield session


async def get_async_session():
    async with AsyncSession(async_engine) as session:
        yield session