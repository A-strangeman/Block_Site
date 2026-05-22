import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_add_blocked_site_success(client: AsyncClient, auth_headers: dict):
    """Test successfully adding a blocked site."""
    response = await client.post(
        "/add-blocked-site",
        json={"domain": "youtube.com"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "youtube.com"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_add_blocked_site_idempotent(
    client: AsyncClient, auth_headers: dict
):
    """Test adding the same blocked site twice returns the same site."""
    # First add
    response1 = await client.post(
        "/add-blocked-site",
        json={"domain": "reddit.com"},
        headers=auth_headers,
    )
    assert response1.status_code == 200
    site1_id = response1.json()["id"]

    # Second add (should be idempotent)
    response2 = await client.post(
        "/add-blocked-site",
        json={"domain": "reddit.com"},
        headers=auth_headers,
    )
    assert response2.status_code == 200
    site2_id = response2.json()["id"]
    assert site1_id == site2_id  # Same site returned


@pytest.mark.asyncio
async def test_add_blocked_site_normalizes_domain(
    client: AsyncClient, auth_headers: dict
):
    """Test that domains are normalized (lowercase, www. removed)."""
    response = await client.post(
        "/add-blocked-site",
        json={"domain": "WWW.YOUTUBE.COM"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["domain"] == "youtube.com"


@pytest.mark.asyncio
async def test_add_blocked_site_unauthorized(client: AsyncClient):
    """Test adding blocked site without auth fails."""
    response = await client.post(
        "/add-blocked-site",
        json={"domain": "youtube.com"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_remove_blocked_site_success(
    client: AsyncClient, auth_headers: dict
):
    """Test successfully removing a blocked site."""
    # Add a site first
    await client.post(
        "/add-blocked-site",
        json={"domain": "facebook.com"},
        headers=auth_headers,
    )

    # Remove it
    response = await client.post(
        "/remove-blocked-site",
        json={"domain": "facebook.com"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "removed"


@pytest.mark.asyncio
async def test_remove_blocked_site_not_found(
    client: AsyncClient, auth_headers: dict
):
    """Test removing non-existent blocked site fails."""
    response = await client.post(
        "/remove-blocked-site",
        json={"domain": "nonexistent.com"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_log_attempt_success(client: AsyncClient, auth_headers: dict):
    """Test successfully logging a block attempt."""
    response = await client.post(
        "/log-attempt",
        json={
            "domain": "youtube.com",
            "url": "https://youtube.com/watch?v=123",
            "tab_id": 42,
            "source": "extension",
            "reason": "blocked",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "logged"


@pytest.mark.asyncio
async def test_log_attempt_normalizes_domain(
    client: AsyncClient, auth_headers: dict
):
    """Test that logged attempt normalizes domain."""
    response = await client.post(
        "/log-attempt",
        json={
            "domain": "WWW.REDDIT.COM",
            "url": "https://reddit.com",
            "source": "extension",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_log_attempt_without_auth(client: AsyncClient):
    """Test logging attempt without auth fails."""
    response = await client.post(
        "/log-attempt",
        json={
            "domain": "youtube.com",
            "url": "https://youtube.com",
            "source": "extension",
        },
    )
    assert response.status_code == 401
