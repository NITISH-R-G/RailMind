import asyncio
import json
import logging
import os
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import redis.asyncio as aioredis # type: ignore
from redis.asyncio.client import PubSub # type: ignore

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MAX_CONNECTIONS = int(os.getenv("WS_MAX_CONNECTIONS", "1000"))

class ConnectionManager:
    """
    Manages active WebSocket connections and Redis Pub/Sub broadcasting.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.redis: aioredis.Redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        self.pubsub: PubSub = self.redis.pubsub()
        self.pubsub_task: asyncio.Task = None

    async def connect(self, websocket: WebSocket):
        if len(self.active_connections) >= MAX_CONNECTIONS:
            await websocket.close(code=1013, reason="Connection limit reached")
            return False

        await websocket.accept()
        self.active_connections.append(websocket)
        try:
            await websocket.send_json({"type": "connection_established", "message": "Connected to RailMind WebSocket"})
            return True
        except Exception:
            logger.exception("Error sending connection response")
            self.disconnect(websocket)
            return False

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # Instead of directly sending to WS, publish to Redis so all worker instances receive it
        try:
            await self.redis.publish("railmind_telemetry", message)
        except Exception:
            logger.exception("Failed to publish to redis")

    async def start_pubsub_listener(self):
        await self.pubsub.subscribe("railmind_telemetry")
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    failed_connections = []
                    for connection in self.active_connections:
                        try:
                            await connection.send_text(data)
                        except Exception:
                            logger.exception("Error broadcasting to client")
                            failed_connections.append(connection)
                    for connection in failed_connections:
                        self.disconnect(connection)
        except asyncio.CancelledError:
            await self.pubsub.unsubscribe("railmind_telemetry")
        except Exception:
            logger.exception("Pubsub listener error")

websocket_manager = ConnectionManager()

async def ping_pong_task(websocket: WebSocket):
    try:
        while True:
            await asyncio.sleep(30) # Send ping every 30 seconds
            await websocket.send_json({"type": "ping"})
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception("Ping task error")

async def websocket_endpoint(websocket: WebSocket):
    """
    Handle live streaming of railway operations updates with Redis backplane.
    """
    # Start the pubsub listener if it's not already running
    if websocket_manager.pubsub_task is None or websocket_manager.pubsub_task.done():
         websocket_manager.pubsub_task = asyncio.create_task(websocket_manager.start_pubsub_listener())

    connected = await websocket_manager.connect(websocket)
    if not connected:
        return

    ping_task = asyncio.create_task(ping_pong_task(websocket))

    try:
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                if parsed.get("type") == "pong":
                    # Handle heartbeat response
                    continue
            except json.JSONDecodeError:
                pass

            await websocket.send_json({
                "type": "echo",
                "received": data
            })
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception:
        logger.exception("WebSocket connection error")
        websocket_manager.disconnect(websocket)
    finally:
        ping_task.cancel()
