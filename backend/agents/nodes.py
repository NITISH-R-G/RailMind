import os
import json
import logging
from dotenv import load_dotenv
from typing import List
from uuid import uuid4
from datetime import datetime
from ..services.ai_service import reason_with_ai
from .state import AgentState, TrainAnomaly, DepartmentTask
from ..services.db_client import db_client
from ..services.railways_api import get_cancelled_trains, mock_train_data, RailwaysAPIClient, get_multiple_trains
from ..services.twilio_service import TwilioSMSClient
from ..api.websocket import websocket_manager

logger = logging.getLogger(__name__)

# Ensure env variables are loaded before configuration
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("RAILWAYS_API_KEY", "mock_key")
railways_client = RailwaysAPIClient(api_key=api_key)

twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "mock_sid")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "mock_token")
twilio_from = os.getenv("TWILIO_PHONE_NUMBER", "+1234567890")
twilio_client = TwilioSMSClient(account_sid=twilio_sid, auth_token=twilio_token, from_number=twilio_from)

# Shared log assistant that prints logs and broadcasts AGENT_LOG WebSocket events (ISSUE 4)
async def log_agent(node_name: str, message: str):
    print(message)
    try:
        await websocket_manager.broadcast(json.dumps({
            "type": "AGENT_LOG",
            "message": f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] [{node_name}] {message}",
            "timestamp": datetime.utcnow().isoformat()
        }))
    except Exception as e:
        logger.error(f"Failed to broadcast AGENT_LOG message: {e}")

async def supervisor_node(state: AgentState) -> dict:
    await log_agent("supervisor_node", "[RAILMIND] Supervisor evaluating next actions...")

    # If there's an error vector, we need to correct it. Route to reason_node.
    if state.get("error_vector"):
        await log_agent("supervisor_node", f"[RAILMIND] Processing error vector: {state['error_vector']}")
        return {"next_node": "reason_node", "error_vector": None}

    # Track the last node executed to prevent infinite loops when data doesn't change
    last_node = state.get("last_node_executed", "")

    if not state.get("raw_train_data") and last_node != "ingest_node":
        return {"next_node": "ingest_node"}

    anomalies = state.get("anomalies", [])
    if not anomalies:
        # We have raw data, but no anomalies. Did we run detect?
        if last_node == "ingest_node" or last_node == "report_node":
            return {"next_node": "detect_node"}
        # If we ran detect and still no anomalies, we are done
        if last_node == "detect_node":
             return {"next_node": "END"}

    # We have anomalies. Do we have reasoning?
    if not state.get("claude_reasoning") and last_node not in ["reason_node", "reroute_node", "coordination_node", "alert_node", "report_node"]:
        return {"next_node": "reason_node"}

    # We have reasoning (or it failed and returned {}). Do we have a reroute plan?
    if not state.get("reroute_plan") and last_node not in ["reroute_node", "coordination_node", "alert_node", "report_node"]:
        return {"next_node": "reroute_node"}

    # We have a reroute plan (or failed). Do we have department tasks?
    if not state.get("department_tasks") and last_node not in ["coordination_node", "alert_node", "report_node"]:
        return {"next_node": "coordination_node"}

    # We have tasks. Have we sent alerts?
    if not state.get("sms_alerts_sent") and last_node not in ["alert_node", "report_node"]:
        return {"next_node": "alert_node"}

    # We have alerted. Generate report.
    if not state.get("incident_report") and last_node != "report_node":
        return {"next_node": "report_node"}

    # If we just ran report node, we can start again
    if last_node == "report_node":
        return {"next_node": "ingest_node"}

    return {"next_node": "END"}


async def ingest_node(state: AgentState) -> dict:
    try:
        await log_agent("ingest_node", "[RAILMIND] Ingesting live train status from API feeds...")
        train_numbers = [
            "12301", "12951", "12001", "12259", "12565",
            "11057", "12627", "12625", "12621", "12615",
            "12309", "12721", "12229", "12311", "12641"
        ]
        
        import time
        start_time = time.time()
        
        client = railways_client
        print(f"[RAILMIND] Calling Railways API for {len(train_numbers)} trains...")
        results = await client.get_multiple_trains(train_numbers)
        
        # Ensure that if some train fetches failed and returned empty dict, they fallback to get_mock_rapidapi_train
        # So we always have all 15 trains
        train_results = []
        for tn in train_numbers:
            found = False
            for r in results:
                if r.get("train_number") == tn:
                    train_results.append(r)
                    found = True
                    break
            if not found:
                from ..services.railways_api import get_mock_rapidapi_train, parse_rapidapi_train_for_agent
                mock_data = get_mock_rapidapi_train(tn)
                parsed_mock = parse_rapidapi_train_for_agent(mock_data, tn)
                if parsed_mock:
                    train_results.append(parsed_mock)
        
        results = train_results
        
        latency = int((time.time() - start_time) * 1000)
        state["last_api_call"] = datetime.utcnow().isoformat()
        state["railways_latency_ms"] = latency
        
        print(f"[RAILMIND] API returned {len(results)} trains")
        print(f"[RAILMIND] Sample: {results[0] if results else 'EMPTY - using mock'}")
        
        if not results:
            print("[RAILMIND] WARNING: Railways API returned no data, check RAILWAYS_API_KEY in .env")
            await log_agent("ingest_node", "[RAILMIND] WARNING: Railways API returned no data, check RAILWAYS_API_KEY in .env")
            results = mock_train_data()
            print("[RAILMIND] Using mock fallback data")
            await log_agent("ingest_node", "[RAILMIND] Using mock fallback data")
            
        cancelled = await get_cancelled_trains()
        live_trains = results.copy()
        for train in cancelled:
            live_trains.append({
                "train_number": train.get("TrainNo", "Unknown"),
                "train_name": train.get("TrainName", "Unknown"),
                "status": "cancelled",
                "delay_minutes": 999,
                "passenger_load": "overcrowded",
                "current_station": "Unknown",
                "lat": 20.5937,
                "lng": 78.9629
            })
        
        for train in live_trains:
            await websocket_manager.broadcast(json.dumps({
                "type": "TRAIN_UPDATE",
                "data": train
            }))
        
        await log_agent("ingest_node", f"[RAILMIND] Ingested {len(live_trains)} trains")
        return {
            "raw_train_data": live_trains,
            "last_api_call": state.get("last_api_call", ""),
            "railways_latency_ms": state.get("railways_latency_ms", 0),
            "last_node_executed": "ingest_node"
        }
    except Exception as e:
        logger.error(f"Error in ingest_node: {e}")
        await log_agent("ingest_node", f"[RAILMIND] [ERROR] Ingest node failed: {e}")
        return {"error_vector": f"Ingest failed: {str(e)}"}

async def detect_node(state: AgentState) -> dict:
    try:
        await log_agent("detect_node", "[RAILMIND] Running real-time anomaly detection rules...")
        anomalies: List[TrainAnomaly] = []
        raw_data = state.get("raw_train_data", [])
        processed_trains = state.get("processed_trains", [])
        for train in raw_data:
            train_num = train.get("train_number", "Unknown")
            if train_num in processed_trains:
                continue
            train_name = train.get("train_name", "Unknown")
            location = train.get("current_station") or train.get("source") or "Unknown"
            delay = train.get("delay_minutes", 0)
            load = train.get("passenger_load")
            status = str(train.get("status") or "").lower()
            
            # Rule 1: delay > 15 minutes
            if delay > 15:
                severity = "low"
                if 15 < delay <= 30:
                    severity = "low"
                elif 30 < delay <= 60:
                    severity = "medium"
                elif 60 < delay <= 120:
                    severity = "high"
                elif delay > 120:
                    severity = "critical"
                    
                anomalies.append({
                    "train_number": train_num,
                    "train_name": train_name,
                    "anomaly_type": "delay",
                    "severity": severity,
                    "location": location,
                    "delay_minutes": delay,
                    "passenger_load": load,
                    "current_station": train.get("current_station") or location,
                    "status": status or "delayed",
                    "source": train.get("source") or "Unknown",
                    "destination": train.get("destination") or "Unknown"
                })
                
            # Rule 2: overcrowding checks
            elif load == "overcrowded":
                anomalies.append({
                    "train_number": train_num,
                    "train_name": train_name,
                    "anomaly_type": "overcrowding",
                    "severity": "high",
                    "location": location,
                    "delay_minutes": delay,
                    "passenger_load": load,
                    "current_station": train.get("current_station") or location,
                    "status": status or "delayed",
                    "source": train.get("source") or "Unknown",
                    "destination": train.get("destination") or "Unknown"
                })
                
            # Rule 3: cancellations
            elif status == "cancelled":
                anomalies.append({
                    "train_number": train_num,
                    "train_name": train_name,
                    "anomaly_type": "cancellation",
                    "severity": "critical",
                    "location": location,
                    "delay_minutes": delay,
                    "passenger_load": load,
                    "current_station": train.get("current_station") or location,
                    "status": "cancelled",
                    "source": train.get("source") or "Unknown",
                    "destination": train.get("destination") or "Unknown"
                })
                
        n = len(anomalies)
        if n > 0:
            await log_agent("detect_node", f"[RAILMIND] [WARNING] Detected {n} anomalies")
            return {"anomalies": anomalies, "should_continue": True, "last_node_executed": "detect_node"}
        else:
            await log_agent("detect_node", "[RAILMIND] [OK] All trains nominal")
            return {"anomalies": [], "should_continue": False, "last_node_executed": "detect_node"}
    except Exception as e:
        logger.error(f"Error in detect_node: {e}")
        await log_agent("detect_node", f"[RAILMIND] [ERROR] Detect node failed: {e}")
        return {"error_vector": f"Detect failed: {str(e)}"}

async def reason_node(state: AgentState) -> dict:
    try:
        anomalies = state.get("anomalies", [])
        if not anomalies:
            await log_agent("reason_node", "[RAILMIND] [OK] All trains nominal, skipping AI reasoning")
            return {
                "claude_reasoning": "{}",
                "reroute_plan": None,
                "incident_report": None,
                "last_node_executed": "reason_node"
            }

        await log_agent("reason_node", f"[RAILMIND] Contacting AI to reason about {len(anomalies)} anomalies...")
        
        import time
        start_time = time.time()
        
        result = await reason_with_ai(anomalies)
        
        latency = int((time.time() - start_time) * 1000)
        
        if result:
            await log_agent("reason_node", f"[RAILMIND] AI reasoning: {result.get('situation_summary')}")
            return {
                "claude_reasoning": json.dumps(result),
                "ai_latency_ms": latency,
                "reroute_plan": result.get("reroute_plan"),
                "incident_report": result.get("incident_summary"),
                "last_node_executed": "reason_node"
            }
        else:
            await log_agent("reason_node", "[RAILMIND] AI reasoning failed — using defaults")
            return {
                "claude_reasoning": "{}",
                "ai_latency_ms": latency,
                "last_node_executed": "reason_node"
            }
    except Exception as e:
        logger.error(f"Error in reason_node: {e}")
        await log_agent("reason_node", f"[RAILMIND] [ERROR] Reason node failed: {e}")
        return {"error_vector": f"Reasoning failed: {str(e)}"}

import heapq
import math

def heuristic(a: tuple, b: tuple) -> float:
    # simple euclidean distance for demo
    return math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2)

async def a_star_search(start: str, goal: str, graph: dict) -> list:
    if start not in graph or goal not in graph:
        return []

    # Coordinates of stations for heuristic
    coords = {
        "Kanpur": (26.4499, 80.3319),
        "NDLS": (28.6139, 77.2090),
        "Agra": (27.1767, 78.0081),
        "Lucknow": (26.8467, 80.9462),
        "Aligarh": (27.8974, 78.0880)
    }

    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while frontier:
        _, current = heapq.heappop(frontier)

        if current == goal:
            break

        for next_node in graph.get(current, []):
            # mock distance weight 1
            new_cost = cost_so_far[current] + 1
            if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                cost_so_far[next_node] = new_cost
                priority = new_cost + heuristic(coords.get(next_node, (0,0)), coords.get(goal, (0,0)))
                heapq.heappush(frontier, (priority, next_node))
                came_from[next_node] = current

    if goal not in came_from:
        return []

    path = []
    current = goal
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()
    return path

async def reroute_node(state: AgentState) -> dict:
    try:
        await log_agent("reroute_node", "[RAILMIND] Checking and resolving rerouting options with A*...")

        # Mock rail network graph
        rail_graph = {
            "Kanpur": ["Lucknow", "Agra"],
            "Lucknow": ["Kanpur"],
            "Agra": ["Kanpur", "Aligarh"],
            "Aligarh": ["Agra", "NDLS"],
            "NDLS": ["Aligarh"]
        }

        reroute_plan = "Proceed on current path."

        anomalies = state.get("anomalies", [])
        if anomalies:
            train = anomalies[0]
            current_station = train.get("current_station", train.get("location", "Kanpur"))
            # Just an example target
            target = "NDLS"

            if current_station in rail_graph and target in rail_graph:
                path = await a_star_search(current_station, target, rail_graph)
                if path:
                    reroute_plan = f"A* Reroute computed: {' -> '.join(path)}"
                else:
                    reroute_plan = "No alternate A* path found."
            else:
                claude_json = state.get("claude_reasoning", "{}")
                try:
                    claude_response = json.loads(claude_json)
                    reroute_plan = claude_response.get("reroute_plan", "Fallback reroute generated.")
                except:
                    reroute_plan = "Fallback reroute generated."

        return {"reroute_plan": reroute_plan, "last_node_executed": "reroute_node"}
    except Exception as e:
        logger.error(f"Error in reroute_node: {e}")
        await log_agent("reroute_node", f"[RAILMIND] [ERROR] Reroute node failed: {e}")
        return {"error_vector": f"Reroute failed: {str(e)}"}

async def coordination_node(state: AgentState) -> dict:
    try:
        await log_agent("coordination_node", "[RAILMIND] Initiating department task dispatches...")
        claude_json = state.get("claude_reasoning", "{}")
        try:
            claude_response = json.loads(claude_json)
        except Exception as e:
            logger.error(f"Error parsing Claude reasoning JSON in coordination_node: {e}")
            claude_response = {}

        anomalies = state.get("anomalies", [])
        
        # Calculate highest severity from anomalies
        severity_rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        highest_severity = "low"
        highest_rank = 0
        for anomaly in anomalies:
            sev = anomaly.get("severity", "low").lower()
            rank = severity_rank.get(sev, 1)
            if rank > highest_rank:
                highest_rank = rank
                highest_severity = sev

        has_critical = any(anomaly.get("severity", "").lower() == "critical" for anomaly in anomalies)
        operations_urgency = "high" if has_critical else "medium"

        maintenance_task: DepartmentTask = {
            "department": "maintenance",
            "task_description": claude_response.get("maintenance_task", "Inspect signals and tracks."),
            "urgency": highest_severity,
            "action_required": "Dispatch repair team immediately"
        }

        operations_task: DepartmentTask = {
            "department": "operations",
            "task_description": claude_response.get("operations_task", "Coordinate slot changes and schedules."),
            "urgency": operations_urgency,
            "action_required": "Execute rerouting plan"
        }

        station_manager_task: DepartmentTask = {
            "department": "station_manager",
            "task_description": claude_response.get("station_manager_task", "Broadcast announcement on platform boards."),
            "urgency": "high",
            "action_required": "Make passenger announcement + update platform boards"
        }

        department_tasks = [maintenance_task, operations_task, station_manager_task]

        # Save to MongoDB
        incident_uuid = str(uuid4())
        mongo_tasks = []
        for task in department_tasks:
            mongo_tasks.append({
                "incident_id": incident_uuid,
                "department": task["department"],
                "task_description": task["task_description"],
                "urgency": task["urgency"],
                "action_required": task["action_required"],
                "status": "pending",
                "timestamp": datetime.utcnow()
            })

        try:
            await db_client.insert_department_tasks(mongo_tasks)
        except Exception as e:
            logger.warning(f"Failed to save department tasks to MongoDB: {e}")

        await log_agent("coordination_node", "[RAILMIND] Dispatched tasks to 3 departments simultaneously")
        return {"department_tasks": department_tasks, "last_node_executed": "coordination_node"}
    except Exception as e:
        logger.error(f"Error in coordination_node: {e}")
        await log_agent("coordination_node", f"[RAILMIND] [ERROR] Coordination node failed: {e}")
        return {"error_vector": f"Coordination failed: {str(e)}"}

async def alert_node(state: AgentState) -> dict:
    try:
        await log_agent("alert_node", "[RAILMIND] Sending Twilio notifications...")
        m_phone = os.getenv("MAINTENANCE_PHONE", "+1234567891")
        o_phone = os.getenv("OPERATIONS_PHONE", "+1234567892")
        s_phone = os.getenv("STATION_PHONE", "+1234567893")
        p_phone = os.getenv("DEMO_PASSENGER_PHONE", "+1234567894")

        phone_map = {
            "maintenance": m_phone,
            "operations": o_phone,
            "station_manager": s_phone
        }

        tasks = state.get("department_tasks", [])
        sent_sms = []

        for task in tasks:
            dept = task.get("department", "")
            desc = task.get("task_description", "")
            urg = task.get("urgency", "medium")

            to_phone = phone_map.get(dept)
            if to_phone:
                message_body = f"[RailMind Alert] {dept.upper()}: {desc[:120]}... Urgency: {urg}"
                try:
                    sid = await twilio_client.send_incident_alert(to_phone, message_body)
                    if sid:
                        sent_sms.append(sid)
                except Exception as e:
                    logger.error(f"Error sending SMS to {dept}: {e}")

        # Send passenger SMS
        claude_json = state.get("claude_reasoning", "{}")
        try:
            claude_response = json.loads(claude_json)
        except Exception:
            claude_response = {}

        pass_sms = claude_response.get("passenger_sms")
        if pass_sms and p_phone:
            try:
                sid = await twilio_client.send_incident_alert(p_phone, pass_sms[:160])
                if sid:
                    sent_sms.append(sid)
            except Exception as e:
                logger.error(f"Error sending passenger SMS: {e}")

        await log_agent("alert_node", f"[RAILMIND] SMS alerts sent to {len(sent_sms)} recipients")
        return {"sms_alerts_sent": sent_sms, "last_node_executed": "alert_node"}
    except Exception as e:
        logger.error(f"Error in alert_node: {e}")
        await log_agent("alert_node", f"[RAILMIND] [ERROR] Alert node failed: {e}")
        return {"error_vector": f"Alert failed: {str(e)}"}

async def save_incident_if_not_duplicate(db, incident):
    # Check last 5 minutes for same train number
    from datetime import datetime, timedelta
    five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
    
    existing = await db.incidents.find_one({
        "train_number": incident["train_number"],
        "timestamp": {
            "$gt": five_mins_ago.isoformat()
        }
    })
    
    if existing:
        print(f"[RAILMIND] Skipping duplicate incident for "
              f"train {incident['train_number']} "
              f"(last logged {existing['timestamp']})")
        return False
    
    # Make a copy to avoid inserting _id of type ObjectId in-place into the original dictionary
    incident_copy = incident.copy()
    await db.incidents.insert_one(incident_copy)
    print(f"[RAILMIND] New incident saved: "
          f"{incident['incident_title']}")
    return True

async def report_node(state: AgentState) -> dict:
    try:
        await log_agent("report_node", "[RAILMIND] Broadcasting operations report...")
        
        anomalies = state.get("anomalies", [])
        if not anomalies:
            return {"last_node_executed": "report_node"}
            
        anomaly = anomalies[0]
        train_number = anomaly.get("train_number", "Unknown")
        train_name = anomaly.get("train_name", "Unknown")
        current_station = anomaly.get("current_station") or anomaly.get("location") or "Unknown"
        delay_minutes = anomaly.get("delay_minutes", 0)
        severity = anomaly.get("severity", "medium")

        claude_json = state.get("claude_reasoning", "{}")
        try:
            claude_response = json.loads(claude_json)
        except Exception:
            claude_response = {}

        incident_id = str(uuid4())
        
        incident_report = {
            "incident_id": incident_id,
            "timestamp": datetime.utcnow().isoformat(),
            "train_number": train_number,
            "train_name": train_name,
            "incident_title": claude_response.get("incident_title") or f"{train_number} {train_name} delayed {delay_minutes}min at {current_station}",
            "current_station": current_station,
            "delay_minutes": delay_minutes,
            "severity": severity,
            "situation_summary": claude_response.get("situation_summary") or f"Train {train_number} {train_name} is running {delay_minutes} minutes behind schedule at {current_station}.",
            "reroute_plan": claude_response.get("reroute_plan") or "Redirect affected trains via alternate route.",
            "maintenance_task": claude_response.get("maintenance_task") or "Inspect signaling hardware.",
            "operations_task": claude_response.get("operations_task") or "Execute scheduling adjustments.",
            "station_manager_task": claude_response.get("station_manager_task") or "Broadcast delay announcements.",
            "passenger_sms": claude_response.get("passenger_sms") or "Check platform screens for status updates.",
            "resolution_status": "pending",
            "departments_notified": ["maintenance", "operations", "station_manager"],
            "sms_sent": len(state.get("sms_alerts_sent", []))
        }

        # Check for duplicates in last 5 minutes before saving (ISSUE 2)
        saved = await save_incident_if_not_duplicate(db_client.db, incident_report)
        if saved:
            # Broadcast via WebSocket
            try:
                await websocket_manager.broadcast(json.dumps({
                    "type": "INCIDENT_UPDATE",
                    "data": incident_report
                }))
            except Exception as e:
                logger.error(f"Failed to broadcast incident update: {e}")

            await log_agent("report_node", f"[RAILMIND] Incident report #{incident_id[:8]} logged and broadcast")
        else:
            await log_agent("report_node", f"[RAILMIND] Duplicate incident check: train {train_number} has an active report in the last 5 minutes. Skipping DB insertion and broadcast.")

        # Mark this train as recently processed in state
        processed_trains = state.get("processed_trains", [])
        processed_trains.append(anomaly["train_number"])

        import asyncio
        await log_agent("report_node", "[RAILMIND] Sleeping for 10 seconds before next iteration...")
        await asyncio.sleep(10)

        return {
            "processed_trains": processed_trains,
            "anomalies": [],
            "department_tasks": [{"department": "CLEAR"}],
            "sms_alerts_sent": ["CLEAR"],
            "loop_count": state.get("loop_count", 0) + 1,
            "incident_report": str(incident_report),
            "last_node_executed": "report_node"
        }
    except Exception as e:
        logger.error(f"Error in report_node: {e}")
        await log_agent("report_node", f"[RAILMIND] [ERROR] Report node failed: {e}")
        return {"error_vector": f"Report failed: {str(e)}"}
