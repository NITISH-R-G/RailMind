import re

with open("backend/agents/graph.py", "r") as f:
    content = f.read()

# Replace the whole graph construction part

new_graph_str = """
workflow = StateGraph(AgentState)
workflow.add_node("evaluate_previous_action", evaluate_previous_action)
workflow.add_node("ingest_node", ingest_node)
workflow.add_node("detect_node", detect_node)
workflow.add_node("predict_node", predict_node)
workflow.add_node("supervisor_node", supervisor_node)
workflow.add_node("reason_node", reason_node)
workflow.add_node("reroute_node", reroute_node)
workflow.add_node("coordination_node", coordination_node)
workflow.add_node("alert_node", alert_node)
workflow.add_node("report_node", report_node)

# Set supervisor as entry point
workflow.set_entry_point("supervisor_node")

def route_from_supervisor(state: AgentState) -> str:
    next_node = state.get("next_node", "END")
    if next_node == "END":
        return END
    return next_node

# All nodes route back to supervisor
workflow.add_edge("evaluate_previous_action", "supervisor_node")
workflow.add_edge("ingest_node", "supervisor_node")
workflow.add_edge("detect_node", "supervisor_node")
workflow.add_edge("predict_node", "supervisor_node")
workflow.add_edge("reason_node", "supervisor_node")
workflow.add_edge("reroute_node", "supervisor_node")
workflow.add_edge("coordination_node", "supervisor_node")
workflow.add_edge("alert_node", "supervisor_node")
workflow.add_edge("report_node", END)

# Supervisor dynamically dispatches
workflow.add_conditional_edges(
    "supervisor_node",
    route_from_supervisor,
    {
        "evaluate_previous_action": "evaluate_previous_action",
        "ingest_node": "ingest_node",
        "detect_node": "detect_node",
        "predict_node": "predict_node",
        "reason_node": "reason_node",
        "reroute_node": "reroute_node",
        "coordination_node": "coordination_node",
        "alert_node": "alert_node",
        "report_node": "report_node",
        END: END
    }
)

from langgraph.checkpoint.memory import MemorySaver
"""

content = re.sub(r'workflow = StateGraph\(AgentState\).*?from langgraph\.checkpoint\.memory import MemorySaver', new_graph_str, content, flags=re.DOTALL)

with open("backend/agents/graph.py", "w") as f:
    f.write(content)
