import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
import os

client = TestClient(app)

def test_approve_incident_no_api_key():
    response = client.post("/api/incidents/test-id/approve")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_approve_incident_invalid_api_key():
    response = client.post("/api/incidents/test-id/approve", headers={"X-API-Key": "wrong_key"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API Key"}

def test_approve_incident_valid_api_key():
    # Since we are mocking db_client, we expect an exception or success
    # but NOT 401 Unauthorized
    response = client.post("/api/incidents/test-id/approve", headers={"X-API-Key": "admin_secret"})
    assert response.status_code != 401

if __name__ == "__main__":
    pytest.main(["-v", "test_auth.py"])

def test_missing_api_key_configuration(monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    response = client.post("/api/incidents/test-id/approve", headers={"X-API-Key": "some_key"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Server configuration error: Authentication is not configured securely."}
