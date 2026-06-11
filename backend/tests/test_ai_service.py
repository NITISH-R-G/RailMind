import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from backend.services.ai_service import reason_with_ai, MitigationPlan

@pytest.mark.asyncio
async def test_reason_with_ai_empty_anomalies():
    result = await reason_with_ai([])
    assert result == {}

@pytest.mark.asyncio
async def test_reason_with_ai_success_no_tools():
    with patch("backend.services.ai_service.llm_with_tools") as mock_llm_with_tools:
        mock_llm_with_tools.ainvoke = AsyncMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_llm_with_tools.ainvoke.return_value = mock_response

        with patch("backend.services.ai_service.llm") as mock_llm:
            mock_structured_llm = MagicMock()
            mock_structured_llm.ainvoke = AsyncMock()
            mock_plan = MitigationPlan(
                incident_title="Test Title",
                situation_summary="Test Summary",
                maintenance_task="Test Maintenance",
                operations_task="Test Operations",
                station_manager_task="Test Station Manager",
                passenger_sms="Test SMS",
                incident_summary="Test Incident Summary"
            )
            mock_structured_llm.ainvoke.return_value = mock_plan
            mock_llm.with_structured_output.return_value = mock_structured_llm

            anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
            result = await reason_with_ai(anomalies)

            expected_response = {
                "incident_title": "Test Title",
                "situation_summary": "Test Summary",
                "maintenance_task": "Test Maintenance",
                "operations_task": "Test Operations",
                "station_manager_task": "Test Station Manager",
                "passenger_sms": "Test SMS",
                "incident_summary": "Test Incident Summary"
            }
            assert result == expected_response
            mock_llm_with_tools.ainvoke.assert_called_once()
            mock_structured_llm.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_reason_with_ai_success_with_tools():
    with patch("backend.services.ai_service.llm_with_tools") as mock_llm_with_tools:
        mock_llm_with_tools.ainvoke = AsyncMock()

        mock_response1 = MagicMock()
        mock_response1.tool_calls = [{"name": "query_line_capacity", "args": {"station": "Kanpur"}, "id": "call_1"}]

        mock_response2 = MagicMock()
        mock_response2.tool_calls = []

        mock_llm_with_tools.ainvoke.side_effect = [mock_response1, mock_response2]

        with patch("backend.services.ai_service.llm") as mock_llm:
            mock_structured_llm = MagicMock()
            mock_structured_llm.ainvoke = AsyncMock()
            mock_plan = MitigationPlan(
                incident_title="Test Title",
                situation_summary="Test Summary",
                maintenance_task="Test Maintenance",
                operations_task="Test Operations",
                station_manager_task="Test Station Manager",
                passenger_sms="Test SMS",
                incident_summary="Test Incident Summary"
            )
            mock_structured_llm.ainvoke.return_value = mock_plan
            mock_llm.with_structured_output.return_value = mock_structured_llm

            anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
            result = await reason_with_ai(anomalies)

            expected_response = {
                "incident_title": "Test Title",
                "situation_summary": "Test Summary",
                "maintenance_task": "Test Maintenance",
                "operations_task": "Test Operations",
                "station_manager_task": "Test Station Manager",
                "passenger_sms": "Test SMS",
                "incident_summary": "Test Incident Summary"
            }
            assert result == expected_response
            assert mock_llm_with_tools.ainvoke.call_count == 2
            mock_structured_llm.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_reason_with_ai_tool_error():
    with patch("backend.services.ai_service.llm_with_tools") as mock_llm_with_tools:
        mock_llm_with_tools.ainvoke = AsyncMock()

        mock_response1 = MagicMock()
        mock_response1.tool_calls = [{"name": "query_line_capacity", "args": {"station": "Kanpur"}, "id": "call_1"}]

        mock_response2 = MagicMock()
        mock_response2.tool_calls = []

        mock_llm_with_tools.ainvoke.side_effect = [mock_response1, mock_response2]

        with patch("backend.services.ai_service.llm") as mock_llm:
            with patch("backend.services.ai_service.tool_map") as mock_tool_map:
                mock_tool_func = MagicMock()
                mock_tool_func.ainvoke = AsyncMock()
                mock_tool_func.ainvoke.side_effect = Exception("Tool error")
                mock_tool_map.__getitem__.return_value = mock_tool_func

                mock_structured_llm = MagicMock()
                mock_structured_llm.ainvoke = AsyncMock()
                mock_plan = MitigationPlan(
                    incident_title="Test Title",
                    situation_summary="Test Summary",
                    maintenance_task="Test Maintenance",
                    operations_task="Test Operations",
                    station_manager_task="Test Station Manager",
                    passenger_sms="Test SMS",
                    incident_summary="Test Incident Summary"
                )
                mock_structured_llm.ainvoke.return_value = mock_plan
                mock_llm.with_structured_output.return_value = mock_structured_llm

                anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
                result = await reason_with_ai(anomalies)

                assert result["incident_title"] == "Test Title"

@pytest.mark.asyncio
async def test_reason_with_ai_fallback_exception():
    with patch("backend.services.ai_service.llm_with_tools") as mock_llm_with_tools:
        mock_llm_with_tools.ainvoke = AsyncMock()
        mock_response1 = MagicMock()
        mock_response1.tool_calls = []
        mock_llm_with_tools.ainvoke.return_value = mock_response1

        with patch("backend.services.ai_service.llm") as mock_llm:
            mock_structured_llm = MagicMock()
            mock_structured_llm.ainvoke = AsyncMock()
            mock_structured_llm.ainvoke.side_effect = Exception("API Error")
            mock_llm.with_structured_output.return_value = mock_structured_llm

            anomalies = [{"train_name": "Test Train", "train_number": "123", "delay_minutes": 10}]
            result = await reason_with_ai(anomalies)

            assert "incident_title" in result
            assert result["incident_title"] == "123 Test Train delayed 10min at Unknown Station"
