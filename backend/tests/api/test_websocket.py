import pytest
from unittest.mock import AsyncMock, patch
from fastapi import WebSocket
from backend.api.websocket import ConnectionManager

@pytest.mark.asyncio
async def test_broadcast_success():
    manager = ConnectionManager()
    ws1 = AsyncMock(spec=WebSocket)
    ws2 = AsyncMock(spec=WebSocket)

    await manager.connect(ws1)
    await manager.connect(ws2)

    assert len(manager.active_connections) == 2

    await manager.broadcast("hello")

    ws1.send_text.assert_called_once_with("hello")
    ws2.send_text.assert_called_once_with("hello")
    assert len(manager.active_connections) == 2

@pytest.mark.asyncio
async def test_broadcast_error_removes_connection():
    manager = ConnectionManager()

    ws_success = AsyncMock(spec=WebSocket)
    ws_fail = AsyncMock(spec=WebSocket)

    # Configure ws_fail to raise an Exception on send_text
    ws_fail.send_text.side_effect = Exception("Failed to send text")

    await manager.connect(ws_success)
    await manager.connect(ws_fail)

    assert len(manager.active_connections) == 2

    with patch("backend.api.websocket.logger") as mock_logger:
        await manager.broadcast("test message")

        ws_success.send_text.assert_called_once_with("test message")
        ws_fail.send_text.assert_called_once_with("test message")

        # Error should be logged
        mock_logger.error.assert_called_once()
        assert "Error broadcasting to client: Failed to send text" in mock_logger.error.call_args[0][0]

    # The failed websocket should be removed, the successful one kept
    assert len(manager.active_connections) == 1
    assert manager.active_connections[0] == ws_success
