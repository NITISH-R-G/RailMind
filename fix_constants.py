import re

with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# I accidentally made constants definitions refer to themselves if the string was replaced.
# e.g. DEFAULT_PASSENGER_IMPACT = DEFAULT_PASSENGER_IMPACT
# Let's fix that block.

bad_block = """DEFAULT_PASSENGER_IMPACT = DEFAULT_PASSENGER_IMPACT
DEFAULT_MAINT_TASK = DEFAULT_MAINT_TASK
DEFAULT_OPS_TASK = DEFAULT_OPS_TASK
DEFAULT_STATION_TASK = DEFAULT_STATION_TASK
DEFAULT_SMS_TASK = DEFAULT_SMS_TASK"""

good_block = """DEFAULT_PASSENGER_IMPACT = "847 passengers affected"
DEFAULT_MAINT_TASK = "Inspect signaling hardware."
DEFAULT_OPS_TASK = "Execute scheduling adjustments."
DEFAULT_STATION_TASK = "Broadcast delay announcements."
DEFAULT_SMS_TASK = "Check platform screens for status updates." """

content = content.replace(bad_block, good_block)

with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
