import os
import json
from motor.motor_asyncio import AsyncIOMotorClient # type: ignore
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Ensure env variables are loaded from the backend/.env file relative to this script
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

# Real MongoDB Atlas Connection for RailMind
MONGODB_URI = os.getenv("MONGODB_URI")
# Enforce strict database connectivity pooling
client = AsyncIOMotorClient(MONGODB_URI, maxPoolSize=50, minPoolSize=10)
db = client["railmind"]

# Collections needed:
# - db["incidents"] — for incident reports
# - db["department_tasks"] — for dept coordination tasks  
# - db["train_logs"] — for raw train data logs

async def init_db_indexes():
    """Establish geospatial 2dsphere and unique compound indices."""
    try:
        # Create a unique compound index on train_number and timestamp_window (truncated to minute)
        # to ensure idempotent writes and prevent duplicates natively.
        await db.incidents.create_index(
            [("train_number", 1), ("timestamp_window", 1)],
            unique=True
        )

        # Optional: geospatial 2dsphere index if train locations are stored as GeoJSON
        # await db.incidents.create_index([("location", "2dsphere")])
        logger.info("Database indexes initialized successfully.")
    except Exception as e:
        logger.warning(f"Failed to initialize database indexes: {e}")

class FallbackDB:
    def __init__(self):
        self.client = client
        self.db = db
        self.use_fallback = False
        self.fallback_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fallback_db.json")

    def _init_fallback_file(self):
        if not os.path.exists(self.fallback_file):
            try:
                with open(self.fallback_file, "w") as f:
                    json.dump({"incidents": [], "department_tasks": []}, f)
            except Exception as e:
                logger.error(f"Failed to initialize fallback file: {e}")

    def _read_fallback(self):
        self._init_fallback_file()
        try:
            with open(self.fallback_file, "r") as f:
                return json.load(f)
        except Exception:
            return {"incidents": [], "department_tasks": []}

    def _write_fallback(self, data):
        try:
            with open(self.fallback_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to write to fallback database: {e}")

    async def has_recent_incident(self, train_number, minutes=2):
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        if not self.use_fallback:
            try:
                existing = await self.db["incidents"].find_one({
                    "train_number": train_number,
                    "$or": [
                        {"timestamp": {"$gt": cutoff}},
                        {"timestamp": {"$gt": cutoff.isoformat()}}
                    ]
                })
                if existing:
                    return True
            except Exception as e:
                logger.warning(f"MongoDB has_recent_incident failed: {e}. Falling back.")
                self.use_fallback = True

        # Fallback file check
        data = self._read_fallback()
        for inc in data["incidents"]:
            if inc.get("train_number") == train_number:
                ts_str = inc.get("timestamp")
                try:
                    if isinstance(ts_str, datetime):
                        ts = ts_str
                    else:
                        ts = datetime.fromisoformat(str(ts_str))
                    if ts > cutoff:
                        return True
                except Exception as e:
                    logger.warning(f"Failed to parse timestamp '{ts_str}': {e}")
        return False

    async def insert_incident(self, incident):
        if not self.use_fallback:
            try:
                await self.db["incidents"].insert_one(incident.copy())
                return
            except Exception as e:
                logger.warning(f"MongoDB insert_incident failed: {e}. Falling back.")
                self.use_fallback = True
        
        # Fallback
        data = self._read_fallback()
        if "_id" not in incident:
            incident["_id"] = incident.get("incident_id")
        data["incidents"].append(incident)
        self._write_fallback(data)

    async def get_incidents(self, limit=20):
        if not self.use_fallback:
            try:
                cursor = self.db["incidents"].find().sort("timestamp", -1).limit(limit)
                incidents = await cursor.to_list(length=limit)
                for inc in incidents:
                    inc["_id"] = str(inc["_id"])
                return incidents
            except Exception as e:
                logger.warning(f"MongoDB get_incidents failed: {e}. Falling back.")
                self.use_fallback = True
                
        # Fallback
        data = self._read_fallback()
        incidents = data["incidents"]
        try:
            incidents = sorted(incidents, key=lambda x: x.get("timestamp", ""), reverse=True)
        except Exception:
            logger.exception("Failed to sort incidents")
        return incidents[:limit]

    async def insert_department_tasks(self, tasks):
        if not self.use_fallback:
            try:
                await self.db["department_tasks"].insert_many(tasks)
                return
            except Exception as e:
                logger.warning(f"MongoDB insert_department_tasks failed: {e}. Falling back.")
                self.use_fallback = True
                
        # Fallback
        data = self._read_fallback()
        data["department_tasks"].extend(tasks)
        self._write_fallback(data)

    async def get_pending_department_tasks(self):
        if not self.use_fallback:
            try:
                cursor = self.db["department_tasks"].find({"status": "pending"})
                tasks = await cursor.to_list(length=100)
                for t in tasks:
                    t["_id"] = str(t["_id"])
                    t["id"] = t.get("incident_id") or str(t["_id"])
                return tasks
            except Exception as e:
                logger.warning(f"MongoDB get_pending_department_tasks failed: {e}. Falling back.")
                self.use_fallback = True
                
        # Fallback
        data = self._read_fallback()
        pending = []
        for t in data["department_tasks"]:
            if t.get("status") == "pending":
                if "id" not in t:
                    t["id"] = t.get("incident_id") or str(t.get("_id"))
                pending.append(t)
        return pending

    async def resolve_department_task(self, task_id):
        if not self.use_fallback:
            try:
                from bson import ObjectId
                query = {}
                try:
                    query = {"_id": ObjectId(task_id)}
                except Exception:
                    query = {"incident_id": task_id}
                result = await self.db["department_tasks"].update_many(query, {"$set": {"status": "resolved"}})
                return result.modified_count
            except Exception as e:
                logger.warning(f"MongoDB resolve_department_task failed: {e}. Falling back.")
                self.use_fallback = True
                
        # Fallback
        data = self._read_fallback()
        modified_count = 0
        for t in data["department_tasks"]:
            if t.get("incident_id") == task_id or t.get("id") == task_id or str(t.get("_id")) == task_id or t.get("_id") == task_id:
                if t.get("status") != "resolved":
                    t["status"] = "resolved"
                    modified_count += 1
        if modified_count > 0:
            self._write_fallback(data)
        return modified_count

    async def approve_incident(self, incident_id):
        if not self.use_fallback:
            try:
                from bson import ObjectId
                query = {}
                try:
                    query = {"_id": ObjectId(incident_id)}
                except Exception:
                    query = {"incident_id": incident_id}
                result = await self.db["incidents"].update_many(query, {"$set": {"resolution_status": "approved"}})
                return result.modified_count
            except Exception as e:
                logger.warning(f"MongoDB approve_incident failed: {e}. Falling back.")
                self.use_fallback = True

        # Fallback file check
        data = self._read_fallback()
        modified_count = 0
        for inc in data["incidents"]:
            if inc.get("incident_id") == incident_id or str(inc.get("_id")) == incident_id or inc.get("_id") == incident_id:
                if inc.get("resolution_status") != "approved":
                    inc["resolution_status"] = "approved"
                    modified_count += 1
        if modified_count > 0:
            self._write_fallback(data)
        return modified_count

db_client = FallbackDB()
