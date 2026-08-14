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
        if len(self.active_connections) >= self.MAX_CONNECTIONS:
            logger.warning("WebSocket local limit reached. Rejecting.")
            await websocket.close(code=1008, reason="Connection limit exceeded")
            return False

        # Global horizontal scaling limit using Redis INCR
        global_connections = 0
        try:
            if self.redis is not None:
                global_connections = await self.redis.incr("global_active_connections")
                # Add a TTL so that unclean shutdowns don't leak forever
                await self.redis.expire("global_active_connections", 3600)
        except Exception as e:
            logger.error(f"Redis incr failed: {e}. Bypassing global limit check.")

        if global_connections > 5000:  # arbitrary global limit
            logger.warning("Global WebSocket connection limit reached. Rejecting connection.")
            try:
                if self.redis is not None:
                    await self.redis.decr("global_active_connections")
            except Exception:
                pass
            await websocket.close(code=1008, reason="Global connection limit exceeded")
            return False

        try:
            await websocket.accept()
        except Exception as e:
            logger.error(f"WebSocket accept failed: {e}")
            try:
                if self.redis is not None:
                    await self.redis.decr("global_active_connections")
            except Exception:
                pass
            return False

        self.active_connections.append(websocket)

        # Start the listener task if it's not already running
        if not self._listener_task or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._listen_to_redis())

        try:
            # Explicit state recovery signaling
            await websocket.send_json({"type": "connection_established", "state_recovery": "sync_required"})
        except Exception as e:
            logger.error(f"Error sending connection response: {e}")
            # we do not return False here, connection is established, just sending failed
        return True

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        try:
            if self.redis is not None:
                await self.redis.decr("global_active_connections")
        except Exception as e:
            logger.error(f"Failed to decrement global_active_connections: {e}")

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
                await self.disconnect(connection)

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

            # State recovery parsing
            try:
                json_data = json.loads(data)
                if json_data.get("type") == "SYNC_STATE":
                    await websocket.send_json({"type": "state_recovery_ack"})
                    continue
            except json.JSONDecodeError:
                pass

            # Ping-pong heartbeats
            if data == "PING" or data == "PING_TEST":
                await websocket.send_json({"type": "echo", "received": data})
            else:
                await websocket.send_json({
                    "type": "echo",
                    "received": data
                })
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket_manager.disconnect(websocket)
