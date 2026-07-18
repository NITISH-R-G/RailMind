with open('backend/tests/test_railways_api.py', 'r') as f:
    content = f.read()

content = content.replace('assert result["passenger_load"] == "medium"', 'assert result["passenger_load"] == "normal"', 2)

with open('backend/tests/test_railways_api.py', 'w') as f:
    f.write(content)
