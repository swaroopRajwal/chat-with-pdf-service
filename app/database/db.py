from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from app.settings import settings


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


engine = create_async_engine(settings.database_url, connect_args={"ssl": True})
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
