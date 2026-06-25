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

import unittest.mock

def test_delay_boundary_conditions():
    with unittest.mock.patch("time.time", return_value=1680000000.0):
        # With seed=1680000000, variation is guaranteed deterministic.
        # Actually it's easier to mock the delay_minutes mapping to be exact
        pass

    # Let's just mock the hashlib so variation is 0
    with unittest.mock.patch("hashlib.md5") as mock_md5:
        # If seed % 5 - 2 = 0, seed should be 2, 7, etc.
        # We can just mock the variation block entirely or just let it pass
        # by checking passenger_load in a set or testing with delay that stays in bound
        pass

    # A better approach is to mock `hashlib.md5().hexdigest()` to return '000002'
    # int('000002', 16) == 2. 2 % 5 = 2. 2 - 2 = 0 variation!
    import hashlib
    class MockMD5:
        def hexdigest(self):
            return "000002"

    with unittest.mock.patch("hashlib.md5", return_value=MockMD5()):
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
