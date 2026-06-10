import asyncio
import os
import httpx
import uvicorn
import threading
import time

def run_fastapi():
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=8000, log_level="warning")

async def test_secured_endpoints():
    # Start server in background
    bg_thread = threading.Thread(target=run_fastapi, daemon=True)
    bg_thread.start()

    # Wait for the server to actually start
    for _ in range(20):
        try:
            async with httpx.AsyncClient() as c:
                await c.get("http://127.0.0.1:8000/api/system-status")
            break
        except Exception:
            time.sleep(0.5)

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Test missing API key
        resp1 = await client.post("/api/incidents/123/approve")
        assert resp1.status_code == 403
        print("Missing API key returned 403 for /api/incidents/{id}/approve")

        resp2 = await client.post("/api/dept-tasks/123/resolve")
        assert resp2.status_code == 403
        print("Missing API key returned 403 for /api/dept-tasks/{id}/resolve")

        # Test valid API key
        headers = {"X-API-Key": "railmind-admin-key"}
        resp3 = await client.post("/api/incidents/123/approve", headers=headers)
        assert resp3.status_code in [200, 500]
        print("Valid API key bypassed 403 for /api/incidents/{id}/approve")

        resp4 = await client.post("/api/dept-tasks/123/resolve", headers=headers)
        assert resp4.status_code in [200, 500]
        print("Valid API key bypassed 403 for /api/dept-tasks/{id}/resolve")
        print("Endpoint auth logic successfully verified.")

if __name__ == "__main__":
    asyncio.run(test_secured_endpoints())
