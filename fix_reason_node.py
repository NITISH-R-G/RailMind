import re

with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# I see that the reason_node replacement replaced the start of reason_node but left the remainder of the old reason_node hanging.
# Let's fix this by finding the new reason_node block and removing the leftover old code.

# Find the start of the leftover code
leftover_start = content.find("        # Fetch last 5 incidents for historical context")
# Find the start of the next valid function (which is reroute_node)
next_func = content.find("async def reroute_node(state: AgentState) -> dict:")

if leftover_start != -1 and next_func != -1:
    content = content[:leftover_start] + content[next_func:]

with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
