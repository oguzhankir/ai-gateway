"""Pytest configuration and fixtures."""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.db.models import User, APIKey
from app.core.security import hash_api_key, generate_api_key
from uuid import uuid4


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Create test database session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_user(test_db):
    """Create test user."""
    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
    )
    test_db.add(user)
    await test_db.flush()
    return user


@pytest.fixture
async def test_api_key(test_db, test_user):
    """Create test API key."""
    api_key = generate_api_key()
    api_key_obj = APIKey(
        id=uuid4(),
        user_id=test_user.id,
        key_hash=hash_api_key(api_key),
        name="Test Key",
        is_active=True,
    )
    test_db.add(api_key_obj)
    await test_db.flush()
    return api_key, api_key_obj
