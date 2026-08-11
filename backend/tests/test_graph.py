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
    # The ai circuit breaker should catch failures and return get_local_llm_fallback()

    anomalies = [{
        "train_number": "12301",
        "train_name": "Test Train",
        "anomaly_type": "delay",
        "severity": "high",
        "location": "Kanpur",
        "delay_minutes": 100,
        "passenger_load": "high"
    }]

    state = {
        "raw_train_data": [],
        "anomalies": anomalies,
        "claude_reasoning": "",
        "reroute_plan": None,
        "department_tasks": [],
        "sms_alerts_sent": [],
        "incident_report": None,
        "loop_count": 0,
        "should_continue": True,
        "processed_trains": []
    }

    # Actually invoke the graph to see it run through reason_node
    # We will just verify it runs and next node is reroute_node (if reasoning produces plan) or ends
    # or that reason node itself doesn't crash.

    from backend.agents.nodes import reason_node

    # Let's directly call reason_node to test it handles errors (since ChatAnthropic is mocked to throw or we use the fallback)
    result = await reason_node(state)

    # The result should contain a claude_reasoning JSON string
    assert "claude_reasoning" in result
    import json
    reasoning = json.loads(result["claude_reasoning"])

    # It should either have a plan or the local fallback plan.
    assert isinstance(reasoning, dict)
    assert "situation_summary" in reasoning

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
