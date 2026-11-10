from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings

DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_size=5,
    max_overflow=10,
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session

async def init_db():
    """Create the cache table if the DB is reachable; skip quietly otherwise.

    Bazaar works fully without a database — it's used only as an optional
    cache. Postgres not being installed should never block the app from
    starting.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        async with engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("CREATE TABLE IF NOT EXISTS ohlcv_data (id SERIAL PRIMARY KEY)"))
    except Exception as exc:
        logger.warning("Database not available, continuing without it: %s", exc)
