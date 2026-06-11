import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any, List
from backend.agents.state import AgentState, TrainAnomaly
from backend.agents.nodes import (
    detect_node, ingest_node, reason_node, reroute_node, coordination_node, alert_node, report_node, supervisor_node
)
import json

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
@patch("backend.agents.nodes.railways_client.get_multiple_trains", new_callable=AsyncMock)
@patch("backend.agents.nodes.websocket_manager.broadcast", new_callable=AsyncMock)
@patch("backend.agents.nodes.get_cancelled_trains", new_callable=AsyncMock)
async def test_ingest_node_with_data(mock_cancelled, mock_ws, mock_get_trains, base_state):
    mock_get_trains.return_value = [
        {"train_number": "12301", "train_name": "Test Train", "status": "running", "delay_minutes": 5}
    ]
    mock_cancelled.return_value = []

    with patch("backend.services.railways_api.get_mock_rapidapi_train", return_value={}), \
         patch("backend.services.railways_api.parse_rapidapi_train_for_agent", return_value=None):
        new_state = await ingest_node(base_state)

    assert "raw_train_data" in new_state
    assert len(new_state["raw_train_data"]) >= 1

@pytest.mark.asyncio
@patch("backend.agents.nodes.reason_with_ai", new_callable=AsyncMock)
async def test_reason_node_with_anomalies(mock_reason, base_state):
    base_state["anomalies"] = [{"train_number": "123", "delay_minutes": 20}]
    mock_reason.return_value = {
        "incident_title": "Test Title",
        "reroute_plan": "Test Reroute",
        "incident_summary": "Test Summary",
        "situation_summary": "Summary"
    }

    new_state = await reason_node(base_state)
    assert new_state["reroute_plan"] == "Test Reroute"
    assert new_state["incident_report"] == "Test Summary"
    assert new_state["claude_reasoning"] == json.dumps(mock_reason.return_value)

@pytest.mark.asyncio
@patch("backend.agents.nodes.dijkstra_route_discovery")
async def test_reroute_node_success(mock_dijkstra, base_state):
    base_state["anomalies"] = [{"train_number": "123", "current_station": "Station A", "destination": "Station B"}]
    mock_dijkstra.return_value = {"status": "Success", "route": ["Station A", "Station B"], "cost": 10}

    new_state = await reroute_node(base_state)
    assert "Dijkstra routed: Station A -> Station B (ETA 10 mins)" in new_state["reroute_plan"]

@pytest.mark.asyncio
@patch("backend.agents.nodes.db_client.insert_department_tasks", new_callable=AsyncMock)
async def test_coordination_node(mock_insert, base_state):
    base_state["anomalies"] = [{"severity": "high"}]
    base_state["claude_reasoning"] = json.dumps({
        "maintenance_task": "Task M",
        "operations_task": "Task O",
        "station_manager_task": "Task S"
    })

    new_state = await coordination_node(base_state)
    tasks = new_state["department_tasks"]
    assert len(tasks) == 3
    assert tasks[0]["department"] == "maintenance"
    assert tasks[0]["task_description"] == "Task M"
    mock_insert.assert_called_once()

@pytest.mark.asyncio
@patch("backend.agents.nodes.twilio_client.send_incident_alert", new_callable=AsyncMock)
async def test_alert_node(mock_send_sms, base_state):
    base_state["department_tasks"] = [
        {"department": "maintenance", "task_description": "Fix track", "urgency": "high"}
    ]
    mock_send_sms.return_value = "SM123"

    new_state = await alert_node(base_state)
    assert "SM123" in new_state["sms_alerts_sent"]

@pytest.mark.asyncio
@patch("backend.agents.nodes.websocket_manager.broadcast", new_callable=AsyncMock)
@patch("backend.agents.nodes.save_incident_if_not_duplicate", new_callable=AsyncMock)
async def test_report_node(mock_save, mock_ws, base_state):
    base_state["anomalies"] = [{"train_number": "123", "delay_minutes": 20}]
    base_state["claude_reasoning"] = json.dumps({"incident_title": "Test Title"})
    mock_save.return_value = True

    new_state = await report_node(base_state)
    assert "123" in new_state["processed_trains"]
    assert new_state["next_node"] == "END"

@pytest.mark.asyncio
async def test_supervisor_node(base_state):
    # Test transition logic
    base_state["anomalies"] = [{"train_number": "123"}]
    base_state["claude_reasoning"] = "{}"
    new_state = await supervisor_node(base_state)
    assert new_state["next_node"] == "reason_node"

    base_state["claude_reasoning"] = json.dumps({"maintenance_task": "Test"})
    base_state["reroute_plan"] = None
    new_state = await supervisor_node(base_state)
    assert new_state["next_node"] == "reroute_node"

    base_state["reroute_plan"] = "Plan"
    base_state["department_tasks"] = []
    new_state = await supervisor_node(base_state)
    assert new_state["next_node"] == "coordination_node"

    base_state["department_tasks"] = [{"department": "maintenance"}]
    base_state["sms_alerts_sent"] = []
    new_state = await supervisor_node(base_state)
    assert new_state["next_node"] == "alert_node"

    base_state["sms_alerts_sent"] = ["SM123"]
    new_state = await supervisor_node(base_state)
    assert new_state["next_node"] == "report_node"

def create_train(train_number="123", delay_minutes=0, passenger_load="normal", status="running", current_station="Station A") -> Dict[str, Any]:
    return {
        "train_number": train_number,
        "train_name": f"Train {train_number}",
        "delay_minutes": delay_minutes,
        "passenger_load": passenger_load,
        "status": status,
        "current_station": current_station,
        "source": "Source",
        "destination": "Destination"
    }

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
async def test_detect_node_no_anomalies(mock_log, base_state):
    base_state["raw_train_data"] = [create_train()]

    new_state = await detect_node(base_state)

    assert len(new_state["anomalies"]) == 0
    assert new_state["should_continue"] is False

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
async def test_detect_node_delay_rules(mock_log, base_state):
    trains = [
        create_train("1", delay_minutes=15),
        create_train("2", delay_minutes=20),
        create_train("3", delay_minutes=45),
        create_train("4", delay_minutes=90),
        create_train("5", delay_minutes=150)
    ]

    base_state["raw_train_data"] = trains
    new_state = await detect_node(base_state)
    anomalies = new_state["anomalies"]

    assert len(anomalies) == 4
    assert new_state["should_continue"] is True

    mapping = {a["train_number"]: a["severity"] for a in anomalies}
    assert mapping["2"] == "low"
    assert mapping["3"] == "medium"
    assert mapping["4"] == "high"
    assert mapping["5"] == "critical"

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
async def test_detect_node_overcrowding_rule(mock_log, base_state):
    base_state["raw_train_data"] = [create_train("1", passenger_load="overcrowded")]

    new_state = await detect_node(base_state)
    anomalies = new_state["anomalies"]

    assert len(anomalies) == 1
    assert anomalies[0]["anomaly_type"] == "overcrowding"
    assert anomalies[0]["severity"] == "high"
    assert new_state["should_continue"] is True

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
async def test_detect_node_cancellation_rule(mock_log, base_state):
    base_state["raw_train_data"] = [create_train("1", status="cancelled")]

    new_state = await detect_node(base_state)
    anomalies = new_state["anomalies"]

    assert len(anomalies) == 1
    assert anomalies[0]["anomaly_type"] == "cancellation"
    assert anomalies[0]["severity"] == "critical"
    assert anomalies[0]["status"] == "cancelled"
    assert new_state["should_continue"] is True

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
async def test_detect_node_processed_trains_skipped(mock_log, base_state):
    base_state["raw_train_data"] = [
        create_train("1", delay_minutes=100),
        create_train("2", delay_minutes=100)
    ]
    base_state["processed_trains"] = ["1"]

    new_state = await detect_node(base_state)
    anomalies = new_state["anomalies"]

    assert len(anomalies) == 1
    assert anomalies[0]["train_number"] == "2"
    assert new_state["should_continue"] is True
