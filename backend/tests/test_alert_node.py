import pytest
from unittest.mock import patch, AsyncMock
import json
import os
from typing import Dict, Any

from backend.agents.state import AgentState
from backend.agents.nodes import alert_node

@pytest.fixture
def base_state() -> AgentState:
    return {
        "raw_train_data": [],
        "anomalies": [],
        "claude_reasoning": "{}",
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
@patch("backend.agents.nodes.log_agent")
@patch("backend.agents.nodes.twilio_client.send_incident_alert", new_callable=AsyncMock)
@patch.dict(os.environ, {
    "MAINTENANCE_PHONE": "+1111111111",
    "OPERATIONS_PHONE": "+2222222222",
    "STATION_PHONE": "+3333333333",
    "DEMO_PASSENGER_PHONE": "+4444444444"
})
async def test_alert_node_sends_sms_to_departments(mock_send_alert, mock_log_agent, base_state):
    # Setup department tasks
    base_state["department_tasks"] = [
        {"department": "maintenance", "task_description": "Fix tracks", "urgency": "high"},
        {"department": "operations", "task_description": "Reroute trains", "urgency": "medium"},
        {"department": "station_manager", "task_description": "Announce delay", "urgency": "low"}
    ]

    mock_send_alert.side_effect = ["sid_maint", "sid_ops", "sid_station"]

    new_state = await alert_node(base_state)

    assert mock_send_alert.call_count == 3
    assert new_state["sms_alerts_sent"] == ["sid_maint", "sid_ops", "sid_station"]

    # Check that calls were made with correct arguments
    calls = mock_send_alert.call_args_list
    assert calls[0][0][0] == "+1111111111"  # MAINTENANCE_PHONE
    assert "MAINTENANCE" in calls[0][0][1]
    assert calls[1][0][0] == "+2222222222"  # OPERATIONS_PHONE
    assert "OPERATIONS" in calls[1][0][1]
    assert calls[2][0][0] == "+3333333333"  # STATION_PHONE
    assert "STATION_MANAGER" in calls[2][0][1]

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
@patch("backend.agents.nodes.twilio_client.send_incident_alert", new_callable=AsyncMock)
@patch.dict(os.environ, {
    "DEMO_PASSENGER_PHONE": "+4444444444"
})
async def test_alert_node_sends_passenger_sms(mock_send_alert, mock_log_agent, base_state):
    base_state["claude_reasoning"] = json.dumps({"passenger_sms": "Train delayed 30 mins. Sorry for inconvenience."})
    mock_send_alert.return_value = "sid_passenger"

    new_state = await alert_node(base_state)

    assert mock_send_alert.call_count == 1
    assert new_state["sms_alerts_sent"] == ["sid_passenger"]
    calls = mock_send_alert.call_args_list
    assert calls[0][0][0] == "+4444444444"
    assert calls[0][0][1] == "Train delayed 30 mins. Sorry for inconvenience."

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
@patch("backend.agents.nodes.twilio_client.send_incident_alert", new_callable=AsyncMock)
@patch.dict(os.environ, {
    "MAINTENANCE_PHONE": "+1111111111",
    "OPERATIONS_PHONE": "+2222222222",
    "DEMO_PASSENGER_PHONE": "+4444444444"
})
async def test_alert_node_handles_twilio_error(mock_send_alert, mock_log_agent, base_state):
    base_state["department_tasks"] = [
        {"department": "maintenance", "task_description": "Fix tracks", "urgency": "high"},
        {"department": "operations", "task_description": "Reroute trains", "urgency": "medium"}
    ]
    base_state["claude_reasoning"] = json.dumps({"passenger_sms": "Train delayed."})

    # Let the first call (maintenance) fail, and subsequent ones succeed
    mock_send_alert.side_effect = [Exception("Twilio error"), "sid_ops", "sid_passenger"]

    new_state = await alert_node(base_state)

    # Should still try to send 3 SMS (2 departments + 1 passenger)
    assert mock_send_alert.call_count == 3
    # Only 2 successes
    assert new_state["sms_alerts_sent"] == ["sid_ops", "sid_passenger"]

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
@patch("backend.agents.nodes.twilio_client.send_incident_alert", new_callable=AsyncMock)
async def test_alert_node_no_tasks(mock_send_alert, mock_log_agent, base_state):
    base_state["department_tasks"] = []
    base_state["claude_reasoning"] = "{}"

    new_state = await alert_node(base_state)

    assert mock_send_alert.call_count == 0
    assert new_state["sms_alerts_sent"] == []
