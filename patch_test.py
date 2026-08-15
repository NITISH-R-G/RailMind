import unittest.mock
from backend.services.railways_api import parse_rapidapi_train_for_agent

@unittest.mock.patch('time.time', return_value=12345678.0)
def run_test(mock_time):
    data = {"data": {"delay": 15}}
    result = parse_rapidapi_train_for_agent(data, "12345")
    print(result["delay_minutes"])
    print(result["passenger_load"])

run_test()
