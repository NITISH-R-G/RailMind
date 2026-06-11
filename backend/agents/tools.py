import json
from typing import Dict, Any
from langchain_core.tools import tool # type: ignore

@tool
def check_line_capacity(station: str, time_window: str) -> str:
    """Queries available line capacities at a given station for a time window."""
    # Mock implementation
    data = {
        "station": station,
        "time_window": time_window,
        "capacity": "75%",
        "available_tracks": [3, 4, 6]
    }
    return json.dumps(data)

@tool
def check_local_weather(location: str) -> str:
    """Checks the local weather grid for a specific location."""
    # Mock implementation
    data = {
        "location": location,
        "weather": "Clear",
        "temperature_celsius": 28,
        "visibility_km": 10
    }
    return json.dumps(data)

@tool
def review_historical_incidents(train_number: str, location: str) -> str:
    """Reviews historical incident databases for a train at a given location."""
    # Mock implementation
    data = {
        "train_number": train_number,
        "location": location,
        "past_incidents": [
            {"date": "2023-01-15", "type": "Signal Failure", "delay": 45},
            {"date": "2023-08-02", "type": "Track Maintenance", "delay": 20}
        ]
    }
    return json.dumps(data)

TOOLS = [check_line_capacity, check_local_weather, review_historical_incidents]
