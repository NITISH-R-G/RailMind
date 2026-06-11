import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from backend.services.ai_service import reason_with_ai

@pytest.mark.asyncio
async def test_reason_with_ai_empty_anomalies():
    result = await reason_with_ai([])
    assert result == {}

@pytest.mark.asyncio
async def test_reason_with_ai_success():
    expected_response = {
        "incident_title": "Test Title",
        "situation_summary": "Test Summary",
        "maintenance_task": "Test Maintenance",
        "operations_task": "Test Operations",
        "station_manager_task": "Test Station Manager",
        "passenger_sms": "Test SMS",
        "incident_summary": "Test Incident Summary"
    }

    mock_msg = MagicMock()
    mock_msg.tool_calls = []

    mock_plan = MagicMock()
    mock_plan.dict.return_value = expected_response

    with patch("backend.services.ai_service.llm_with_tools") as mock_tools:
        mock_tools.ainvoke = AsyncMock(return_value=mock_msg)
        with patch("backend.services.ai_service.llm") as mock_llm:
            mock_structured_llm = AsyncMock()
            mock_structured_llm.ainvoke.return_value = mock_plan
            mock_llm.with_structured_output.return_value = mock_structured_llm

            anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
            result = await reason_with_ai(anomalies)

            assert result == expected_response
            mock_tools.ainvoke.assert_called_once()
            mock_structured_llm.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_reason_with_ai_fallback_json_error():
    mock_msg = MagicMock()
    mock_msg.tool_calls = []

    with patch("backend.services.ai_service.llm_with_tools") as mock_tools:
        mock_tools.ainvoke = AsyncMock(return_value=mock_msg)
        with patch("backend.services.ai_service.llm") as mock_llm:
            mock_structured_llm = AsyncMock()
            mock_structured_llm.ainvoke.side_effect = Exception("Invalid JSON string")
            mock_llm.with_structured_output.return_value = mock_structured_llm

            anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
            result = await reason_with_ai(anomalies)

            assert "incident_title" in result
            assert result["incident_title"] == "123 Test Train delayed 10min at Unknown Station"

@pytest.mark.asyncio
async def test_reason_with_ai_fallback_exception():
    mock_msg = MagicMock()
    mock_msg.tool_calls = []

    with patch("backend.services.ai_service.llm_with_tools") as mock_tools:
        mock_tools.ainvoke = AsyncMock(return_value=mock_msg)

        with patch("backend.services.ai_service.llm") as mock_llm:
            mock_structured_llm = AsyncMock()
            mock_structured_llm.ainvoke.side_effect = Exception("API Error")
            mock_llm.with_structured_output.return_value = mock_structured_llm

            anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
            result = await reason_with_ai(anomalies)

            assert "incident_title" in result
            assert result["incident_title"] == "123 Test Train delayed 10min at Unknown Station"
