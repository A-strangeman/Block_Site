import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post(
        "/register",
        json={"email": "newuser@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration fails with duplicate email."""
    email = "duplicate@example.com"
    password = "StrongPass123!"

    # First registration succeeds
    response1 = await client.post(
        "/register",
        json={"email": email, "password": password},
    )
    assert response1.status_code == 200

    # Second registration fails
    response2 = await client.post(
        "/register",
        json={"email": email, "password": password},
    )
    assert response2.status_code == 409
    assert "already registered" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Test registration fails with weak password."""
    response = await client.post(
        "/register",
        json={"email": "user@example.com", "password": "weak"},
    )
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, registered_user):
    """Test successful login."""
    response = await client.post(
        "/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, registered_user):
    """Test login fails with invalid password."""
    response = await client.post(
        "/login",
        json={"email": registered_user["email"], "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login fails for non-existent user."""
    response = await client.post(
        "/login",
        json={"email": "nonexistent@example.com", "password": "SomePass123!"},
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]
