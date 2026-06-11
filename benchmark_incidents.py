import asyncio
import time
from datetime import datetime, timedelta
import random

# We'll import the necessary parts
from backend.services.db_client import FallbackDB

async def main():
    db = FallbackDB()
    # Force fallback mode to test without MongoDB running if needed, or we can use the MongoDB one.
    # Let's populate the database with a lot of incidents.

    print("Populating DB with 10,000 old incidents and 100 new incidents...")
    incidents = []
    now = datetime.utcnow()

    # Old incidents (older than 24 hours)
    for i in range(10000):
        ts = now - timedelta(hours=24, minutes=random.randint(1, 10000))
        incidents.append({"incident_id": f"old_{i}", "timestamp": ts.isoformat() + "Z"})

    # New incidents
    for i in range(100):
        ts = now - timedelta(hours=1, minutes=random.randint(1, 60))
        incidents.append({"incident_id": f"new_{i}", "timestamp": ts.isoformat() + "Z"})

    # Just mock get_incidents and the API filtering

    # original behavior
    async def get_incidents_original(limit=1000):
        # mock db fetch
        # In real db, this would fetch the most recent 1000
        # Since new are 100, and old are 10000, it would fetch 100 new and 900 old.
        sorted_incidents = sorted(incidents, key=lambda x: x["timestamp"], reverse=True)
        return sorted_incidents[:limit]

    # simulate the API filtering
    start = time.perf_counter()
    for _ in range(100):
        fetched = await get_incidents_original(limit=1000)

        cutoff = datetime.utcnow() - timedelta(hours=24)
        filtered = []
        for inc in fetched:
            ts_str = inc.get("timestamp")
            if not ts_str:
                continue
            try:
                if isinstance(ts_str, datetime):
                    ts = ts_str
                else:
                    ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                if ts.tzinfo is not None:
                    ts = ts.replace(tzinfo=None)
                if ts >= cutoff:
                    filtered.append(inc)
            except Exception:
                filtered.append(inc)

    end = time.perf_counter()
    print(f"Original logic took {end - start:.4f} seconds for 100 iterations. Result count: {len(filtered)}")

if __name__ == "__main__":
    asyncio.run(main())
