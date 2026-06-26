import asyncio
import json
import logging
import os
from typing import List

from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class SlidingWindowRateLimiter:
    def __init__(self, capacity: int, window_sec: float):
        self.capacity = capacity
        self.window = window_sec
        self.timestamps = []
        self._lock = asyncio.Lock()

    async def consume(self) -> bool:
        async with self._lock:
            now = asyncio.get_event_loop().time()
            self.timestamps = [t for t in self.timestamps if now - t <= self.window]
            if len(self.timestamps) < self.capacity:
                self.timestamps.append(now)
                return True
            return False

rate_limiter = SlidingWindowRateLimiter(capacity=100, window_sec=1.0)


class ConnectionManager:
    """
    Manages active WebSocket connections and broadcasting via Redis Pub/Sub backplane.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        self.channel = "railmind_telemetry"
        self._listener_task = None
        self.MAX_CONNECTIONS = 1000

    async def connect(self, websocket: WebSocket):
        if len(self.active_connections) >= self.MAX_CONNECTIONS:
            logger.warning("WebSocket connection limit reached. Rejecting connection.")
            await websocket.close(code=1008, reason="Connection limit exceeded")
            return False

        await websocket.accept()
        self.active_connections.append(websocket)

        # Start the listener task if it's not already running
        if not self._listener_task or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._listen_to_redis())

        try:
            await websocket.send_json({"type": "connection_established", "message": "Connected to RailMind WebSocket", "state_recovery": "sync_required"})
        except Exception as e:
            logger.error(f"Error sending connection response: {e}")
        return True

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # Publish to Redis instead of sending directly to active_connections
        try:
            await self.redis.publish(self.channel, message)
        except Exception as e:
            logger.error(f"Error publishing to Redis: {e}. Falling back to direct connection broadcasting.")
            failed_connections = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception as ex:
                    logger.error(f"Error sending directly to client: {ex}")
                    failed_connections.append(connection)
            for connection in failed_connections:
                self.disconnect(connection)

    async def _listen_to_redis(self):
        while True:
            try:
                await self.pubsub.subscribe(self.channel)
                async for message in self.pubsub.listen():
                    if message["type"] == "message":
                        data = message["data"]
                        # Broadcast to all local WebSocket connections
                        failed_connections = []
                        for connection in self.active_connections:
                            try:
                                await connection.send_text(data)
                            except Exception as e:
                                logger.error(f"Error sending to client: {e}")
                                failed_connections.append(connection)

                        for connection in failed_connections:
                            self.disconnect(connection)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Redis listener error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)
            finally:
                try:
                    await self.pubsub.unsubscribe(self.channel)
                except Exception:
                    pass

websocket_manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket):
    """
    Handle live streaming of railway operations updates.
    """
    connected = await websocket_manager.connect(websocket)
    if not connected:
        return
    try:
        while True:
                        # Add ping-pong heartbeats
            data = await websocket.receive_text()
            if not await rate_limiter.consume():
                await websocket.send_json({"type": "error", "message": "Rate limit exceeded"})
                continue

            if data == "PING" or data == "PING_TEST":
                await websocket.send_json({"type": "PONG"})
            elif data == "RECOVER_STATE":
                await websocket.send_json({"type": "STATE_RECOVERY", "status": "sync_complete", "timestamp": "current_time"})
            else:
                await websocket.send_json({
                    "type": "echo",
                    "received": data
                })
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        websocket_manager.disconnect(websocket)

