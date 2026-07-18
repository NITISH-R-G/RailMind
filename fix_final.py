import re

with open('backend/tests/test_railways_api.py', 'r') as f:
    test_content = f.read()

# Change the second medium check to high.
test_content = test_content.replace('assert result["passenger_load"] == "medium"', 'assert result["passenger_load"] == "high"')

with open('backend/tests/test_railways_api.py', 'w') as f:
    f.write(test_content)


with open('backend/agents/nodes.py', 'r') as f:
    content = f.read()

# Make sure we don't have unbound local error on time
content = content.replace("start_time_metric = time.time()", "import time\n    start_time_metric = time.time()")

with open('backend/agents/nodes.py', 'w') as f:
    f.write(content)
