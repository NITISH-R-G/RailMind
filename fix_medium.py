with open('backend/tests/test_railways_api.py', 'r') as f:
    content = f.read()

content = content.replace('def test_delay_boundary_conditions():\n    # <= 15 minutes\n    data = {"data": {"delay": 15}}\n    result = parse_rapidapi_train_for_agent(data, "12345")\n    assert result["passenger_load"] == "high"', 'def test_delay_boundary_conditions():\n    # <= 15 minutes\n    data = {"data": {"delay": 15}}\n    result = parse_rapidapi_train_for_agent(data, "12345")\n    assert result["passenger_load"] == "medium"')

with open('backend/tests/test_railways_api.py', 'w') as f:
    f.write(content)
