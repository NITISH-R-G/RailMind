import os
import json
import logging
import traceback
from dotenv import load_dotenv
from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime
from ..services.ai_service import reason_with_ai
from .state import AgentState, TrainAnomaly, DepartmentTask
from ..services.db_client import db_client
from ..services.railways_api import get_live_train_status, get_cancelled_trains, mock_train_data, RailwaysAPIClient, get_multiple_trains
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

async def ingest_node(state: AgentState) -> AgentState:
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
        
        state["raw_train_data"] = live_trains
        await log_agent("ingest_node", f"[RAILMIND] Ingested {len(live_trains)} trains")
    except Exception as e:
        logger.error(f"Error in ingest_node: {e}")
        await log_agent("ingest_node", f"[RAILMIND] [ERROR] Ingestion failed: {e}")
    return state

async def detect_node(state: AgentState) -> AgentState:
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
                
        state["anomalies"] = anomalies
        n = len(anomalies)
        if n > 0:
            await log_agent("detect_node", f"[RAILMIND] [WARNING] Detected {n} anomalies")
            state["should_continue"] = True
        else:
            await log_agent("detect_node", "[RAILMIND] [OK] All trains nominal")
            state["should_continue"] = False
    except Exception as e:
        logger.error(f"Error in detect_node: {e}")
        await log_agent("detect_node", f"[RAILMIND] [ERROR] Detect node failed: {e}")
    return state

async def reason_node(state: AgentState) -> AgentState:
    try:
        anomalies = state.get("anomalies", [])
        if not anomalies:
            state["claude_reasoning"] = "{}"
            state["reroute_plan"] = None
            state["incident_report"] = None
            await log_agent("reason_node", "[RAILMIND] [OK] All trains nominal, skipping AI reasoning")
            return state

        await log_agent("reason_node", f"[RAILMIND] Contacting AI to reason about {len(anomalies)} anomalies...")
        
        import time
        start_time = time.time()
        
        errors = state.get("errors", [])
        try:
            result = await reason_with_ai(anomalies, errors)
        except Exception as ai_e:
            logger.exception("Reasoning API failed")
            result = {}
        
        latency = int((time.time() - start_time) * 1000)
        state["ai_latency_ms"] = latency
        
        if result:
            state["claude_reasoning"] = json.dumps(result)
            state["reroute_plan"] = result.get("reroute_plan")
            state["incident_report"] = result.get("incident_summary")
            await log_agent("reason_node", f"[RAILMIND] AI reasoning: {result.get('situation_summary')}")
        else:
            state["claude_reasoning"] = "{}"
            await log_agent("reason_node", "[RAILMIND] AI reasoning failed — using defaults")
    except Exception as e:
        logger.error(f"Error in reason_node: {e}")
        await log_agent("reason_node", f"[RAILMIND] [ERROR] Reason node failed: {e}")
    return state

from .routing import dijkstra_route_discovery

async def reroute_node(state: AgentState) -> AgentState:
    try:
        await log_agent("reroute_node", "[RAILMIND] Checking and resolving rerouting options...")
        anomalies = state.get("anomalies", [])
        if anomalies:
            anomaly = anomalies[0]
            start_station = anomaly.get("current_station") or anomaly.get("location") or ""
            target_station = anomaly.get("destination", "")

            # Use fallback destination if none provided
            if start_station == "Kanpur Central" and not target_station:
                target_station = "Varanasi"

            if start_station and target_station:
                result = dijkstra_route_discovery(start_station, target_station)
                if result["status"] == "Success":
                    route_str = " -> ".join(result["route"])
                    await log_agent("reroute_node", f"[RAILMIND] Route found: {route_str}")
                    return {"reroute_plan": f"Dijkstra routed: {route_str} (ETA {result['cost']} mins)"}
                else:
                    status_msg = result.get("status", "Unknown status")
                    await log_agent("reroute_node", f"[RAILMIND] No viable detour found: {status_msg}")
                    state["reroute_plan"] = f"No reroute available: {status_msg}"
    except Exception as e:
        logger.error(f"Error in reroute_node: {e}")
        await log_agent("reroute_node", f"[RAILMIND] [ERROR] Reroute node failed: {e}")
    return {}

async def coordination_node(state: AgentState) -> AgentState:
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
                if highest_rank == 4:
                    break

        has_critical = (highest_severity == "critical")
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
        # Instead of replacing, we return it to let Annotated[..., operator.add] handle it, or we append directly
        # LangGraph state update dictionary:
        state["department_tasks"] = department_tasks

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
    except Exception as e:
        logger.error(f"Error in coordination_node: {e}")
        await log_agent("coordination_node", f"[RAILMIND] [ERROR] Coordination node failed: {e}")
    return state

async def alert_node(state: AgentState) -> AgentState:
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

        state["sms_alerts_sent"] = sent_sms
        await log_agent("alert_node", f"[RAILMIND] SMS alerts sent to {len(sent_sms)} recipients")
    except Exception as e:
        logger.error(f"Error in alert_node: {e}")
        await log_agent("alert_node", f"[RAILMIND] [ERROR] Alert node failed: {e}")
    return state

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

async def report_node(state: AgentState) -> AgentState:
    try:
        await log_agent("report_node", "[RAILMIND] Broadcasting operations report...")
        
        anomalies = state.get("anomalies", [])
        if not anomalies:
            return state
            
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
        state["processed_trains"] = processed_trains

        # Reset state fields
        # For LangGraph annotated reducers, we can't easily clear lists by passing [] if it appends.
        # But we can let the next graph invocation use a fresh initial state.
        # So we just mark the next node.
        state["loop_count"] = state.get("loop_count", 0) + 1
        state["next_node"] = "END"

        # We don't sleep here in a real LangGraph flow, the streaming app handles it or the caller.
        await log_agent("report_node", "[RAILMIND] Report node complete. Supervisor will transition to END.")

    except Exception as e:
        logger.error(f"Error in report_node: {e}")
        await log_agent("report_node", f"[RAILMIND] [ERROR] Report node failed: {e}")
    return state

async def supervisor_node(state: AgentState) -> dict:
    try:
        await log_agent("supervisor_node", "[RAILMIND] Supervisor evaluating graph state...")

        anomalies = state.get("anomalies", [])
        if not anomalies:
            return {"next_node": "END"}

        # If reasoning hasn't happened or failed to produce plan
        if not state.get("claude_reasoning") or state.get("claude_reasoning") == "{}":
            # For offline testing where Reason API throws Auth Error and falls back to {}
            # we don't want an infinite loop.
            if getattr(state, "get", lambda k,d: d)("ai_latency_ms", -1) > 0:
                 # AI ran but returned nothing. Stop ping-ponging.
                 return {"next_node": "END"}
            return {"next_node": "reason_node"}

        # Self correction loop check
        try:
            reasoning = json.loads(state.get("claude_reasoning", "{}"))
            maintenance = reasoning.get("maintenance_task", "")
            if "Kanpur" in maintenance and "restricted" in maintenance.lower():
                 # Mock conflict logic
                 await log_agent("supervisor_node", "[RAILMIND] [WARNING] Conflict detected in maintenance task. Re-routing to Reasoner.")
                 if "errors" not in state or state["errors"] is None:
                     state["errors"] = []
                 state["errors"].append("Maintenance task conflicts with active line configurations at Kanpur.")
                 state["claude_reasoning"] = "{}" # clear to force re-reason
                 state["next_node"] = "reason_node"
                 return state
        except json.JSONDecodeError as e:
            logger.warning("JSON parse failed: %s", e)
        except Exception:
            logger.exception("Unexpected error in supervisor self-correction logic")
            raise

        if not state.get("reroute_plan"):
             state["next_node"] = "reroute_node"
             return state

        # If tasks not generated
        if not state.get("department_tasks"):
            state["next_node"] = "coordination_node"
            return state

        # If alerts not sent
        if not state.get("sms_alerts_sent") and len(state.get("department_tasks", [])) > 0:
            state["next_node"] = "alert_node"
            return state

        # Otherwise report and finish
        state["next_node"] = "report_node"

    except Exception as e:
         logger.exception("Error in supervisor_node")
         tb = traceback.format_exc()
         await log_agent("supervisor_node", f"[RAILMIND] [ERROR] Supervisor node failed: {e}\n{tb}")
         state["next_node"] = "END"
    return state
