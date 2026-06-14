import re

with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# Fix the specific syntax error in supervisor_node
# Replace newline in f-string with escaped newline
content = content.replace('f"[RAILMIND] [ERROR] Supervisor node failed: {e}\n{tb}"', 'f"[RAILMIND] [ERROR] Supervisor node failed: {e}\\n{tb}"')

with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
