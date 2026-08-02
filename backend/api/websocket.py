import asyncio
import json
import logging
import os
from typing import List

from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

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
        # Check global limit using Redis
        current_connections = await self.redis.incr("global_active_connections")
        if current_connections > self.MAX_CONNECTIONS:
            await self.redis.decr("global_active_connections")
            logger.warning("Global WebSocket connection limit reached. Rejecting connection.")
            try:
                await websocket.accept()
                await websocket.close(code=1008, reason="Connection limit exceeded")
            except Exception:
                pass
            return False

        try:
            await websocket.accept()
            self.active_connections.append(websocket)

            # Start the listener task if it's not already running
            if not self._listener_task or self._listener_task.done():
                self._listener_task = asyncio.create_task(self._listen_to_redis())

            await websocket.send_json({"type": "connection_established", "message": "Connected to RailMind WebSocket", "state_recovery": "sync_required"})
            return True
        except Exception as e:
            await self.redis.decr("global_active_connections")
            logger.error(f"Error sending connection response: {e}")
            return False

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            try:
                await self.redis.decr("global_active_connections")
            except Exception as e:
                logger.error(f"Failed to decrement global_active_connections: {e}")

    async def broadcast(self, message: str):
        # Publish to Redis
        try:
            await self.redis.publish(self.channel, message)
        except Exception as e:
            logger.error(f"Error publishing to Redis: {e}")

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
                            await self.disconnect(connection)
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
            data = await websocket.receive_text()
            # Explicit State Recovery
            if data == "SYNC_STATE":
                await websocket.send_json({
                    "type": "state_recovery_ack",
                    "status": "synchronized"
                })
            # Ping-Pong Heartbeat
            elif data == "PING" or data == "PING_TEST":
                await websocket.send_json({"type": "PONG"})
            else:
                try:
                    parsed = json.loads(data)
                    # Support json-based pings/syncs
                    if parsed.get("type") == "SYNC_STATE":
                        await websocket.send_json({
                            "type": "state_recovery_ack",
                            "status": "synchronized"
                        })
                    elif parsed.get("type") == "PING":
                        await websocket.send_json({"type": "PONG"})
                    else:
                        await websocket.send_json({
                            "type": "echo",
                            "received": data
                        })
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "echo",
                        "received": data
                    })
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket_manager.disconnect(websocket)

