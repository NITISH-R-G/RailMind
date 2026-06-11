import pytest
import asyncio
from backend.agents.state import AgentState
from backend.agents.nodes import reason_node, supervisor_node

@pytest.mark.asyncio
async def test_reason_node_recovery(monkeypatch):
    # Mock reason_with_ai to throw an exception
    async def mock_reason_with_ai(anomalies):
        raise Exception("Tool Execution Failed")

    monkeypatch.setattr("backend.agents.nodes.reason_with_ai", mock_reason_with_ai)

    initial_state = {
        "anomalies": [{
            "train_number": "12301",
            "train_name": "Test Train",
            "anomaly_type": "delay",
            "severity": "high",
            "location": "Test Station",
            "delay_minutes": 60,
            "passenger_load": "high",
            "current_station": "Test Station",
            "status": "delayed",
            "source": "A",
            "destination": "B"
        }],
        "claude_reasoning": "",
        "reroute_plan": None,
        "department_tasks": [],
        "sms_alerts_sent": [],
        "incident_report": None,
        "loop_count": 0,
        "should_continue": True,
        "last_api_call": "",
        "railways_latency_ms": 0,
        "ai_latency_ms": 0,
        "processed_trains": [],
        "next_node": None,
        "error_vector": None,
        "raw_train_data": []
    }

    # Run reason node
    result_state = await reason_node(initial_state)

    # Assert it returned an error vector
    assert "error_vector" in result_state
    assert "Reasoning failed: Tool Execution Failed" in result_state["error_vector"]

    # Merge into state for supervisor
    initial_state.update(result_state)

    # Run supervisor node
    supervisor_result = await supervisor_node(initial_state)

    # Assert supervisor routes back to reason_node for self-correction
    assert supervisor_result["next_node"] == "reason_node"
    assert supervisor_result["error_vector"] is None
