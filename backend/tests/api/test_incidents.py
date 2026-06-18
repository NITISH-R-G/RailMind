import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from backend.api.main import app

@pytest.fixture
def mock_db_client():
    with patch('backend.api.main.db_client') as mock_client:
        yield mock_client

@pytest.mark.asyncio
async def test_get_incidents_api_filter_24h(mock_db_client):
    now = datetime.now(timezone.utc)
    # The API now relies on the DB client to do the filtering, so we mock the DB client
    # to return the filtered results
    mock_db_client.get_incidents = AsyncMock(return_value=[
        {"id": "1", "timestamp": now.isoformat()},
        {"id": "2", "timestamp": (now - timedelta(hours=12)).isoformat()}
    ])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.get("/api/incidents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert [inc["id"] for inc in data] == ["1", "2"]

@pytest.mark.asyncio
async def test_get_incidents_api_all(mock_db_client):
    now = datetime.now(timezone.utc)
    mock_db_client.get_incidents = AsyncMock(return_value=[
        {"id": "1", "timestamp": now.isoformat()},
        {"id": "2", "timestamp": (now - timedelta(hours=12)).isoformat()},
        {"id": "3", "timestamp": (now - timedelta(hours=48)).isoformat()}
    ])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.get("/api/incidents?all=true")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert [inc["id"] for inc in data] == ["1", "2", "3"]

@pytest.mark.asyncio
async def test_get_incidents_api_empty(mock_db_client):
    mock_db_client.get_incidents = AsyncMock(return_value=[])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.get("/api/incidents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

@pytest.mark.asyncio
async def test_get_incidents_api_invalid_timestamp(mock_db_client):
    now = datetime.now(timezone.utc)
    mock_db_client.get_incidents = AsyncMock(return_value=[
        {"id": "1", "timestamp": now.isoformat()},
        {"id": "2", "timestamp": "invalid_timestamp"}
    ])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.get("/api/incidents")

    assert response.status_code == 200
    data = response.json()
    # the endpoint catches exception and returns the item anyway, we assert it does
    assert len(data) == 2
