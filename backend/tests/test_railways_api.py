import pytest
from backend.services.railways_api import parse_rapidapi_train_for_agent, STATION_COORDS

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

def test_partial_data_schema():
    # Provide a payload that has a "data" key but is otherwise empty
    # This forces the parser to use default values for everything
    data = {"data": {"dummy_key": "dummy_value"}}
    result = parse_rapidapi_train_for_agent(data, "12345")

    assert result == {
        "train_number": "12345",
        "train_name": "12345",
        "current_station": "Unknown",
        "station_code": "Unknown",
        "delay_minutes": 0,
        "passenger_load": "normal",
        "status": "on_time",
        "schedule_arrival": "-",
        "actual_arrival": "-",
        "source": "Unknown",
        "destination": "Unknown",
        "lat": 20.5937,
        "lng": 78.9629
    }

def test_current_station_name_stripping():
    # Test stripping ~ and whitespace from current_station_name
    data = {
        "data": {
            "current_station_code": "UNKNOWN_CODE",
            "current_station_name": " ~New Delhi~ "
        }
    }
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["current_station"] == "New Delhi"

def test_train_name_fallback():
    # If train_name is missing, it should fall back to train_number
    # (Since outer_data.get("train_number", train_number) falls back to the parameter,
    # and then outer_data.get("train_name", t_num) falls back to the resolved t_num)
    data = {
        "data": {
            "train_number": "54321"
        }
    }
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["train_number"] == "54321"
    assert result["train_name"] == "54321"

def test_title_non_string():
    # Test that title handles non-string values gracefully (like None)
    data = {
        "data": {
            "title": None
        }
    }
    result = parse_rapidapi_train_for_agent(data, "12345")
    assert result["status"] == "on_time" # Default status since none is None and doesn't match "reached"
