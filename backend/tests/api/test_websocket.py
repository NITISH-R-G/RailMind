import pytest
from unittest.mock import AsyncMock
from fastapi import WebSocket, WebSocketDisconnect, FastAPI
from fastapi.testclient import TestClient

from backend.api.websocket import ConnectionManager, websocket_endpoint, websocket_manager

@pytest.fixture
def manager():
    return ConnectionManager()

@pytest.mark.asyncio
async def test_connect(manager):
    mock_ws = AsyncMock(spec=WebSocket)
    await manager.connect(mock_ws)

    mock_ws.accept.assert_awaited_once()
    mock_ws.send_json.assert_awaited_once_with({"type": "connection_established", "message": "Connected to RailMind WebSocket"})
    assert mock_ws in manager.active_connections

@pytest.mark.asyncio
async def test_connect_exception(manager, caplog):
    mock_ws = AsyncMock(spec=WebSocket)
    mock_ws.send_json.side_effect = Exception("Test Error")

    await manager.connect(mock_ws)

    mock_ws.accept.assert_awaited_once()
    assert mock_ws in manager.active_connections
    assert "Error sending connection response: Test Error" in caplog.text

def test_disconnect(manager):
    mock_ws = AsyncMock(spec=WebSocket)
    manager.active_connections.append(mock_ws)
    manager.disconnect(mock_ws)
    assert mock_ws not in manager.active_connections

    # Should not raise an exception if removing a websocket not in the list
    manager.disconnect(mock_ws)

@pytest.mark.asyncio
async def test_broadcast(manager):
    mock_ws1 = AsyncMock(spec=WebSocket)
    mock_ws2 = AsyncMock(spec=WebSocket)
    manager.active_connections = [mock_ws1, mock_ws2]

    await manager.broadcast("Test Broadcast")

    mock_ws1.send_text.assert_awaited_once_with("Test Broadcast")
    mock_ws2.send_text.assert_awaited_once_with("Test Broadcast")
    assert len(manager.active_connections) == 2

@pytest.mark.asyncio
async def test_broadcast_with_failure(manager, caplog):
    mock_ws_success = AsyncMock(spec=WebSocket)
    mock_ws_fail = AsyncMock(spec=WebSocket)

    mock_ws_fail.send_text.side_effect = Exception("Broadcast Error")

    manager.active_connections = [mock_ws_success, mock_ws_fail]

    await manager.broadcast("Test Broadcast")

    mock_ws_success.send_text.assert_awaited_once_with("Test Broadcast")
    mock_ws_fail.send_text.assert_awaited_once_with("Test Broadcast")

    # The failed websocket should be disconnected
    assert mock_ws_success in manager.active_connections
    assert mock_ws_fail not in manager.active_connections
    assert "Error broadcasting to client: Broadcast Error" in caplog.text


app = FastAPI()
app.websocket("/ws")(websocket_endpoint)

def test_websocket_endpoint_echo():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connection_established"

        websocket.send_text("Hello World")
        data = websocket.receive_json()
        assert data == {"type": "echo", "received": "Hello World"}

def test_websocket_disconnect_integration():
    client = TestClient(app)
    initial_connections = len(websocket_manager.active_connections)
    with client.websocket_connect("/ws"):
        assert len(websocket_manager.active_connections) == initial_connections + 1
    assert len(websocket_manager.active_connections) == initial_connections

@pytest.mark.asyncio
async def test_websocket_endpoint_exceptions(caplog):
    mock_ws = AsyncMock(spec=WebSocket)
    mock_ws.receive_text.side_effect = Exception("Unknown Error")

    await websocket_endpoint(mock_ws)

    assert "WebSocket connection error: Unknown Error" in caplog.text
    assert mock_ws not in websocket_manager.active_connections

@pytest.mark.asyncio
async def test_websocket_endpoint_disconnect_event():
    mock_ws = AsyncMock(spec=WebSocket)
    # Using code=1000 since WebSocketDisconnect expects a valid disconnect code
    mock_ws.receive_text.side_effect = WebSocketDisconnect(code=1000)

    await websocket_endpoint(mock_ws)

    assert mock_ws not in websocket_manager.active_connections
