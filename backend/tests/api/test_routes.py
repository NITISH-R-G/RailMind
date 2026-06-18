import pytest
from httpx import AsyncClient, ASGITransport
from backend.api.main import app
from backend.api.routes import health_check

@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Test the /health endpoint directly via the FastAPI test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "agent": "RailMind"}

@pytest.mark.asyncio
async def test_health_check_function():
    """Test the health_check function logic directly."""
    response = await health_check()
    assert response == {"status": "healthy", "agent": "RailMind"}
