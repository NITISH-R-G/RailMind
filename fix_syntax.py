with open("backend/agents/nodes.py", "r") as f:
    content = f.read()
content = content.replace('f"[RAILMIND] [ERROR] Supervisor node failed: {e}\n{tb}"', 'f"[RAILMIND] [ERROR] Supervisor node failed: {e}\\n{tb}"')
with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
