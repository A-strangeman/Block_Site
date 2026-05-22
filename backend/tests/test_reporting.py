import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_weekly_report_no_attempts(
    client: AsyncClient, auth_headers: dict
):
    """Test weekly report with no block attempts."""
    response = await client.get(
        "/weekly-report",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["attempts"] == 0
    assert data["most_attempted_website"] is None
    assert data["focus_score"] == 100.0
    assert data["unique_domains"] == 0


@pytest.mark.asyncio
async def test_weekly_report_with_attempts(
    client: AsyncClient, auth_headers: dict
):
    """Test weekly report with block attempts."""
    # Log some attempts
    await client.post(
        "/log-attempt",
        json={
            "domain": "youtube.com",
            "url": "https://youtube.com",
            "source": "extension",
        },
        headers=auth_headers,
    )
    await client.post(
        "/log-attempt",
        json={
            "domain": "youtube.com",
            "url": "https://youtube.com/watch?v=123",
            "source": "extension",
        },
        headers=auth_headers,
    )
    await client.post(
        "/log-attempt",
        json={
            "domain": "reddit.com",
            "url": "https://reddit.com",
            "source": "extension",
        },
        headers=auth_headers,
    )

    # Get report
    response = await client.get(
        "/weekly-report",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["attempts"] == 3
    assert data["most_attempted_website"] == "youtube.com"  # 2 attempts
    assert data["unique_domains"] == 2
    # Focus score decreases with attempts (formula: 100 - min(90, attempts * 3))
    assert data["focus_score"] < 100.0


@pytest.mark.asyncio
async def test_weekly_report_focus_score_calculation(
    client: AsyncClient, auth_headers: dict
):
    """Test focus score calculation."""
    # Log 10 attempts
    for i in range(10):
        await client.post(
            "/log-attempt",
            json={
                "domain": f"site{i % 3}.com",
                "url": f"https://site{i % 3}.com",
                "source": "extension",
            },
            headers=auth_headers,
        )

    response = await client.get(
        "/weekly-report",
        headers=auth_headers,
    )
    data = response.json()
    assert data["attempts"] == 10
    # Focus score = 100 - min(90, 10 * 3) = 100 - 90 = 10
    assert data["focus_score"] == 10.0


@pytest.mark.asyncio
async def test_weekly_report_unauthorized(client: AsyncClient):
    """Test weekly report without auth fails."""
    response = await client.get(
        "/weekly-report",
    )
    assert response.status_code == 401
