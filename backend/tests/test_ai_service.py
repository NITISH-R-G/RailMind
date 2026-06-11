import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from backend.services.ai_service import reason_with_ai

@pytest.mark.asyncio
async def test_reason_with_ai_empty_anomalies():
    result = await reason_with_ai([])
    assert result == {}

@pytest.mark.asyncio
@patch("backend.services.ai_service.ChatAnthropic.with_structured_output")
@patch("langchain_core.runnables.base.RunnableBinding.ainvoke", new_callable=AsyncMock)
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

    mock_llm_res = MagicMock()
    mock_llm_res.tool_calls = []
    mock_ainvoke.return_value = mock_llm_res

    mock_structured_llm = AsyncMock()
    mock_structured_llm.ainvoke.return_value = MagicMock(**{"dict.return_value": expected_response})
    mock_with_structured_output.return_value = mock_structured_llm

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
    result = await reason_with_ai(anomalies)

    assert result == expected_response
    mock_ainvoke.assert_called_once()
    mock_structured_llm.ainvoke.assert_called_once()

@pytest.mark.asyncio
@patch("backend.services.ai_service.ChatAnthropic.with_structured_output")
@patch("langchain_core.runnables.base.RunnableBinding.ainvoke", new_callable=AsyncMock)
async def test_reason_with_ai_fallback_json_error(mock_ainvoke, mock_with_structured_output):
    mock_llm_res = MagicMock()
    mock_llm_res.tool_calls = []
    mock_ainvoke.return_value = mock_llm_res

    mock_structured_llm = AsyncMock()
    mock_structured_llm.ainvoke.side_effect = Exception("JSON Error")
    mock_with_structured_output.return_value = mock_structured_llm

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
    result = await reason_with_ai(anomalies)

    assert "incident_title" in result
    assert result["incident_title"] == "123 Test Train delayed 10min at Unknown Station"

@pytest.mark.asyncio
@patch("backend.services.ai_service.ChatAnthropic.with_structured_output")
@patch("langchain_core.runnables.base.RunnableBinding.ainvoke", new_callable=AsyncMock)
async def test_reason_with_ai_fallback_exception(mock_ainvoke, mock_with_structured_output):
    mock_llm_res = MagicMock()
    mock_llm_res.tool_calls = []
    mock_ainvoke.return_value = mock_llm_res

    mock_structured_llm = AsyncMock()
    mock_structured_llm.ainvoke.side_effect = Exception("API Error")
    mock_with_structured_output.return_value = mock_structured_llm

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
    result = await reason_with_ai(anomalies)

    assert "incident_title" in result
    assert result["incident_title"] == "123 Test Train delayed 10min at Unknown Station"
