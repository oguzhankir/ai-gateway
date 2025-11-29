"""Database session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import config_manager, settings

# Create base class for models
Base = declarative_base()

# Create async engine
# Use isolation_level="AUTOCOMMIT" for asyncpg to avoid nested transaction issues
# But actually, we want to manage transactions ourselves, so we use "READ COMMITTED"
engine = create_async_engine(
    settings.database_url,
    pool_size=config_manager.get("database.pool_size", 20),
    max_overflow=config_manager.get("database.max_overflow", 10),
    pool_timeout=config_manager.get("database.pool_timeout", 30),
    echo=config_manager.get("database.echo", False),
    # Ensure we don't have nested transaction issues
    connect_args={"server_settings": {"jit": "off"}},
    # Use future=True for SQLAlchemy 2.0 style
    future=True,
)

# Create async session maker
# Use autocommit=False to avoid nested transaction issues
# Note: autocommit parameter doesn't exist in async_sessionmaker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    Dependency for getting database session.

    Yields:
        Database session
    """
    # Create session without auto-commit
    # Transaction will be managed by the endpoint
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Only commit if no exception occurred
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

