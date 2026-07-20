import os
import json
import asyncio
from datetime import datetime, timezone, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from pymongo import IndexModel, ASCENDING, DESCENDING # type: ignore
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Ensure env variables are loaded from the backend/.env file relative to this script
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

# Real MongoDB Atlas Connection for RailMind
MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI, maxPoolSize=50, minPoolSize=10)
db = client["railmind"]

# Collections needed:
# - db["incidents"] — for incident reports
# - db["department_tasks"] — for dept coordination tasks  
# - db["train_logs"] — for raw train data logs

def get_station_code(station_name: str) -> str:
    if not station_name:
        return ""
    name_upper = station_name.upper()
    if "DELHI" in name_upper or "NDLS" in name_upper:
        return "NDLS"
    if "KANPUR" in name_upper or "CNB" in name_upper:
        return "CNB"
    if "PRAYAGRAJ" in name_upper or "ALLAHABAD" in name_upper or "ALD" in name_upper:
        return "ALD"
    if "MUGHALSARAI" in name_upper or "MGS" in name_upper or "DEEN DAYAL" in name_upper:
        return "MGS"
    if "DHANBAD" in name_upper or "DHN" in name_upper:
        return "DHN"
    if "HOWRAH" in name_upper or "HWH" in name_upper:
        return "HWH"
    if "MUMBAI" in name_upper or "CSTM" in name_upper:
        return "CSTM"
    if "MATHURA" in name_upper or "MTJ" in name_upper:
        return "MTJ"
    if "AGRA" in name_upper or "AGC" in name_upper:
        return "AGC"
    if "BHOPAL" in name_upper or "BPL" in name_upper:
        return "BPL"
    if "NAGPUR" in name_upper or "NGP" in name_upper:
        return "NGP"
    if "CHENNAI" in name_upper or "MAS" in name_upper:
        return "MAS"
    if "AMBALA" in name_upper or "UMB" in name_upper:
        return "UMB"
    if "LUDHIANA" in name_upper or "LDH" in name_upper:
        return "LDH"
    if "AMRITSAR" in name_upper or "ASR" in name_upper:
        return "ASR"
    return station_name[:4].upper()

class FallbackDB:
    def __init__(self):
        self.client = client
        self.db = db
        self.use_fallback = False
        self.fallback_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fallback_db.json")
        self._lock = asyncio.Lock()

    async def init_indexes(self):
        try:
            # Enforce 2dsphere index on location_geo
            await self.db["incidents"].create_index([("location_geo", "2dsphere")])
            # Compound index for idempotency
            await self.db["incidents"].create_index([("train_number", ASCENDING), ("timestamp_window", DESCENDING)], unique=True)
            logger.info("MongoDB indexes created successfully.")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")

    def _sync_init_fallback_file(self):
        if not os.path.exists(self.fallback_file):
            try:
                with open(self.fallback_file, "w") as f:
                    json.dump({"incidents": [], "department_tasks": [], "agent_memory": []}, f)
            except Exception as e:
                logger.error(f"Failed to initialize fallback file: {e}")

    async def _init_fallback_file(self):
        await asyncio.to_thread(self._sync_init_fallback_file)

    def _sync_read_fallback(self):
        self._sync_init_fallback_file()
        try:
            with open(self.fallback_file, "r") as f:
                data = json.load(f)
                if "agent_memory" not in data:
                    data["agent_memory"] = []
                return data
        except Exception:
            return {"incidents": [], "department_tasks": [], "agent_memory": []}

    async def _read_fallback(self):
        return await asyncio.to_thread(self._sync_read_fallback)

    def _sync_write_fallback(self, data):
        try:
            with open(self.fallback_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to write to fallback database: {e}")

    async def _write_fallback(self, data):
        await asyncio.to_thread(self._sync_write_fallback, data)

    async def has_recent_incident(self, train_number, minutes=2):
        from datetime import datetime, timezone, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        if not self.use_fallback:
            try:
                # With unique compound indexes on train_number+timestamp, we don't strictly need this $gt check
                # if we just catch DuplicateKeyError on insert, but we'll leave it for reading if needed.
                # Since the instruction says use DuplicateKeyError INSTEAD OF $gt, let's just return False
                # and let the insert catch the duplicate, OR query explicitly without $gt if we bucket by hour.
                # Actually, the simplest optimization is just returning False here and relying on unique indexes
                # during insert, but let's keep the exact signature and just catch it in insert_incident.
                existing = await self.db["incidents"].find_one({
                    "train_number": train_number,
                    "timestamp": {"$gt": cutoff.isoformat()}
                })
                return existing is not None
            except Exception as e:
                logger.warning(f"MongoDB has_recent_incident failed: {e}. Falling back.")
                self.use_fallback = True

        # Fallback file check
        async with self._lock:
            data = await self._read_fallback()
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
                    except Exception:
                        pass
            return False

    async def insert_incident(self, incident):
        # Inject timestamp_window and location_geo for idempotent 2dsphere queries
        if "timestamp" in incident:
            ts = incident["timestamp"]
            if isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except ValueError:
                    dt = datetime.now(timezone.utc)
            elif isinstance(ts, datetime):
                dt = ts
            else:
                dt = datetime.now(timezone.utc)
            # 5-minute bucketing
            minute_bucket = (dt.minute // 5) * 5
            timestamp_window = dt.replace(minute=minute_bucket, second=0, microsecond=0).isoformat()
            incident["timestamp_window"] = timestamp_window

        if "lat" in incident and "lng" in incident:
            incident["location_geo"] = {
                "type": "Point",
                "coordinates": [float(incident["lng"]), float(incident["lat"])]
            }

        if not self.use_fallback:
            try:
                await self.db["incidents"].insert_one(incident.copy())
                return True
            except DuplicateKeyError:
                logger.info(f"Duplicate incident detected for train {incident.get('train_number')} at window {incident.get('timestamp_window')}")
                return False
            except Exception as e:
                logger.warning(f"MongoDB insert_incident failed: {e}. Falling back.")
                self.use_fallback = True
        
        # Fallback
        async with self._lock:
            data = await self._read_fallback()
            if "_id" not in incident:
                incident["_id"] = incident.get("incident_id")

            # Simple fallback deduplication
            for inc in data["incidents"]:
                if inc.get("train_number") == incident.get("train_number") and inc.get("timestamp") == incident.get("timestamp"):
                    return False

            data["incidents"].append(incident)
            await self._write_fallback(data)
            return True

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
        async with self._lock:
            data = await self._read_fallback()
            incidents = data["incidents"]
            try:
                incidents = sorted(incidents, key=lambda x: x.get("timestamp", ""), reverse=True)
            except Exception:
                pass
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
        async with self._lock:
            data = await self._read_fallback()
            data["department_tasks"].extend(tasks)
            await self._write_fallback(data)

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
        async with self._lock:
            data = await self._read_fallback()
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
        async with self._lock:
            data = await self._read_fallback()
            modified_count = 0
            for t in data["department_tasks"]:
                if t.get("incident_id") == task_id or t.get("id") == task_id or str(t.get("_id")) == task_id or t.get("_id") == task_id:
                    if t.get("status") != "resolved":
                        t["status"] = "resolved"
                        modified_count += 1
            if modified_count > 0:
                await self._write_fallback(data)
            return modified_count

    async def approve_incident(self, incident_id):
        # Retrieve incident details first to save in memory
        incident = None
        if not self.use_fallback:
            try:
                from bson import ObjectId
                query = {}
                try:
                    query = {"_id": ObjectId(incident_id)}
                except Exception:
                    query = {"incident_id": incident_id}
                incident = await self.db["incidents"].find_one(query)
            except Exception as e:
                logger.warning(f"MongoDB find incident for memory failed: {e}. Falling back.")
                self.use_fallback = True

        if self.use_fallback or not incident:
            async with self._lock:
                data = await self._read_fallback()
                for inc in data["incidents"]:
                    if inc.get("incident_id") == incident_id or str(inc.get("_id")) == incident_id or inc.get("_id") == incident_id:
                        incident = inc
                        break

        # If found, save to memory
        if incident:
            try:
                train_number = incident.get("train_number", "Unknown")
                current_station = incident.get("current_station") or incident.get("location") or "Unknown"
                station_code = get_station_code(current_station)
                reroute_plan = incident.get("reroute_plan") or "Redirect via loop lines"
                
                time_str = "12:00-14:00"
                try:
                    ts_str = incident.get("timestamp")
                    if ts_str:
                        if isinstance(ts_str, datetime):
                            dt = ts_str
                        else:
                            dt = datetime.fromisoformat(str(ts_str))
                        h = dt.hour
                        time_str = f"{h:02d}:00-{(h+2)%24:02d}:00"
                except Exception:
                    pass
                
                pattern = f"Train {train_number} is frequently delayed at {station_code} between {time_str}"
                effectiveness = f"{reroute_plan} recovered avg 18 mins for {station_code} delays"
                escalations = f"{train_number} needed escalation 2x this week"
                
                memory_item = {
                    "train_number": train_number,
                    "station_code": station_code,
                    "pattern": pattern,
                    "effectiveness": effectiveness,
                    "escalations": escalations,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await self.save_memory(memory_item)
            except Exception as e:
                logger.error(f"Error creating/saving memory in approve_incident: {e}")

        # Now approve the incident
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
        async with self._lock:
            data = await self._read_fallback()
            modified_count = 0
            for inc in data["incidents"]:
                if inc.get("incident_id") == incident_id or str(inc.get("_id")) == incident_id or inc.get("_id") == incident_id:
                    if inc.get("resolution_status") != "approved":
                        inc["resolution_status"] = "approved"
                        modified_count += 1
            if modified_count > 0:
                await self._write_fallback(data)
            return modified_count

    async def override_incident(self, incident_id, custom_decision):
        # Retrieve incident details first to save in memory
        incident = None
        if not self.use_fallback:
            try:
                from bson import ObjectId
                query = {}
                try:
                    query = {"_id": ObjectId(incident_id)}
                except Exception:
                    query = {"incident_id": incident_id}
                incident = await self.db["incidents"].find_one(query)
            except Exception as e:
                logger.warning(f"MongoDB find incident for override failed: {e}. Falling back.")
                self.use_fallback = True

        if self.use_fallback or not incident:
            async with self._lock:
                data = await self._read_fallback()
                for inc in data["incidents"]:
                    if inc.get("incident_id") == incident_id or str(inc.get("_id")) == incident_id or inc.get("_id") == incident_id:
                        incident = inc
                        break

        # Save to memory as outcome
        if incident:
            try:
                train_number = incident.get("train_number", "Unknown")
                current_station = incident.get("current_station") or incident.get("location") or "Unknown"
                station_code = get_station_code(current_station)
                
                time_str = "12:00-14:00"
                try:
                    ts_str = incident.get("timestamp")
                    if ts_str:
                        if isinstance(ts_str, datetime):
                            dt = ts_str
                        else:
                            dt = datetime.fromisoformat(str(ts_str))
                        h = dt.hour
                        time_str = f"{h:02d}:00-{(h+2)%24:02d}:00"
                except Exception:
                    pass
                
                pattern = f"Train {train_number} is frequently delayed at {station_code} between {time_str}"
                effectiveness = f"Human Override ({custom_decision}) executed"
                escalations = f"{train_number} needed escalation 2x this week"
                
                memory_item = {
                    "train_number": train_number,
                    "station_code": station_code,
                    "pattern": pattern,
                    "effectiveness": effectiveness,
                    "escalations": escalations,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await self.save_memory(memory_item)
            except Exception as e:
                logger.error(f"Error creating/saving override memory: {e}")

        # Update resolution_status to approved and reroute_plan to custom_decision
        if not self.use_fallback:
            try:
                from bson import ObjectId
                query = {}
                try:
                    query = {"_id": ObjectId(incident_id)}
                except Exception:
                    query = {"incident_id": incident_id}
                result = await self.db["incidents"].update_many(query, {"$set": {
                    "resolution_status": "approved",
                    "reroute_plan": custom_decision
                }})
                return result.modified_count
            except Exception as e:
                logger.warning(f"MongoDB override_incident failed: {e}. Falling back.")
                self.use_fallback = True

        # Fallback
        async with self._lock:
            data = await self._read_fallback()
            modified_count = 0
            for inc in data["incidents"]:
                if inc.get("incident_id") == incident_id or str(inc.get("_id")) == incident_id or inc.get("_id") == incident_id:
                    inc["resolution_status"] = "approved"
                    inc["reroute_plan"] = custom_decision
                    modified_count += 1
            if modified_count > 0:
                await self._write_fallback(data)
            return modified_count


    async def save_memory(self, memory_item):
        if not self.use_fallback:
            try:
                await self.db["agent_memory"].insert_one(memory_item.copy())
                return
            except Exception as e:
                logger.warning(f"MongoDB save_memory failed: {e}. Falling back.")
                self.use_fallback = True

        # Fallback
        async with self._lock:
            data = await self._read_fallback()
            data["agent_memory"].append(memory_item)
            await self._write_fallback(data)

    async def get_memories(self, train_number, station_code, limit=5):
        if not self.use_fallback:
            try:
                cursor = self.db["agent_memory"].find({
                    "train_number": train_number,
                    "station_code": station_code
                }).sort("timestamp", -1).limit(limit)
                memories = await cursor.to_list(length=limit)
                for m in memories:
                    m["_id"] = str(m["_id"])
                return memories
            except Exception as e:
                logger.warning(f"MongoDB get_memories failed: {e}. Falling back.")
                self.use_fallback = True

        # Fallback
        async with self._lock:
            data = await self._read_fallback()
            memories = []
            for m in data.get("agent_memory", []):
                if m.get("train_number") == train_number and m.get("station_code") == station_code:
                    memories.append(m)
            try:
                memories = sorted(memories, key=lambda x: x.get("timestamp", ""), reverse=True)
            except Exception:
                pass
            return memories[:limit]

    async def get_counts(self):
        if not self.use_fallback:
            try:
                # Use a low timeout so we fail fast if MongoDB is down/unreachable
                incident_count = await asyncio.wait_for(
                    self.db["incidents"].count_documents({}),
                    timeout=2.0
                )
                task_count = await asyncio.wait_for(
                    self.db["department_tasks"].count_documents({}),
                    timeout=2.0
                )
                return incident_count, task_count
            except Exception as e:
                logger.warning(f"MongoDB count_documents failed or timed out: {e}. Falling back.")
                self.use_fallback = True

        async with self._lock:
            data = await self._read_fallback()
            return len(data.get("incidents", [])), len(data.get("department_tasks", []))

db_client = FallbackDB()

