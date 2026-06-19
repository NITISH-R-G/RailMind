import re

with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# I did the same bad constant replacement earlier!
bad_err_block = """ERR_BROADCAST_MSG = ERR_BROADCAST_MSG
ERR_OCCURRED_MSG = ERR_OCCURRED_MSG
DEFAULT_PASSENGER_IMPACT ="""

good_err_block = """ERR_BROADCAST_MSG = "Failed to broadcast update: %s"
ERR_OCCURRED_MSG = "Error occurred: %s"
DEFAULT_PASSENGER_IMPACT ="""

content = content.replace(bad_err_block, good_err_block)

with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
