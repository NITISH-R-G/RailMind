import pytest
from unittest.mock import patch
from typing import List, Dict, Any
from backend.agents.state import AgentState, TrainAnomaly
from backend.agents.nodes import detect_node

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


@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
async def test_detect_node_delay_rules(mock_log, base_state):
    # Rule 1: Delay mapping
    # > 15 -> low (16-30)
    # > 30 -> medium (31-60)
    # > 60 -> high (61-120)
    # > 120 -> critical

    trains = [
        create_train("1", delay_minutes=15),   # No anomaly
        create_train("2", delay_minutes=20),   # low
        create_train("3", delay_minutes=45),   # medium
        create_train("4", delay_minutes=90),   # high
        create_train("5", delay_minutes=150)   # critical
    ]

    base_state["raw_train_data"] = trains
    new_state = await detect_node(base_state)
    anomalies = new_state["anomalies"]

    assert len(anomalies) == 4
    assert new_state["should_continue"] is True


    # Verify mapping
    mapping = {a["train_number"]: a["severity"] for a in anomalies}
    assert mapping["2"] == "low"
    assert mapping["3"] == "medium"
    assert mapping["4"] == "high"
    assert mapping["5"] == "critical"

@pytest.mark.asyncio
@patch("backend.agents.nodes.log_agent")
async def test_detect_node_overcrowding_rule(mock_log, base_state):
    # Rule 2: Overcrowded -> high
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
    # Rule 3: Cancelled -> critical
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
    # Ensure processed trains are skipped even if anomalous
    base_state["raw_train_data"] = [
        create_train("1", delay_minutes=100), # Should be skipped
        create_train("2", delay_minutes=100)  # Should trigger anomaly
    ]
    base_state["processed_trains"] = ["1"]

    new_state = await detect_node(base_state)
    anomalies = new_state["anomalies"]

    assert len(anomalies) == 1
    assert anomalies[0]["train_number"] == "2"
    assert new_state["should_continue"] is True
