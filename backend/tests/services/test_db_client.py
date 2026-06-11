import pytest
from unittest.mock import AsyncMock, MagicMock

# We do not use sys.path.append hack; pytest handles paths or we use PYTHONPATH
from backend.services.db_client import FallbackDB

@pytest.mark.asyncio
async def test_insert_incident_fallback():
    # Instantiate our db client
    db_client = FallbackDB()

    # Ensure it starts not in fallback mode
    db_client.use_fallback = False

    # Mock the mongodb collection insert_one to raise an exception
    mock_collection = MagicMock()
    mock_collection.insert_one = AsyncMock(side_effect=Exception("Simulated MongoDB insert failure"))

    # Mock db dict-like access
    db_client.db = {"incidents": mock_collection}

    # Mock the fallback read and write methods
    mock_read = MagicMock(return_value={"incidents": [], "department_tasks": []})
    mock_write = MagicMock()

    db_client._read_fallback = mock_read
    db_client._write_fallback = mock_write

    incident = {"incident_id": "test_123", "data": "val"}

    # Call the method
    await db_client.insert_incident(incident)

    # Verify the behaviors
    assert mock_collection.insert_one.called
    assert db_client.use_fallback is True
    assert mock_read.called
    assert mock_write.called

    # Verify what was written to fallback
    written_data = mock_write.call_args[0][0]
    assert len(written_data["incidents"]) == 1
    assert written_data["incidents"][0]["incident_id"] == "test_123"
    assert written_data["incidents"][0]["_id"] == "test_123"
