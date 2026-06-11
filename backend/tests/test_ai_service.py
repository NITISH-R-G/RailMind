import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from backend.services.ai_service import reason_with_ai, MitigationPlan
from langchain_core.messages import AIMessage

@pytest.mark.asyncio
async def test_reason_with_ai_empty_anomalies():
    result = await reason_with_ai([])
    assert result == {}

@pytest.mark.asyncio
async def test_reason_with_ai_none_anomalies():
    result = await reason_with_ai(None)
    assert result == {}

@pytest.mark.asyncio
@patch("backend.services.ai_service.ChatAnthropic.with_structured_output")
@patch("langchain_core.runnables.base.RunnableBindingBase.ainvoke", new_callable=AsyncMock)
async def test_reason_with_ai_success(mock_ainvoke, mock_with_structured_output):
    expected_response = {
        "incident_title": "Test Title",
        "situation_summary": "Test Summary",
        "maintenance_task": "Test Maintenance",
        "operations_task": "Test Operations",
        "station_manager_task": "Test Station Manager",
        "passenger_sms": "Test SMS",
        "incident_summary": "Test Incident Summary"
    }

    # First loop breaks because tool_calls is empty
    mock_ainvoke.return_value = AIMessage(content="I am done", tool_calls=[])

    # Second invoke forces structured output
    mock_structured_llm = MagicMock()
    mock_structured_llm_ainvoke = AsyncMock()
    mock_structured_llm_ainvoke.return_value = MitigationPlan(**expected_response)
    mock_structured_llm.ainvoke = mock_structured_llm_ainvoke
    mock_with_structured_output.return_value = mock_structured_llm

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
    result = await reason_with_ai(anomalies)

    assert result == expected_response
    mock_ainvoke.assert_called()
    mock_structured_llm_ainvoke.assert_called()

@pytest.mark.asyncio
@patch("backend.services.ai_service.ChatAnthropic.with_structured_output")
@patch("langchain_core.runnables.base.RunnableBindingBase.ainvoke", new_callable=AsyncMock)
async def test_reason_with_ai_fallback_json_error(mock_ainvoke, mock_with_structured_output):
    # First loop breaks because tool_calls is empty
    mock_ainvoke.return_value = AIMessage(content="I am done", tool_calls=[])

    # Second invoke raises an exception to trigger the fallback block
    mock_structured_llm = MagicMock()
    mock_structured_llm_ainvoke = AsyncMock()
    mock_structured_llm_ainvoke.side_effect = Exception("Invalid JSON string")
    mock_structured_llm.ainvoke = mock_structured_llm_ainvoke
    mock_with_structured_output.return_value = mock_structured_llm

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
    result = await reason_with_ai(anomalies)

    assert "incident_title" in result
    assert result["incident_title"] == "123 Test Train delayed 10min at Unknown Station"
    mock_ainvoke.assert_called()
    mock_structured_llm_ainvoke.assert_called()

@pytest.mark.asyncio
@patch("backend.services.ai_service.ChatAnthropic.with_structured_output")
@patch("langchain_core.runnables.base.RunnableBindingBase.ainvoke", new_callable=AsyncMock)
async def test_reason_with_ai_fallback_exception(mock_ainvoke, mock_with_structured_output):
    # First loop breaks because tool_calls is empty
    mock_ainvoke.return_value = AIMessage(content="I am done", tool_calls=[])

    # Second invoke raises an exception to trigger the fallback block
    mock_structured_llm = MagicMock()
    mock_structured_llm_ainvoke = AsyncMock()
    mock_structured_llm_ainvoke.side_effect = Exception("API Error")
    mock_structured_llm.ainvoke = mock_structured_llm_ainvoke
    mock_with_structured_output.return_value = mock_structured_llm

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
    result = await reason_with_ai(anomalies)

    assert "incident_title" in result
    assert result["incident_title"] == "123 Test Train delayed 10min at Unknown Station"
    mock_ainvoke.assert_called()
    mock_structured_llm_ainvoke.assert_called()
