import pytest
from backend.services.railways_api import (
    parse_rapidapi_train_for_agent,
    STATION_COORDS,
    get_live_train_status,
    parse_train_for_agent,
    get_cancelled_trains,
    get_trains_between_stations,
    get_multiple_trains,
    RailwaysAPIClient
)
from unittest.mock import patch
import httpx

def test_empty_or_missing_data():
    assert parse_rapidapi_train_for_agent({}, "12345") == {}
    assert parse_rapidapi_train_for_agent({"data": {}}, "12345") == {}

def test_normal_well_formed_dictionary():
    data = {
        "data": {
            "train_number": "12345",
            "train_name": "Test Train",
            "current_station_code": "NDLS",
            "current_station_name": "New Delhi",
            "delay": 0,
            "title": "Running",
            "cur_stn_sta": "10:00",
            "eta": "10:00",
            "source_stn_name": "Source",
            "dest_stn_name": "Destination"
        }
    }
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["train_number"] == "12345"
    assert result["train_name"] == "Test Train"
    assert result["delay_minutes"] == 0
    assert result["passenger_load"] == "normal"
    assert result["status"] == "on_time"
    assert result["schedule_arrival"] == "10:00"
    assert result["actual_arrival"] == "10:00"
    assert result["source"] == "Source"
    assert result["destination"] == "Destination"

def test_delay_boundary_conditions():
    # <= 15 minutes
    data = {"data": {"delay": 15}}
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["passenger_load"] == "medium"
    assert result["status"] == "on_time"

    # <= 30 minutes
    data = {"data": {"delay": 30}}
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["passenger_load"] == "high"
    assert result["status"] == "delayed"

    # > 30, <= 60 minutes
    data = {"data": {"delay": 45}}
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["passenger_load"] == "overcrowded"
    assert result["status"] == "delayed"

    # > 60 minutes
    data = {"data": {"delay": 65}}
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["passenger_load"] == "overcrowded"
    assert result["status"] == "severely_delayed"

def test_malformed_delay_values():
    data = {"data": {"delay": "unknown"}}
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["delay_minutes"] == 0
    assert result["passenger_load"] == "normal"
    assert result["status"] == "on_time"

def test_title_checks():
    data = {"data": {"title": "Train reached NDLS"}}
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["status"] == "reached"

    data = {"data": {"title": "Journey complete"}}
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["status"] == "reached"

def test_fallback_of_current_station_name():
    data = {
        "data": {
            "current_station_code": "NDLS",
            "current_station_name": "Unknown"
        }
    }
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["current_station"] == STATION_COORDS["NDLS"]["name"]

    data = {
        "data": {
            "current_station_code": "UNKNOWN_CODE",
            "current_station_name": "Unknown"
        }
    }
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["current_station"] == "Unknown"

@pytest.mark.asyncio
async def test_get_live_train_status_rapidapi_success(httpx_mock):
    httpx_mock.add_response(
        url="https://irctc1.p.rapidapi.com/api/v1/liveTrainStatus?trainNo=12345&startDay=0",
        json={
            "status": True,
            "data": {
                "train_number": "12345",
                "train_name": "RapidAPI Train",
                "current_station_code": "NDLS",
                "current_station_name": "New Delhi",
                "delay": 5,
                "title": "Running",
                "cur_stn_sta": "10:00",
                "eta": "10:05",
                "source_stn_name": "Source",
                "dest_stn_name": "Destination"
            }
        }
    )

    with patch("backend.services.railways_api.RAPIDAPI_KEY", "test_key"):
        result = await get_live_train_status("12345")
        assert result["train_number"] == "12345"
        assert result["train_name"] == "RapidAPI Train"
        assert result["delay_minutes"] == 5

@pytest.mark.asyncio
async def test_get_live_train_status_rapidapi_non_200(httpx_mock):
    httpx_mock.add_response(
        url="https://irctc1.p.rapidapi.com/api/v1/liveTrainStatus?trainNo=12301&startDay=0",
        status_code=500
    )

    with patch("backend.services.railways_api.RAPIDAPI_KEY", "test_key"):
        result = await get_live_train_status("12301")
        assert result["train_number"] == "12301" # Mock fallback

@pytest.mark.asyncio
async def test_get_live_train_status_rapidapi_false_status(httpx_mock):
    httpx_mock.add_response(
        url="https://irctc1.p.rapidapi.com/api/v1/liveTrainStatus?trainNo=12301&startDay=0",
        json={"status": False, "message": "Error"}
    )

    with patch("backend.services.railways_api.RAPIDAPI_KEY", "test_key"):
        result = await get_live_train_status("12301")
        assert result["train_number"] == "12301" # Mock fallback

@pytest.mark.asyncio
async def test_get_live_train_status_rapidapi_exception(httpx_mock):
    httpx_mock.add_exception(
        httpx.ReadTimeout("Timeout"),
        url="https://irctc1.p.rapidapi.com/api/v1/liveTrainStatus?trainNo=12301&startDay=0"
    )

    with patch("backend.services.railways_api.RAPIDAPI_KEY", "test_key"):
        result = await get_live_train_status("12301")
        assert result["train_number"] == "12301" # Mock fallback

@pytest.mark.asyncio
@patch("backend.services.railways_api.datetime")
async def test_get_live_train_status_indianrail_success(mock_datetime, httpx_mock):
    mock_datetime.now.return_value.strftime.return_value = "20231024"
    httpx_mock.add_response(
        url="https://indianrailapi.com/api/v2/livetrainstatus/apikey/test_key/trainnumber/12345/date/20231024/",
        json={
            "ResponseCode": "200",
            "TrainNumber": "12345",
            "CurrentStation": {
                "StationCode": "NDLS",
                "StationName": "New Delhi",
                "DelayInArrival": "10 M",
                "ScheduleArrival": "10:00",
                "ActualArrival": "10:10"
            },
            "TrainRoute": [{"StationName": "Src"}, {"StationName": "Dst"}]
        }
    )

    with patch("backend.services.railways_api.RAPIDAPI_KEY", None), \
         patch("backend.services.railways_api.RAILWAYS_API_KEY", "test_key"):
        result = await get_live_train_status("12345")
        assert result["train_number"] == "12345"
        assert result["delay_minutes"] == 10
        assert result["passenger_load"] == "medium"
        assert result["status"] == "on_time"

@pytest.mark.asyncio
@patch("backend.services.railways_api.datetime")
async def test_get_live_train_status_indianrail_exception(mock_datetime, httpx_mock):
    mock_datetime.now.return_value.strftime.return_value = "20231024"
    httpx_mock.add_exception(
        httpx.ReadTimeout("Timeout"),
        url="https://indianrailapi.com/api/v2/livetrainstatus/apikey/test_key/trainnumber/12301/date/20231024/"
    )

    with patch("backend.services.railways_api.RAPIDAPI_KEY", None), \
         patch("backend.services.railways_api.RAILWAYS_API_KEY", "test_key"):
        result = await get_live_train_status("12301")
        assert result["train_number"] == "12301"

def test_parse_train_for_agent():
    data = {
        "TrainNumber": "12345",
        "CurrentStation": {
            "StationCode": "NDLS",
            "StationName": "New Delhi",
            "DelayInArrival": "45 M",
            "ScheduleArrival": "10:00",
            "ActualArrival": "10:45"
        },
        "TrainRoute": [
            {"StationName": "SourceStation"},
            {"StationName": "Intermediate"},
            {"StationName": "DestStation"}
        ]
    }
    result = parse_train_for_agent(data, "12345")
    assert result["train_number"] == "12345"
    assert result["delay_minutes"] == 45
    assert result["passenger_load"] == "overcrowded"
    assert result["status"] == "delayed"
    assert result["source"] == "SourceStation"
    assert result["destination"] == "DestStation"

def test_parse_train_for_agent_malformed_delay():
    data = {
        "TrainNumber": "12345",
        "CurrentStation": {
            "StationCode": "NDLS",
            "DelayInArrival": "Unknown"
        }
    }
    result = parse_train_for_agent(data, "12345")
    assert result["delay_minutes"] == 0
    assert result["passenger_load"] == "normal"

@pytest.mark.asyncio
@patch("backend.services.railways_api.datetime")
async def test_get_cancelled_trains_success(mock_datetime, httpx_mock):
    mock_datetime.now.return_value.strftime.return_value = "20231024"
    httpx_mock.add_response(
        url="https://indianrailapi.com/api/v2/CancelledTrains/apikey/test_key/Date/20231024",
        json={"Trains": [{"TrainNo": "99999", "TrainName": "Test Cancelled"}]}
    )

    with patch("backend.services.railways_api.RAILWAYS_API_KEY", "test_key"):
        result = await get_cancelled_trains()
        assert len(result) == 1
        assert result[0]["TrainNo"] == "99999"

@pytest.mark.asyncio
@patch("backend.services.railways_api.datetime")
async def test_get_cancelled_trains_exception(mock_datetime, httpx_mock):
    mock_datetime.now.return_value.strftime.return_value = "20231024"
    httpx_mock.add_exception(
        httpx.ReadTimeout("Timeout"),
        url="https://indianrailapi.com/api/v2/CancelledTrains/apikey/test_key/Date/20231024"
    )

    with patch("backend.services.railways_api.RAILWAYS_API_KEY", "test_key"):
        result = await get_cancelled_trains()
        assert len(result) > 0 # Returns mock fallback
        assert result[0]["TrainNo"] == "12303"

@pytest.mark.asyncio
async def test_get_trains_between_stations_success(httpx_mock):
    httpx_mock.add_response(
        url="https://indianrailapi.com/api/v2/TrainBetweenStation/apikey/test_key/From/NDLS/To/HWH",
        json={"Trains": [{"TrainNo": "88888", "TrainName": "Test Between"}]}
    )

    with patch("backend.services.railways_api.RAILWAYS_API_KEY", "test_key"):
        result = await get_trains_between_stations("NDLS", "HWH")
        assert len(result) == 1
        assert result[0]["TrainNo"] == "88888"

@pytest.mark.asyncio
async def test_get_trains_between_stations_exception(httpx_mock):
    httpx_mock.add_exception(
        httpx.ReadTimeout("Timeout"),
        url="https://indianrailapi.com/api/v2/TrainBetweenStation/apikey/test_key/From/NDLS/To/HWH"
    )

    with patch("backend.services.railways_api.RAILWAYS_API_KEY", "test_key"):
        result = await get_trains_between_stations("NDLS", "HWH")
        assert len(result) > 0 # Returns mock fallback
        assert result[0]["TrainNo"] == "12301"

@pytest.mark.asyncio
@patch("backend.services.railways_api.get_live_train_status")
async def test_get_multiple_trains(mock_get_live_status):
    mock_get_live_status.side_effect = [{"train_number": "123"}, {"train_number": "456"}]

    result = await get_multiple_trains(["123", "456"])

    assert len(result) == 2
    assert result[0]["train_number"] == "123"
    assert result[1]["train_number"] == "456"
    assert mock_get_live_status.call_count == 2

@pytest.mark.asyncio
@patch("backend.services.railways_api.get_live_train_status")
@patch("backend.services.railways_api.get_cancelled_trains")
@patch("backend.services.railways_api.get_trains_between_stations")
@patch("backend.services.railways_api.get_multiple_trains")
async def test_railways_api_client(
    mock_multiple, mock_between, mock_cancelled, mock_live
):
    client = RailwaysAPIClient("test_client_key")

    mock_live.return_value = {"status": "ok"}
    result = await client.get_live_train_status("123")
    assert result == {"status": "ok"}
    mock_live.assert_called_with("123")

    mock_cancelled.return_value = [{"TrainNo": "999"}]
    result = await client.get_cancelled_trains()
    assert len(result) == 1
    mock_cancelled.assert_called_once()

    mock_between.return_value = [{"TrainNo": "888"}]
    result = await client.get_trains_between_stations("A", "B")
    assert len(result) == 1
    mock_between.assert_called_with("A", "B")

    mock_multiple.return_value = [{"train_number": "111"}]
    result = await client.get_multiple_trains(["111"])
    assert len(result) == 1
    mock_multiple.assert_called_with(["111"])

    mock_data = client.mock_train_data()
    assert isinstance(mock_data, list)
    assert len(mock_data) > 0
