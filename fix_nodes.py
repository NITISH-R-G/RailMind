import re

with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# Fix 1: Ensure reason_with_ai is properly imported
if "from ..services.ai_service import reason_with_ai" not in content:
    content = content.replace("from ..services.ai_service import ", "from ..services.ai_service import reason_with_ai, ")

# Fix 2: Remove the duplicated/hanging supervisor_node code that caused SyntaxError.
# We will find the correct start and end of the supervisor node to cleanly replace it.
import ast

try:
    tree = ast.parse(content)
except SyntaxError:
    # If there's a syntax error, let's fix it by regex string manipulation
    # Find the newly injected supervisor_node
    match = re.search(r'async def supervisor_node\(state: AgentState\) -> dict:.*?(?=async def |$)', content, re.DOTALL)
    if match:
        start_idx = match.start()
        # Cleanly extract up to start_idx and just keep the new supervisor node
        content = content[:start_idx] + match.group(0)

        # But wait, the new supervisor node itself has an exception block that returns END.
        # Let's cleanly rewrite supervisor_node

supervisor_clean = '''async def supervisor_node(state: AgentState) -> dict:
    try:
        last_node = state.get("last_node_executed")
        await log_agent("supervisor_node", f"[RAILMIND] Supervisor evaluating graph state... (Last execution: {last_node})")

        anomalies = state.get("anomalies", [])
        if last_node == "supervisor_node" and (not anomalies or state.get("should_continue") is False):
            return {"next_node": "END", "last_node_executed": "supervisor_node"}

        # If we just came from ingest, we must go to detect.
        if not last_node or last_node == "ingest_node" or last_node == "supervisor_node" and not anomalies:
             return {"next_node": "detect_node", "last_node_executed": "supervisor_node"}

        # If reasoning hasn't happened or failed to produce plan
        if not state.get("claude_reasoning") or state.get("claude_reasoning") == "{}":
            if getattr(state, "get", lambda k,d: d)("ai_latency_ms", -1) > 0:
                 # AI ran but returned nothing. Stop ping-ponging.
                 return {"next_node": "END", "last_node_executed": "supervisor_node"}
            return {"next_node": "reason_node", "last_node_executed": "supervisor_node"}

        # Self correction loop check
        try:
            reasoning = json.loads(state.get("claude_reasoning", "{}"))
            maintenance = reasoning.get("maintenance_task", "")
            if "Kanpur" in maintenance and "restricted" in maintenance.lower():
                 # Mock conflict logic
                 await log_agent("supervisor_node", "[RAILMIND] [WARNING] Conflict detected in maintenance task. Re-routing to Reasoner.")
                 return {
                     "errors": ["Maintenance task conflicts with active line configurations at Kanpur."],
                     "claude_reasoning": "{}", # clear to force re-reason
                     "next_node": "reason_node",
                     "last_node_executed": "supervisor_node"
                 }
        except json.JSONDecodeError as e:
            logger.warning("JSON parse failed: %s", e)
        except Exception:
            logger.exception("Unexpected error in supervisor self-correction logic")
            pass # continue to normal routing if parsing fails

        if not state.get("reroute_plan"):
             return {"next_node": "reroute_node", "last_node_executed": "supervisor_node"}

        # If tasks not generated
        if not state.get("department_tasks"):
            return {"next_node": "coordination_node", "last_node_executed": "supervisor_node"}

        # If alerts not sent
        if not state.get("sms_alerts_sent") and len(state.get("department_tasks", [])) > 0:
            return {"next_node": "alert_node", "last_node_executed": "supervisor_node"}

        # Otherwise report and finish
        return {"next_node": "report_node", "last_node_executed": "supervisor_node"}

    except Exception as e:
        import traceback
        logger.exception("Error in supervisor_node")
        tb = traceback.format_exc()
        await log_agent("supervisor_node", f"[RAILMIND] [ERROR] Supervisor node failed: {e}\\n{tb}")
        return {"next_node": "END", "last_node_executed": "supervisor_node"}
'''

# Delete all supervisor_node definitions and replace with clean one
content = re.sub(r'async def supervisor_node\(state: AgentState\).*', supervisor_clean, content, flags=re.DOTALL)

with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
