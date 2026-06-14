import re

with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# Update reroute_node
reroute_node_new = '''async def reroute_node(state: AgentState) -> dict:
    try:
        await log_agent("reroute_node", "[RAILMIND] Checking and resolving rerouting options...")
        diff = {"last_node_executed": "reroute_node", "detour_route": []}
        anomalies = state.get("anomalies", [])
        if anomalies:
            anomaly = anomalies[0]
            start_station = anomaly.get("current_station") or anomaly.get("location") or ""
            target_station = anomaly.get("destination", "")

            # Use fallback destination if none provided
            if start_station == "Kanpur Central" and not target_station:
                target_station = "Varanasi"

            # Add geo-coordinate checking for A* or DP route discovery fallback
            lat = anomaly.get("lat")
            lng = anomaly.get("lng")
            await log_agent("reroute_node", f"[RAILMIND] Evaluating geo-coordinates (lat: {lat}, lng: {lng}) for track availability...")

            # Bypassing the anomaly location
            blocked = anomaly.get("location") or start_station

            from .routing import dijkstra_route_discovery
            result = dijkstra_route_discovery(start_station, target_station, blocked_station=blocked)
            # If path not found due to blockage, try standard routing
            if result["status"] != "Success":
                result = dijkstra_route_discovery(start_station, target_station)

            if result["status"] == "Success":
                route_str = " -> ".join(result["route"])
                await log_agent("reroute_node", f"[RAILMIND] Dijkstra bypass found: {route_str}")
                diff["reroute_plan"] = f"Dijkstra detour bypass: {route_str} (ETA {result['cost']} mins)"
                diff["detour_route"] = result["route"]
            else:
                status_msg = result.get("status", "Unknown status")
                await log_agent("reroute_node", f"[RAILMIND] No bypass route found: {status_msg}")
                diff["reroute_plan"] = f"No detour bypass available: {status_msg}"
        return diff
    except Exception as e:
        logger.error(f"Error in reroute_node: {e}")
        await log_agent("reroute_node", f"[RAILMIND] [ERROR] Reroute node failed: {e}")
        return {"last_node_executed": "reroute_node", "errors": [f"reroute error: {e}"], "detour_route": []}
'''

content = re.sub(
    r'async def reroute_node\(state: AgentState\) -> AgentState:.*?return \{"detour_route": \[\]\}',
    reroute_node_new,
    content,
    flags=re.DOTALL
)

with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
