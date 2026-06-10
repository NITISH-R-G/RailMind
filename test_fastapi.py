import asyncio
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_endpoints():
    # Test missing API key
    resp1 = client.post("/api/incidents/123/approve")
    assert resp1.status_code == 403, f"Expected 403, got {resp1.status_code}"
    print("Missing API key returned 403 for /api/incidents/{id}/approve")

    resp2 = client.post("/api/dept-tasks/123/resolve")
    assert resp2.status_code == 403, f"Expected 403, got {resp2.status_code}"
    print("Missing API key returned 403 for /api/dept-tasks/{id}/resolve")

    # Test valid API key
    headers = {"X-API-Key": "railmind-admin-key"}
    resp3 = client.post("/api/incidents/123/approve", headers=headers)
    assert resp3.status_code in [200, 500], f"Expected 200 or 500, got {resp3.status_code}"
    print("Valid API key bypassed 403 for /api/incidents/{id}/approve")

    resp4 = client.post("/api/dept-tasks/123/resolve", headers=headers)
    assert resp4.status_code in [200, 500], f"Expected 200 or 500, got {resp4.status_code}"
    print("Valid API key bypassed 403 for /api/dept-tasks/{id}/resolve")
    print("Endpoint auth logic successfully verified.")

if __name__ == "__main__":
    test_endpoints()
