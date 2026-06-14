import re
with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# Fix the specific indentation error at line 1441
content = content.replace("             return {\"next_node\": \"detect_node\", \"last_node_executed\": \"supervisor_node\"}", "            return {\"next_node\": \"detect_node\", \"last_node_executed\": \"supervisor_node\"}")
content = content.replace("             # AI ran but returned nothing. Stop ping-ponging.", "                # AI ran but returned nothing. Stop ping-ponging.")
content = content.replace("             return {\"next_node\": \"END\", \"last_node_executed\": \"supervisor_node\"}", "                return {\"next_node\": \"END\", \"last_node_executed\": \"supervisor_node\"}")
content = content.replace("             return {\"next_node\": \"reason_node\", \"last_node_executed\": \"supervisor_node\"}", "            return {\"next_node\": \"reason_node\", \"last_node_executed\": \"supervisor_node\"}")
content = content.replace("             return {\"next_node\": \"reroute_node\", \"last_node_executed\": \"supervisor_node\"}", "            return {\"next_node\": \"reroute_node\", \"last_node_executed\": \"supervisor_node\"}")
content = content.replace("         logger.exception(\"Error in supervisor_node\")", "        logger.exception(\"Error in supervisor_node\")")
content = content.replace("         tb = traceback.format_exc()", "        tb = traceback.format_exc()")
content = content.replace("         await log_agent(\"supervisor_node\", f\"[RAILMIND] [ERROR] Supervisor node failed: {e}\\n{tb}\")", "        await log_agent(\"supervisor_node\", f\"[RAILMIND] [ERROR] Supervisor node failed: {e}\\n{tb}\")")
content = content.replace("         return {\"next_node\": \"END\", \"last_node_executed\": \"supervisor_node\"}", "        return {\"next_node\": \"END\", \"last_node_executed\": \"supervisor_node\"}")

with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
