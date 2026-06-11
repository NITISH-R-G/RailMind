import asyncio
import os
import uvicorn
from datetime import datetime
from dotenv import load_dotenv

# Ensure env variables are loaded before imports
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ..services.db_client import db_client

from .routes import router
from .websocket import websocket_endpoint, websocket_manager # type: ignore
from ..agents.graph import railmind_graph # type: ignore
from ..agents.state import AgentState # type: ignore
from ..services.railways_api import RailwaysAPIClient

app = FastAPI(
    title="RailMind Operations API",
    description="Autonomous railway operations intelligence agent API",
    version="0.1.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize railways client for fallback train list queries
api_key = os.getenv("RAILWAYS_API_KEY", "mock_key")
railways_client = RailwaysAPIClient(api_key=api_key)

import json
from .websocket import REDIS_URL
import redis.asyncio as aioredis # type: ignore

redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

async def get_latest_agent_state():
    """Fetch latest state from Redis, populated by the ARQ worker."""
    try:
        state_str = await redis_client.get("railmind_agent_state")
        if state_str:
            return json.loads(state_str)
    except Exception as e:
        print(f"Error fetching state from redis: {e}")
    return {}

@app.on_event("startup")
async def startup_event():
    # Test connection on startup and clean collections:
    try:
        from ..services.db_client import client, db, init_db_indexes
        await client.admin.command('ping')
        print("[RAILMIND] MongoDB Atlas connected [OK]")
        
        # Cleanup incidents and tasks
        await db.incidents.delete_many({})
        await db.department_tasks.delete_many({})
        print("[RAILMIND] Cleared MongoDB incidents and tasks collections [OK]")

        # Initialize unique and geospatial indices
        await init_db_indexes()
    except Exception as e:
        print(f"[RAILMIND] MongoDB connection/cleanup failed: {e}")

    # The manual agent loop has been fully decoupled to the ARQ worker.
    pass

# Include general REST routers
app.include_router(router, prefix="/api")

# Mounting direct WebSocket handler
@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket_endpoint(websocket)

# REST Endpoint: GET /api/incidents - Fetch last 20 incidents (last 24h by default, or all=true)
@app.get("/api/incidents")
async def get_incidents_api(all: bool = False):
    try:
        from datetime import datetime, timedelta
        # Fetch up to 1000 incidents
        incidents = await db_client.get_incidents(limit=1000)
        if all:
            return incidents
            
        cutoff = datetime.utcnow() - timedelta(hours=24)
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
                filtered.append(inc)
        return filtered
    except Exception as e:
        print(f"Error fetching incidents: {e}")
        return []

# REST Endpoint: GET /api/trains - Fetch current train statuses
@app.get("/api/trains")
async def get_trains_api():
    state = await get_latest_agent_state()
    trains = state.get("raw_train_data", [])
    if not trains:
        # Fallback to mock data if empty
        return railways_client.mock_train_data()
    return trains

# REST Endpoint: GET /api/dept-tasks - Fetch pending tasks
@app.get("/api/dept-tasks")
async def get_dept_tasks_api():
    try:
        return await db_client.get_pending_department_tasks()
    except Exception as e:
        print(f"Error fetching department tasks: {e}")
        return []

# REST Endpoint: POST /api/dept-tasks/{id}/resolve - Mark task resolved
@app.post("/api/dept-tasks/{id}/resolve")
async def resolve_task_api(id: str):
    try:
        modified_count = await db_client.resolve_department_task(id)
        return {"status": "resolved", "modified_count": modified_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# REST Endpoint: POST /api/incidents/{id}/approve - Approve reroute plan
@app.post("/api/incidents/{id}/approve")
async def approve_incident_api(id: str):
    try:
        modified_count = await db_client.approve_incident(id)
        return {"status": "approved", "modified_count": modified_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# REST Endpoint: GET /api/system-status -> returns all system statuses
@app.get("/api/system-status")
async def get_system_status():
    mongo_status = "Disconnected"
    try:
        from ..services.db_client import client
        await client.admin.command('ping')
        mongo_status = "Connected"
    except Exception as e:
        print(f"Error checking MongoDB status: {e}")
        print(f"Error pinging MongoDB in get_system_status: {e}")
        mongo_status = f"Disconnected ({str(e)})"

    # Railways API
    railways_api_key = os.getenv("RAILWAYS_API_KEY", "")
    rapidapi_key = os.getenv("RAPIDAPI_KEY", "")
    is_railways_connected = (railways_api_key not in ["", "your_railways_api_key_here"]) or (rapidapi_key not in ["", "your_key_here"])
    railways_status = "Connected" if is_railways_connected else "Disconnected"

    # Twilio SMS
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    is_twilio_connected = twilio_sid not in ["", "mock_sid"] and twilio_token not in ["", "mock_token"]
    twilio_status = "Connected" if is_twilio_connected else "Disconnected"

    return {
        "agent_status": "ACTIVE",
        "model": "Gemini 2.0 Flash (primary) / Claude (fallback)",
        "railways_api": railways_status,
        "twilio_sms": twilio_status,
        "mongodb": mongo_status,
        "contacts": {
            "maintenance": os.getenv("MAINTENANCE_PHONE", "+919651058174"),
            "operations": os.getenv("OPERATIONS_PHONE", "+919651058174"),
            "station_manager": os.getenv("STATION_PHONE", "+919651058174")
        }
    }

# REST Endpoint: GET /api/telemetry -> returns timing metrics
@app.get("/api/telemetry")
async def get_telemetry_api():
    incident_count = 0
    task_count = 0
    try:
        from ..services.db_client import db
        incident_count = await db["incidents"].count_documents({})
        task_count = await db["department_tasks"].count_documents({})
    except Exception as e:
        print(f"Error fetching telemetry metrics: {e}")
        print(f"Error fetching telemetry from MongoDB: {e}")

    state = await get_latest_agent_state()
    return {
        "agent_loop_status": "running",
        "last_api_call": state.get("last_api_call", "Never"),
        "railways_latency_ms": state.get("railways_latency_ms", 0),
        "ai_latency_ms": state.get("ai_latency_ms", 0),
        "websocket_clients": len(websocket_manager.active_connections),
        "mongodb_incidents": incident_count,
        "mongodb_tasks": task_count
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
