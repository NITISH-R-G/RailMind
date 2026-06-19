import pytest
import json
from unittest.mock import patch, AsyncMock
from backend.services.ai_service import reason_with_ai

@pytest.mark.asyncio
async def test_reason_with_ai_empty_anomalies():
    result = await reason_with_ai([])
    assert result == {}

@pytest.mark.asyncio
@patch("backend.services.ai_service.ChatAnthropic.ainvoke", new_callable=AsyncMock)
async def test_reason_with_ai_success(mock_generate_content):
    expected_response = {
        "incident_title": "Test Title",
        "situation_summary": "Test Summary",
        "maintenance_task": "Test Maintenance",
        "operations_task": "Test Operations",
        "station_manager_task": "Test Station Manager",
        "passenger_sms": "Test SMS",
        "incident_summary": "Test Incident Summary"
    }

    from langchain_core.messages import AIMessage
    mock_response = AIMessage(
        content="",
        tool_calls=[{
            "name": "MitigationPlan",
            "args": expected_response,
            "id": "call_1"
        }]
    )
    mock_generate_content.return_value = mock_response

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
    result = await reason_with_ai(anomalies)

    assert result == expected_response

@pytest.mark.asyncio
@patch("langgraph.prebuilt.create_react_agent")
async def test_reason_with_ai_fallback_exception(mock_create_agent):
    mock_agent = AsyncMock()
    mock_agent.ainvoke.side_effect = Exception("API Error")
    mock_create_agent.return_value = mock_agent

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
    result = await reason_with_ai(anomalies)

    assert "incident_title" in result
    assert "situation_summary" in result
