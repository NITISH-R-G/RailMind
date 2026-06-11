import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from backend.services.ai_service import reason_with_ai, MitigationPlan

@pytest.mark.asyncio
async def test_reason_with_ai_empty_anomalies():
    result = await reason_with_ai([])
    assert result == {}

@pytest.mark.asyncio
@patch("backend.services.ai_service.llm")
@patch("backend.services.ai_service.llm_with_tools")
async def test_reason_with_ai_success(mock_llm_with_tools, mock_llm):
    expected_response = {
        "incident_title": "Test Title",
        "situation_summary": "Test Summary",
        "maintenance_task": "Test Maintenance",
        "operations_task": "Test Operations",
        "station_manager_task": "Test Station Manager",
        "passenger_sms": "Test SMS",
        "incident_summary": "Test Incident Summary"
    }

    mock_llm_with_tools_res = MagicMock()
    mock_llm_with_tools_res.tool_calls = []

    mock_llm_with_tools.ainvoke = AsyncMock(return_value=mock_llm_with_tools_res)

    mock_structured_llm = MagicMock()
    mock_structured_llm.ainvoke = AsyncMock(return_value=MitigationPlan(**expected_response))
    mock_llm.with_structured_output.return_value = mock_structured_llm

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
    result = await reason_with_ai(anomalies)

    assert result == expected_response
    mock_llm_with_tools.ainvoke.assert_called()
    mock_structured_llm.ainvoke.assert_called_once()

@pytest.mark.asyncio
@patch("backend.services.ai_service.llm")
@patch("backend.services.ai_service.llm_with_tools")
async def test_reason_with_ai_fallback_json_error(mock_llm_with_tools, mock_llm):
    mock_llm_with_tools_res = MagicMock()
    mock_llm_with_tools_res.tool_calls = []
    mock_llm_with_tools.ainvoke = AsyncMock(return_value=mock_llm_with_tools_res)

    mock_structured_llm = MagicMock()
    mock_structured_llm.ainvoke = AsyncMock(side_effect=Exception("Invalid JSON string"))
    mock_llm.with_structured_output.return_value = mock_structured_llm

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
    result = await reason_with_ai(anomalies)

    assert "incident_title" in result
    assert result["incident_title"] == "123 Test Train delayed 10min at Unknown Station"

@pytest.mark.asyncio
@patch("backend.services.ai_service.llm")
@patch("backend.services.ai_service.llm_with_tools")
async def test_reason_with_ai_fallback_exception(mock_llm_with_tools, mock_llm):
    mock_llm_with_tools_res = MagicMock()
    mock_llm_with_tools_res.tool_calls = []
    mock_llm_with_tools.ainvoke = AsyncMock(return_value=mock_llm_with_tools_res)

    mock_structured_llm = MagicMock()
    mock_structured_llm.ainvoke = AsyncMock(side_effect=Exception("API Error"))
    mock_llm.with_structured_output.return_value = mock_structured_llm

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
    result = await reason_with_ai(anomalies)

    assert "incident_title" in result
    assert result["incident_title"] == "123 Test Train delayed 10min at Unknown Station"
