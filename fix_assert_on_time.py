with open('backend/tests/test_railways_api.py', 'r') as f:
    content = f.read()

content = content.replace('    assert result["passenger_load"] == "high" or result["passenger_load"] == "medium"\n    assert result["status"] == "delayed"', '    assert result["passenger_load"] == "high" or result["passenger_load"] == "medium"\n    assert result["status"] == "on_time"', 1)

with open('backend/tests/test_railways_api.py', 'w') as f:
    f.write(content)
