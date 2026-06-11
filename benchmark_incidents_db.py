import asyncio
import time
from datetime import datetime, timedelta
import random

class MockCollection:
    def __init__(self):
        self.data = []
        now = datetime.utcnow()
        for i in range(10000):
            ts = now - timedelta(hours=24, minutes=random.randint(1, 10000))
            self.data.append({"_id": f"old_{i}", "timestamp": ts})
        for i in range(100):
            ts = now - timedelta(hours=1, minutes=random.randint(1, 60))
            self.data.append({"_id": f"new_{i}", "timestamp": ts})

    def find(self, query=None):
        if query and "$or" in query:
            cutoff = query["$or"][0]["timestamp"]["$gte"]
            res = [d for d in self.data if d["timestamp"] >= cutoff]
        else:
            res = list(self.data)
        return MockCursor(res)

class MockCursor:
    def __init__(self, data):
        self.data = data

    def sort(self, key, direction):
        self.data.sort(key=lambda x: x[key], reverse=(direction == -1))
        return self

    def limit(self, l):
        self.data = self.data[:l]
        return self

    async def to_list(self, length):
        return self.data[:length]

class MockDB:
    def __init__(self):
        self.incidents = MockCollection()

    def __getitem__(self, key):
        if key == "incidents":
            return self.incidents

async def benchmark_old(db, iterations=100):
    start = time.perf_counter()
    for _ in range(iterations):
        cursor = db["incidents"].find().sort("timestamp", -1).limit(1000)
        incidents = await cursor.to_list(length=1000)

        cutoff = datetime.utcnow() - timedelta(hours=24)
        filtered = []
        for inc in incidents:
            ts_str = inc.get("timestamp")
            if not ts_str:
                continue
            if isinstance(ts_str, datetime):
                ts = ts_str
            else:
                ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
            if ts.tzinfo is not None:
                ts = ts.replace(tzinfo=None)
            if ts >= cutoff:
                filtered.append(inc)
    end = time.perf_counter()
    return end - start, len(filtered)

async def benchmark_new(db, iterations=100):
    start = time.perf_counter()
    for _ in range(iterations):
        cutoff = datetime.utcnow() - timedelta(hours=24)
        query = {
            "$or": [
                {"timestamp": {"$gte": cutoff}},
                {"timestamp": {"$gte": cutoff.isoformat()}}
            ]
        }
        cursor = db["incidents"].find(query).sort("timestamp", -1).limit(1000)
        incidents = await cursor.to_list(length=1000)
    end = time.perf_counter()
    return end - start, len(incidents)

async def main():
    db = MockDB()
    old_time, old_count = await benchmark_old(db)
    print(f"Old approach: {old_time:.4f} seconds (count: {old_count})")

    new_time, new_count = await benchmark_new(db)
    print(f"New approach: {new_time:.4f} seconds (count: {new_count})")

    if old_time > 0:
        improvement = (old_time - new_time) / old_time * 100
        print(f"Improvement: {improvement:.2f}%")

if __name__ == "__main__":
    asyncio.run(main())
