"""Initialize database with default user and API key."""

import sys
import asyncio
from pathlib import Path
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import AsyncSessionLocal, Base, engine
from app.db.models.user import User
from app.db.models.api_key import APIKey
from app.core.security import hash_api_key, generate_api_key


async def init_db():
    """Initialize database."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if admin user exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "admin"))
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            # Create admin user
            admin_user = User(
                id=uuid4(),
                username="admin",
                email="admin@example.com",
            )
            session.add(admin_user)
            await session.flush()

            # Generate API key
            api_key = generate_api_key()
            api_key_hash = hash_api_key(api_key)

            api_key_obj = APIKey(
                user_id=admin_user.id,
                key_hash=api_key_hash,
                name="Default Admin Key",
                is_active=True,
            )
            session.add(api_key_obj)
            await session.commit()

            print("=" * 60)
            print("Admin user created!")
            print(f"Username: admin")
            print(f"Email: admin@example.com")
            print(f"API Key: {api_key}")
            print("=" * 60)
            print("IMPORTANT: Save this API key securely!")
            print("=" * 60)
        else:
            print("Admin user already exists")


if __name__ == "__main__":
    asyncio.run(init_db())

