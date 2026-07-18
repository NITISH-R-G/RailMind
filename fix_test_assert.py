with open('backend/tests/test_railways_api.py', 'r') as f:
    content = f.read()

# Let's fix test_delay_boundary_conditions strictly manually
import re
new_test = '''def test_delay_boundary_conditions():
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
    assert result["status"] == "severely_delayed"'''

content = re.sub(r'def test_delay_boundary_conditions\(\):.*?assert result\["status"\] == "severely_delayed"', new_test, content, flags=re.DOTALL)

with open('backend/tests/test_railways_api.py', 'w') as f:
    f.write(content)
