import re

with open("backend/tests/test_graph.py", "r") as f:
    content = f.read()

# Fix test_reason_node_tool_recovery to patch langgraph.prebuilt.create_react_agent
# Because inside ai_service.py we do: from langgraph.prebuilt import create_react_agent
content = content.replace("patch('backend.services.ai_service.create_react_agent')", "patch('langgraph.prebuilt.create_react_agent')")

with open("backend/tests/test_graph.py", "w") as f:
    f.write(content)
