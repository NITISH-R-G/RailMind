import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from backend.services.ai_service import reason_with_ai

from contextlib import asynccontextmanager

@asynccontextmanager
async def mock_llm_setup(mock_tools_invoke, mock_structured_invoke):
    import backend.services.ai_service

    original_llm_with_tools = backend.services.ai_service.llm_with_tools
    original_llm = backend.services.ai_service.llm

    mock_llm_with_tools = MagicMock()
    mock_llm_with_tools.ainvoke = mock_tools_invoke
    backend.services.ai_service.llm_with_tools = mock_llm_with_tools

    mock_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_structured_llm.ainvoke = mock_structured_invoke
    mock_llm.with_structured_output.return_value = mock_structured_llm
    backend.services.ai_service.llm = mock_llm

    try:
        yield
    finally:
        backend.services.ai_service.llm_with_tools = original_llm_with_tools
        backend.services.ai_service.llm = original_llm

@pytest.mark.asyncio
async def test_reason_with_ai_empty_anomalies():
    result = await reason_with_ai([])
    assert result == {}

@pytest.mark.asyncio
async def test_reason_with_ai_none_anomalies():
    result = await reason_with_ai(None)
    assert result == {}

@pytest.mark.asyncio
async def test_reason_with_ai_success():
    mock_tools_invoke = AsyncMock()
    mock_structured_invoke = AsyncMock()

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
    mock_res = AIMessage(content="Test content")
    mock_res.tool_calls = []
    mock_tools_invoke.return_value = mock_res

    from backend.services.ai_service import MitigationPlan
    mock_plan = MitigationPlan(**expected_response)
    mock_structured_invoke.return_value = mock_plan

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]

    async with mock_llm_setup(mock_tools_invoke, mock_structured_invoke):
        result = await reason_with_ai(anomalies)

        assert result == expected_response
        mock_tools_invoke.assert_called_once()
        mock_structured_invoke.assert_called_once()

@pytest.mark.asyncio
async def test_reason_with_ai_fallback_json_error():
    mock_tools_invoke = AsyncMock()
    mock_structured_invoke = AsyncMock()

    from langchain_core.messages import AIMessage
    mock_res = AIMessage(content="Test content")
    mock_res.tool_calls = []
    mock_tools_invoke.return_value = mock_res

    mock_structured_invoke.side_effect = ValueError("Invalid JSON string")

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]

    async with mock_llm_setup(mock_tools_invoke, mock_structured_invoke):
        result = await reason_with_ai(anomalies)

        assert "incident_title" in result
        assert result["incident_title"] == "123 Test Train delayed 10min at Unknown Station"

@pytest.mark.asyncio
async def test_reason_with_ai_fallback_exception():
    mock_tools_invoke = AsyncMock()
    mock_structured_invoke = AsyncMock()

    from langchain_core.messages import AIMessage
    mock_res = AIMessage(content="Test content")
    mock_res.tool_calls = []
    mock_tools_invoke.return_value = mock_res

    mock_structured_invoke.side_effect = Exception("API Error")

    anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]

    async with mock_llm_setup(mock_tools_invoke, mock_structured_invoke):
        result = await reason_with_ai(anomalies)

        assert "incident_title" in result
        assert result["incident_title"] == "123 Test Train delayed 10min at Unknown Station"
