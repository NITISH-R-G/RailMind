import pytest
import os
import json
from unittest.mock import patch, MagicMock

# Force DEMO_MODE for testing to bypass DB setup if not available
os.environ["DEMO_MODE"] = "true"

from backend.agents.graph import railmind_graph
from backend.agents.state import AgentState
from backend.services.ai_service import MitigationPlan

@pytest.mark.asyncio
async def test_reason_node_tool_recovery():
    anomalies = [{
        "train_number": "12301",
        "train_name": "Test Train",
        "anomaly_type": "delay",
        "severity": "high",
        "location": "Kanpur",
        "delay_minutes": 100,
        "passenger_load": "high"
    }]

    state: AgentState = {
        "raw_train_data": [],
        "anomalies": anomalies,
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
        "errors": [],
        "next_node": "",
        "last_node_executed": "detect_node",
        "messages": [],
        "tools_used": []
    }

    # Patch create_react_agent to simulate a tool exception
    with patch('langgraph.prebuilt.create_react_agent') as mock_create_agent:
        mock_agent = MagicMock()
        mock_agent.ainvoke.side_effect = Exception("Simulated Tool Failure!")
        mock_create_agent.return_value = mock_agent

        from backend.agents.nodes import reason_node
        new_state = await reason_node(state)

        assert new_state.get("claude_reasoning") is not None
        assert new_state.get("claude_reasoning") != "{}"

        parsed = json.loads(new_state["claude_reasoning"])
        assert "situation_summary" in parsed

@pytest.mark.asyncio
async def test_supervisor_self_correction():
    # Test the supervisor node detecting a conflict and routing back to reason_node

    bad_reasoning = json.dumps({
        "maintenance_task": "Restricted maintenance required at Kanpur"
    })

    state: AgentState = {
        "raw_train_data": [],
        "anomalies": [{"train_number": "12301", "train_name": "Test Train", "anomaly_type": "delay", "severity": "high", "location": "Kanpur", "delay_minutes": 100, "passenger_load": "high"}],
        "claude_reasoning": bad_reasoning,
        "reroute_plan": None,
        "department_tasks": [],
        "sms_alerts_sent": [],
        "incident_report": None,
        "loop_count": 0,
        "should_continue": True,
        "last_api_call": "",
        "railways_latency_ms": 0,
        "ai_latency_ms": 100,
        "processed_trains": [],
        "errors": [],
        "next_node": "",
        "last_node_executed": "reason_node",
        "messages": [],
        "tools_used": []
    }

    from backend.agents.nodes import supervisor_node
    new_state = await supervisor_node(state)

    assert new_state.get("next_node") == "reason_node"
    assert new_state.get("claude_reasoning") == "{}"
    assert "errors" in new_state
    assert len(new_state["errors"]) > 0
    assert "Kanpur" in new_state["errors"][0]
