import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from DataBase.models import Base

engine = create_async_engine(os.getenv('DB_URL'), echo=False)
session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
