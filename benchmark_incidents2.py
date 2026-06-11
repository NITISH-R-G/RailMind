import asyncio
import time
from datetime import datetime, timedelta
import random

# We'll test our proposed optimized version here to compare

async def main():
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

    # Proposed new behavior
    async def get_incidents_optimized(limit=1000, cutoff=None):
        if cutoff:
            filtered = []
            for inc in incidents:
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
                    pass
            sorted_incidents = sorted(filtered, key=lambda x: x["timestamp"], reverse=True)
            return sorted_incidents[:limit]
        else:
            sorted_incidents = sorted(incidents, key=lambda x: x["timestamp"], reverse=True)
            return sorted_incidents[:limit]

    # simulate the optimized API
    start = time.perf_counter()
    for _ in range(100):
        cutoff = datetime.utcnow() - timedelta(hours=24)
        fetched = await get_incidents_optimized(limit=1000, cutoff=cutoff)

    end = time.perf_counter()
    print(f"Optimized logic took {end - start:.4f} seconds for 100 iterations. Result count: {len(fetched)}")

if __name__ == "__main__":
    asyncio.run(main())
