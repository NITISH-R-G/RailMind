import pytest
import os
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from backend.services.db_client import FallbackDB

@pytest.fixture
def tmp_fallback_file(tmp_path):
    fallback_path = tmp_path / "fallback_db.json"
    return str(fallback_path)

@pytest.fixture
def mock_db():
    db = MagicMock()
    # Mock collections
    db["incidents"] = AsyncMock()
    db["department_tasks"] = AsyncMock()
    return db

@pytest.fixture
def db_client(tmp_fallback_file, mock_db):
    client = FallbackDB()
    client.client = MagicMock()
    client.db = mock_db
    client.fallback_file = tmp_fallback_file
    client.use_fallback = False
    return client

@pytest.mark.asyncio
async def test_init_fallback_file(db_client, tmp_fallback_file):
    await db_client._init_fallback_file()
    assert os.path.exists(tmp_fallback_file)
    with open(tmp_fallback_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data == {"incidents": [], "department_tasks": []}

@pytest.mark.asyncio
async def test_read_write_fallback(db_client, tmp_fallback_file):
    test_data = {"incidents": [{"id": "1"}], "department_tasks": [{"id": "t1"}]}
    await db_client._write_fallback(test_data)

    assert os.path.exists(tmp_fallback_file)

    read_data = await db_client._read_fallback()
    assert read_data == test_data

@pytest.mark.asyncio
async def test_has_recent_incident_mongodb(db_client):
    db_client.db["incidents"].find_one = AsyncMock(return_value={"_id": "some_id"})
    result = await db_client.has_recent_incident("T123")
    assert result is True
    db_client.db["incidents"].find_one.assert_called_once()

@pytest.mark.asyncio
async def test_has_recent_incident_mongodb_not_found(db_client):
    db_client.db["incidents"].find_one = AsyncMock(return_value=None)
    result = await db_client.has_recent_incident("T123")
    assert result is False

@pytest.mark.asyncio
async def test_has_recent_incident_fallback(db_client):
    from datetime import timezone
    db_client.use_fallback = True
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=1)

    await db_client._write_fallback({
        "incidents": [
            {"train_number": "T123", "timestamp": recent_time.isoformat()}
        ],
        "department_tasks": []
    })

    result = await db_client.has_recent_incident("T123")
    assert result is True

@pytest.mark.asyncio
async def test_has_recent_incident_fallback_old(db_client):
    from datetime import timezone
    db_client.use_fallback = True
    old_time = datetime.now(timezone.utc) - timedelta(minutes=10)

    await db_client._write_fallback({
        "incidents": [
            {"train_number": "T123", "timestamp": old_time.isoformat()}
        ],
        "department_tasks": []
    })

    result = await db_client.has_recent_incident("T123")
    assert result is False

@pytest.mark.asyncio
async def test_insert_incident_mongodb(db_client):
    db_client.db["incidents"].insert_one = AsyncMock()
    incident = {"incident_id": "I123", "train_number": "T123"}
    await db_client.insert_incident(incident)
    args, _ = db_client.db["incidents"].insert_one.call_args
    assert args[0] == incident

@pytest.mark.asyncio
async def test_insert_incident_fallback(db_client):
    db_client.db["incidents"].insert_one = AsyncMock(side_effect=Exception("DB Error"))
    incident = {"incident_id": "I123", "train_number": "T123"}
    await db_client.insert_incident(incident)

    assert db_client.use_fallback is True
    data = await db_client._read_fallback()
    assert len(data["incidents"]) == 1
    assert data["incidents"][0]["incident_id"] == "I123"

@pytest.mark.asyncio
async def test_get_incidents_mongodb(db_client):
    # Setup chain: find().sort().limit() returning a to_list
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[{"_id": "1", "name": "Inc1"}])

    db_client.db["incidents"].find.return_value = mock_cursor

    incidents = await db_client.get_incidents()
    assert len(incidents) == 1
    assert incidents[0]["_id"] == "1"

@pytest.mark.asyncio
async def test_get_incidents_fallback(db_client):
    db_client.use_fallback = True
    await db_client._write_fallback({
        "incidents": [
            {"incident_id": "I1", "timestamp": "2023-01-02"},
            {"incident_id": "I2", "timestamp": "2023-01-01"}
        ],
        "department_tasks": []
    })

    incidents = await db_client.get_incidents()
    assert len(incidents) == 2
    assert incidents[0]["incident_id"] == "I1" # Checks sorting

@pytest.mark.asyncio
async def test_insert_department_tasks_mongodb(db_client):
    db_client.db["department_tasks"].insert_many = AsyncMock()
    tasks = [{"task_id": "T1"}, {"task_id": "T2"}]
    await db_client.insert_department_tasks(tasks)
    db_client.db["department_tasks"].insert_many.assert_called_once_with(tasks)

@pytest.mark.asyncio
async def test_insert_department_tasks_fallback(db_client):
    db_client.use_fallback = True
    tasks = [{"task_id": "T1"}]
    await db_client.insert_department_tasks(tasks)

    data = await db_client._read_fallback()
    assert len(data["department_tasks"]) == 1
    assert data["department_tasks"][0]["task_id"] == "T1"

@pytest.mark.asyncio
async def test_get_pending_department_tasks_mongodb(db_client):
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[{"_id": "1", "status": "pending"}])
    db_client.db["department_tasks"].find.return_value = mock_cursor

    tasks = await db_client.get_pending_department_tasks()
    assert len(tasks) == 1
    assert tasks[0]["_id"] == "1"

@pytest.mark.asyncio
async def test_get_pending_department_tasks_fallback(db_client):
    db_client.use_fallback = True
    await db_client._write_fallback({
        "incidents": [],
        "department_tasks": [
            {"id": "T1", "status": "pending"},
            {"id": "T2", "status": "resolved"}
        ]
    })

    tasks = await db_client.get_pending_department_tasks()
    assert len(tasks) == 1
    assert tasks[0]["id"] == "T1"

@pytest.mark.asyncio
async def test_resolve_department_task_mongodb(db_client):
    mock_result = MagicMock()
    mock_result.modified_count = 1
    db_client.db["department_tasks"].update_many = AsyncMock(return_value=mock_result)

    modified = await db_client.resolve_department_task("T1")
    assert modified == 1

@pytest.mark.asyncio
async def test_resolve_department_task_fallback(db_client):
    db_client.use_fallback = True
    await db_client._write_fallback({
        "incidents": [],
        "department_tasks": [{"id": "T1", "status": "pending"}]
    })

    modified = await db_client.resolve_department_task("T1")
    assert modified == 1

    data = await db_client._read_fallback()
    assert data["department_tasks"][0]["status"] == "resolved"

@pytest.mark.asyncio
async def test_approve_incident_mongodb(db_client):
    mock_result = MagicMock()
    mock_result.modified_count = 1
    db_client.db["incidents"].update_many = AsyncMock(return_value=mock_result)

    modified = await db_client.approve_incident("I1")
    assert modified == 1

@pytest.mark.asyncio
async def test_approve_incident_fallback(db_client):
    db_client.use_fallback = True
    await db_client._write_fallback({
        "incidents": [{"incident_id": "I1", "resolution_status": "pending"}],
        "department_tasks": []
    })

    modified = await db_client.approve_incident("I1")
    assert modified == 1

    data = await db_client._read_fallback()
    assert data["incidents"][0]["resolution_status"] == "approved"
