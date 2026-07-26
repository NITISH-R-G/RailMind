from langgraph.graph import StateGraph, END  # type: ignore
import os
from .state import AgentState  # type: ignore
from .nodes import (  # type: ignore
    detect_node, reason_node,
    reroute_node, coordination_node, alert_node, report_node,
    supervisor_node, predict_node
)

workflow = StateGraph(AgentState)
workflow.add_node("detect_node", detect_node)
workflow.add_node("predict_node", predict_node)
workflow.add_node("supervisor_node", supervisor_node)
workflow.add_node("reason_node", reason_node)
workflow.add_node("reroute_node", reroute_node)
workflow.add_node("coordination_node", coordination_node)
workflow.add_node("alert_node", alert_node)
workflow.add_node("report_node", report_node)

workflow.set_entry_point("supervisor_node")

def route_from_supervisor(state: AgentState) -> str:
    next_node = state.get("next_node", "END")
    if next_node == "END":
        return END
    return next_node

# All worker nodes return back to the supervisor
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
checkpointer = MemorySaver()
railmind_graph = workflow.compile(checkpointer=checkpointer)
