import pytest
from unittest.mock import patch, AsyncMock
from backend.agents.nodes import ingest_node
from backend.agents.state import AgentState

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

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent", new_callable=AsyncMock)
@patch("backend.agents.nodes.logger")
@patch("backend.agents.nodes.railways_client.get_multiple_trains", new_callable=AsyncMock)
async def test_ingest_node_error_path(mock_get_multiple_trains, mock_logger, mock_log_agent, base_state):
    # Setup the mock to raise an Exception
    error_message = "Mocked API failure"
    mock_get_multiple_trains.side_effect = Exception(error_message)

    # Copy state to compare later
    initial_state = base_state.copy()

    # Call the node
    result_state = await ingest_node(base_state)

    # Assert that the state is returned as is (unchanged mostly, or at least handles error)
    # The actual implementation of ingest_node just returns state on Exception
    assert result_state == initial_state

    # Verify that the exception was logged via standard logger
    mock_logger.error.assert_called_once()
    assert f"Error in ingest_node: {error_message}" in mock_logger.error.call_args[0][0]

    # Verify that the log_agent recorded the failure
    # log_agent is called twice: once for starting ("Ingesting..."), and once for the error
    assert mock_log_agent.call_count >= 2

    # Get the last call to log_agent (which should be the error log)
    last_log_agent_args = mock_log_agent.call_args[0]
    assert last_log_agent_args[0] == "ingest_node"
    assert f"[RAILMIND] [ERROR] Ingestion failed: {error_message}" in last_log_agent_args[1]
