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
    # Test agentic recovery when tool components report exceptions
    # We will simulate the ai_service encountering an exception and safely falling back

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

    # We mock the chat model to raise an exception during the react loop
    with patch('langgraph.prebuilt.create_react_agent') as mock_create_agent:
        mock_agent = MagicMock()
        mock_agent.ainvoke.side_effect = Exception("Simulated Tool Failure!")
        mock_create_agent.return_value = mock_agent

        # Invoke reason_node
        from backend.agents.nodes import reason_node
        new_state = await reason_node(state)

        # Verify it handled the exception and returned the fallback mock dictionary
        assert new_state.get("claude_reasoning") is not None

        parsed = json.loads(new_state["claude_reasoning"])
        assert "situation_summary" in parsed
        assert "delayed" in parsed["situation_summary"]

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
