from langgraph.graph import StateGraph, END  # type: ignore
from langgraph.checkpoint.memory import MemorySaver # type: ignore
from .state import AgentState  # type: ignore
from .nodes import (  # type: ignore
    supervisor_node, ingest_node, detect_node, reason_node,
    reroute_node, coordination_node, alert_node, report_node
)

workflow = StateGraph(AgentState)
workflow.add_node("supervisor_node", supervisor_node)
workflow.add_node("ingest_node", ingest_node)
workflow.add_node("detect_node", detect_node)
workflow.add_node("reason_node", reason_node)
workflow.add_node("reroute_node", reroute_node)
workflow.add_node("coordination_node", coordination_node)
workflow.add_node("alert_node", alert_node)
workflow.add_node("report_node", report_node)

workflow.set_entry_point("supervisor_node")

def route_from_supervisor(state: AgentState) -> str:
    next_node = state.get("next_node")
    if not next_node or next_node == "END":
        return END
    return next_node

workflow.add_conditional_edges("supervisor_node", route_from_supervisor)

# All worker nodes return control to the supervisor
workflow.add_edge("ingest_node", "supervisor_node")
workflow.add_edge("detect_node", "supervisor_node")
workflow.add_edge("reason_node", "supervisor_node")
workflow.add_edge("reroute_node", "supervisor_node")
workflow.add_edge("coordination_node", "supervisor_node")
workflow.add_edge("alert_node", "supervisor_node")
# To loop indefinitely based on ingest -> detect -> report etc,
# report_node also goes back to supervisor, and supervisor will route to END
# if it has no anomalies, but our supervisor logic says if no raw_data, ingest,
# if raw_data and no processed, detect, else report_node... wait.
# Actually report_node sets loop_count and clears anomalies,
# so we want to go back to ingest.
# In supervisor_node: if not anomalies -> if processed_trains -> next_node: report_node wait this is wrong.
# Let's adjust report_node to route to END if we don't want infinite loop in test,
# or back to ingest_node? The test stream limits steps.
# In production, it loops. Let's just route to supervisor_node.
workflow.add_edge("report_node", "supervisor_node")

memory = MemorySaver()
railmind_graph = workflow.compile(checkpointer=memory)


