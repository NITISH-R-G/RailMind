import asyncio
import os
import sys

# Ensure backend can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.agents.graph import railmind_graph # type: ignore
from backend.agents.state import AgentState # type: ignore

async def main():
    # Initial state
    initial_state = {
        "raw_train_data": [],
        "anomalies": [],
        "claude_reasoning": "",
        "reroute_plan": None,
        "department_tasks": [],
        "sms_alerts_sent": [],
        "incident_report": None,
        "loop_count": 0,
        "should_continue": False,
        "last_api_call": "",
        "railways_latency_ms": 0,
        "ai_latency_ms": 0,
        "processed_trains": [],
        "next_node": None,
        "error_vector": None
    }
    
    print("--- Running RailMind Graph test run ---")
    
    # We will step through the graph for a single cycle
    step_count = 0
    config = {"configurable": {"thread_id": "test_thread_1"}, "recursion_limit": 20}

    async for event in railmind_graph.astream(initial_state, config):
        print(f"\n[EVENT] Node complete: {list(event.keys())}")
        for node_name, state_val in event.items():
            print(f"  - Raw trains count: {len(state_val.get('raw_train_data', []))}")
            print(f"  - Anomalies count: {len(state_val.get('anomalies', []))}")
            print(f"  - Should continue: {state_val.get('should_continue')}")
        
        step_count += 1
        if step_count >= 8:
            print("\n[TEST] Stopping stream to prevent infinite test loop.")
            break

if __name__ == "__main__":
    asyncio.run(main())
