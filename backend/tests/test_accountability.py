import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_add_friend_success(client: AsyncClient, auth_headers: dict):
    """Test successfully adding a friend."""
    response = await client.post(
        "/add-friend",
        json={
            "name": "Bob",
            "email": "bob@example.com",
            "notification_channel": "email",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Bob"
    assert data["email"] == "bob@example.com"
    assert data["notification_channel"] == "email"


@pytest.mark.asyncio
async def test_add_friend_with_phone(client: AsyncClient, auth_headers: dict):
    """Test adding friend with SMS notification channel."""
    response = await client.post(
        "/add-friend",
        json={
            "name": "Carol",
            "phone": "+1234567890",
            "notification_channel": "sms",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+1234567890"
    assert data["notification_channel"] == "sms"


@pytest.mark.asyncio
async def test_add_friend_unauthorized(client: AsyncClient):
    """Test adding friend without auth fails."""
    response = await client.post(
        "/add-friend",
        json={"name": "Bob", "email": "bob@example.com"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_send_approval_success(client: AsyncClient, auth_headers: dict):
    """Test successfully sending an approval request."""
    response = await client.post(
        "/send-approval",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert "token" in data
    assert "expires_at" in data


@pytest.mark.asyncio
async def test_send_approval_unauthorized(client: AsyncClient):
    """Test sending approval without auth fails."""
    response = await client.post(
        "/send-approval",
        json={},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_approve_access_success(
    client: AsyncClient, auth_headers: dict
):
    """Test successfully approving access."""
    # First send an approval request
    send_response = await client.post(
        "/send-approval",
        json={},
        headers=auth_headers,
    )
    approval_token = send_response.json()["token"]

    # Approve it
    response = await client.post(
        "/approve-access",
        json={"token": approval_token, "approver": "bob@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["unlock_minutes"] == 5


@pytest.mark.asyncio
async def test_approve_access_invalid_token(client: AsyncClient):
    """Test approving with invalid token fails."""
    response = await client.post(
        "/approve-access",
        json={"token": "invalid_token_xyz"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_approve_via_link_success(
    client: AsyncClient, auth_headers: dict
):
    """Test approving via link (GET /approve)."""
    # Create an approval request
    send_response = await client.post(
        "/send-approval",
        json={},
        headers=auth_headers,
    )
    approval_token = send_response.json()["token"]

    # Approve via link
    response = await client.get(
        "/approve",
        params={"token": approval_token},
    )
    assert response.status_code == 200
    # Response should be HTML
    assert "Access Approved" in response.text or "approved" in response.text.lower()


@pytest.mark.asyncio
async def test_approve_via_link_invalid_token(client: AsyncClient):
    """Test approving via link with invalid token."""
    response = await client.get(
        "/approve",
        params={"token": "invalid_token_xyz"},
    )
    assert response.status_code == 200
    # Should return error message as HTML
    assert "not found" in response.text.lower() or "invalid" in response.text.lower()
