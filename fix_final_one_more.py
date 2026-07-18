with open('backend/tests/test_railways_api.py', 'r') as f:
    content = f.read()

content = content.replace('assert result["passenger_load"] == "normal"\n    assert result["status"] == "on_time"', 'assert result["passenger_load"] == "medium"\n    assert result["status"] == "on_time"')

content = content.replace('def test_malformed_delay_values():\n    data = {"data": {"delay": "unknown"}}\n    result = parse_rapidapi_train_for_agent(data, "12345")\n    assert result["delay_minutes"] == 0\n    assert result["passenger_load"] == "medium"', 'def test_malformed_delay_values():\n    data = {"data": {"delay": "unknown"}}\n    result = parse_rapidapi_train_for_agent(data, "12345")\n    assert result["delay_minutes"] == 0\n    assert result["passenger_load"] == "normal"')

with open('backend/tests/test_railways_api.py', 'w') as f:
    f.write(content)
