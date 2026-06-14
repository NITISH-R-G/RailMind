import re

with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# Update reason_node to use reason_with_ai
reason_node_new = '''async def reason_node(state: AgentState) -> dict:
    try:
        diff = {"last_node_executed": "reason_node"}
        anomalies = state.get("anomalies", [])
        if not anomalies:
            diff["claude_reasoning"] = "{}"
            diff["reroute_plan"] = None
            diff["incident_report"] = None
            await log_agent("reason_node", "[RAILMIND] [OK] All trains nominal, skipping AI reasoning")
            return diff

        await log_agent("reason_node", f"[RAILMIND] Contacting AI to reason about {len(anomalies)} anomalies...")

        import time
        start_time = time.time()

        # Use Tool Use API to generate mitigation plan
        errors = state.get("errors", [])
        plan = await reason_with_ai(anomalies, errors)

        # Format for downstream nodes
        diff["claude_reasoning"] = json.dumps(plan)
        if "reroute_plan" in plan:
            diff["reroute_plan"] = plan["reroute_plan"]

        latency = int((time.time() - start_time) * 1000)
        diff["ai_latency_ms"] = latency
        await log_agent("reason_node", f"[RAILMIND] Real Autonomous Brain cycle complete ({latency}ms)")
        return diff
    except Exception as e:
        logger.error(f"Error in reason_node: {e}")
        await log_agent("reason_node", f"[RAILMIND] [ERROR] Reason node failed: {e}")
        return {"last_node_executed": "reason_node", "errors": [f"reason_node error: {e}"]}
'''

content = re.sub(
    r'async def reason_node\(state: AgentState\) -> AgentState:.*?return state',
    reason_node_new,
    content,
    flags=re.DOTALL
)

# Update supervisor_node to handle self-correction and partial state returns
supervisor_node_new = '''async def supervisor_node(state: AgentState) -> dict:
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

content = re.sub(
    r'async def supervisor_node\(state: AgentState\) -> dict:.*?return \{"next_node": "END", "last_node_executed": "supervisor_node"\}',
    supervisor_node_new,
    content,
    flags=re.DOTALL
)


with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
