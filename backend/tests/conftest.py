import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.session import get_db
from app.main import app
from app.models.base import Base


 

@pytest.fixture(scope="session")
async def test_db_url():
    """Provide a test database URL (in-memory SQLite for speed or test Postgres)."""
    # For local testing, use SQLite in memory
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db(test_db_url: str) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    engine = create_async_engine(test_db_url, echo=False, future=True)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide a test client with overridden DB dependency."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def registered_user(client: AsyncClient):
    """Register and return a test user with token."""
    response = await client.post(
        "/register",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    return {
        "email": "alice@example.com",
        "password": "StrongPass123!",
        "token": data["access_token"],
    }


@pytest.fixture
async def auth_headers(registered_user):
    """Provide Authorization header for authenticated requests."""
    return {"Authorization": f"Bearer {registered_user['token']}"}
