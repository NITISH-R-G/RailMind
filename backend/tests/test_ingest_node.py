import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

from backend.agents.state import AgentState
from backend.agents.nodes import ingest_node

@pytest.fixture
def base_state() -> AgentState:
    return {
        "raw_train_data": [],
        "anomalies": [],
        "claude_reasoning": "",
        "reroute_plan": None,
        "department_tasks": [],
        "sms_alerts_sent": [],
        "incident_report": None,
        "loop_count": 0,
        "should_continue": False,
        "last_api_call": "",
        "railways_latency_ms": 0,
        "ai_latency_ms": 0,
        "processed_trains": []
    }

def create_mock_train(train_number: str) -> Dict[str, Any]:
    return {
        "train_number": train_number,
        "train_name": f"Train {train_number}",
        "delay_minutes": 10,
        "passenger_load": "normal",
        "current_station": "Station A",
        "status": "running",
        "lat": 0.0,
        "lng": 0.0
    }

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
@patch("backend.agents.nodes.railways_client.get_multiple_trains")
@patch("backend.agents.nodes.get_cancelled_trains")
@patch("backend.agents.nodes.websocket_manager.broadcast")
async def test_ingest_node_happy_path(mock_broadcast, mock_get_cancelled, mock_get_multiple, mock_log_agent, base_state):
    # Mock API returning data for all requested trains
    mock_trains = [create_mock_train(str(tn)) for tn in [
        12301, 12951, 12001, 12259, 12565, 11057, 12627, 12625,
        12621, 12615, 12309, 12721, 12229, 12311, 12641
    ]]
    mock_get_multiple.return_value = mock_trains

    mock_get_cancelled.return_value = [{"TrainNo": "99999", "TrainName": "Cancelled Express"}]

    new_state = await ingest_node(base_state)

    # 15 live trains + 1 cancelled train = 16 trains
    assert "raw_train_data" in new_state
    assert len(new_state["raw_train_data"]) == 16

    # Check cancelled train mapping
    cancelled_train = next((t for t in new_state["raw_train_data"] if t["train_number"] == "99999"), None)
    assert cancelled_train is not None
    assert cancelled_train["status"] == "cancelled"
    assert cancelled_train["delay_minutes"] == 999

    # Verify latency metrics were recorded
    assert "railways_latency_ms" in new_state
    assert "last_api_call" in new_state

    # Check websocket broadcast was called for each train
    assert mock_broadcast.call_count == 16

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
@patch("backend.agents.nodes.railways_client.get_multiple_trains")
@patch("backend.agents.nodes.get_cancelled_trains")
@patch("backend.agents.nodes.websocket_manager.broadcast")
async def test_ingest_node_partial_fallback(mock_broadcast, mock_get_cancelled, mock_get_multiple, mock_log_agent, base_state):
    # API only returns 1 train, missing 14
    mock_get_multiple.return_value = [create_mock_train("12301")]

    # Since they are imported as `from ..services.railways_api import ...` inside the loop,
    # we patch them in the `backend.services.railways_api` module
    with patch("backend.services.railways_api.get_mock_rapidapi_train") as mock_get_mock, \
         patch("backend.services.railways_api.parse_rapidapi_train_for_agent") as mock_parse:
        mock_get_mock.return_value = {"dummy": "data"}
        mock_parse.side_effect = lambda data, tn: create_mock_train(tn)

        mock_get_cancelled.return_value = []

        new_state = await ingest_node(base_state)

        # Should still have 15 trains
        assert len(new_state["raw_train_data"]) == 15
        assert mock_get_mock.call_count == 14
        assert mock_parse.call_count == 14

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
@patch("backend.agents.nodes.railways_client.get_multiple_trains")
@patch("backend.agents.nodes.mock_train_data")
@patch("backend.agents.nodes.get_cancelled_trains")
@patch("backend.agents.nodes.websocket_manager.broadcast")
async def test_ingest_node_complete_fallback(mock_broadcast, mock_get_cancelled, mock_mock_data, mock_get_multiple, mock_log_agent, base_state):
    # API returns empty list
    mock_get_multiple.return_value = []

    with patch("backend.services.railways_api.get_mock_rapidapi_train", return_value={}), \
         patch("backend.services.railways_api.parse_rapidapi_train_for_agent", return_value=None):

        mock_mock_data.return_value = [create_mock_train("11111"), create_mock_train("22222")]
        mock_get_cancelled.return_value = []

        new_state = await ingest_node(base_state)

        # It should use mock_train_data()
        assert len(new_state["raw_train_data"]) == 2
        mock_mock_data.assert_called_once()

        # Check that it logged the warning
        warning_logged = any("Railways API returned no data" in str(call) for call in mock_log_agent.mock_calls)
        assert warning_logged

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
@patch("backend.agents.nodes.railways_client.get_multiple_trains")
async def test_ingest_node_exception_handling(mock_get_multiple, mock_log_agent, base_state):
    # API throws exception
    mock_get_multiple.side_effect = Exception("API connection failed")

    new_state = await ingest_node(base_state)

    # State should remain largely unchanged regarding train data (empty)
    assert len(new_state.get("raw_train_data", [])) == 0

    # Exception should be caught and logged
    error_logged = any("[ERROR]" in str(call) for call in mock_log_agent.mock_calls)
    assert error_logged
