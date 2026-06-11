import os
import json
import logging
import time
from dotenv import load_dotenv
from typing import List
from uuid import uuid4
from datetime import datetime, timezone
from ..services.ai_service import reason_with_ai
from .state import AgentState, TrainAnomaly, DepartmentTask
from ..services.db_client import db_client
from ..services.railways_api import get_cancelled_trains, mock_train_data, RailwaysAPIClient, get_multiple_trains
from ..services.twilio_service import TwilioSMSClient
from ..api.websocket import websocket_manager
from backend.utils.logger import get_json_logger
from backend.utils.metrics import LANGGRAPH_NODE_LATENCY, LANGGRAPH_ERROR_COUNT

logger = get_json_logger(__name__)

from backend.config import settings

# Ensure env variables are loaded before configuration
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)
api_key = settings.railways_api_key
railways_client = RailwaysAPIClient(api_key=api_key)

twilio_sid = settings.twilio_account_sid
twilio_token = settings.twilio_auth_token
twilio_from = settings.twilio_phone_number
twilio_client = TwilioSMSClient(account_sid=twilio_sid, auth_token=twilio_token, from_number=twilio_from)

# Shared log assistant that prints logs and broadcasts AGENT_LOG WebSocket events (ISSUE 4)
async def log_agent(node_name: str, message: str):
    logger.info(message, extra={"node_name": node_name})
    try:
        await websocket_manager.broadcast(json.dumps({
            "type": "AGENT_LOG",
            "message": f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] [{node_name}] {message}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
    except Exception as e:
        logger.error(f"Failed to broadcast AGENT_LOG message: {e}")

async def ingest_node(state: AgentState) -> AgentState:
    start_time_metric = time.time()
    try:
        await log_agent("ingest_node", "[RAILMIND] Ingesting live train status from API feeds...")
        train_numbers = [
            "12301", "12951", "12001", "12259", "12565",
            "11057", "12627", "12625", "12621", "12615",
            "12309", "12721", "12229", "12311", "12641"
        ]
        
        start_time = time.time()
        
        client = railways_client
        
        # Determine if we should mock based on actual env vars, not just string presence
        import os
        is_demo = os.getenv("DEMO_MODE", "false").lower() == "true"
        valid_api_key = False
        r_key = os.getenv("RAILWAYS_API_KEY")
        if r_key and r_key not in ["", "your_railways_api_key_here", "mock_key"]:
            valid_api_key = True

        rapid_key = os.getenv("RAPIDAPI_KEY")
        if rapid_key and rapid_key not in ["", "your_key_here"]:
            valid_api_key = True

        if not valid_api_key:
            print("[RAILMIND] WARNING: Railways API returned no data, check RAILWAYS_API_KEY in .env")
            await log_agent("ingest_node", "[RAILMIND] WARNING: Railways API returned no data, check RAILWAYS_API_KEY in .env")
            if is_demo:
                await log_agent("ingest_node", "[RAILMIND] Using fallback mock data for testing")
                live_trains = client.mock_train_data()
            else:
                live_trains = []
        else:
            await log_agent("ingest_node", f"[RAILMIND] Calling Railways API for {len(train_numbers)} trains...")
            live_trains = await client.get_multiple_trains(train_numbers)

            latency = int((time.time() - start_time) * 1000)
            state["railways_latency_ms"] = latency
            state["last_api_call"] = datetime.now(timezone.utc).strftime('%H:%M:%S UTC')

            if not live_trains:
                if is_demo:
                    await log_agent("ingest_node", "[RAILMIND] Using fallback mock data for testing")
                    live_trains = client.mock_train_data()

        print(f"[RAILMIND] API returned {len(live_trains)} trains")
        if live_trains:
            print(f"[RAILMIND] Sample: {live_trains[0]}")
            
        state["raw_train_data"] = live_trains
        await log_agent("ingest_node", f"[RAILMIND] Ingested {len(live_trains)} trains")
    except Exception as e:
        LANGGRAPH_ERROR_COUNT.labels(node_name="ingest_node").inc()
        logger.error(f"Error in ingest_node: {e}")
        await log_agent("ingest_node", f"[RAILMIND] [ERROR] Ingest node failed: {e}")
    finally:
        LANGGRAPH_NODE_LATENCY.labels(node_name="ingest_node").observe(time.time() - start_time_metric)
    return state

async def detect_node(state: AgentState) -> AgentState:
    start_time_metric = time.time()
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
            delay = train.get("delay_minutes", 0)
            status = train.get("status", "unknown")
            current_station = train.get("current_station", "Unknown")

            if status.lower() == "delayed" and delay > 30:
                severity = "medium"
                if delay > 60:
                    severity = "high"
                if delay > 120:
                    severity = "critical"
                    
                anomalies.append({
                    "train_number": train_num,
                    "train_name": train_name,
                    "delay_minutes": delay,
                    "location": current_station,
                    "current_station": current_station,
                    "issue_type": "Schedule Delay",
                    "severity": severity,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": train.get("source", "Unknown"),
                    "destination": train.get("destination", "Unknown")
                })

            # Additional dummy checks for route deviation
            if train.get("passenger_load", "").lower() == "overcrowded" and delay > 15:
                # Upgrading severity
                anomalies.append({
                    "train_number": train_num,
                    "train_name": train_name,
                    "delay_minutes": delay,
                    "location": current_station,
                    "current_station": current_station,
                    "issue_type": "Congestion Delay",
                    "severity": "high",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": train.get("source", "Unknown"),
                    "destination": train.get("destination", "Unknown")
                })

        state["anomalies"] = anomalies

        if anomalies:
            await log_agent("detect_node", f"[RAILMIND] [WARNING] Detected {len(anomalies)} anomalies")
            state["should_continue"] = True
        else:
            await log_agent("detect_node", "[RAILMIND] [OK] All trains nominal")
            state["should_continue"] = False
    except Exception as e:
        LANGGRAPH_ERROR_COUNT.labels(node_name="detect_node").inc()
        logger.error(f"Error in detect_node: {e}")
        await log_agent("detect_node", f"[RAILMIND] [ERROR] Detect node failed: {e}")
    finally:
        LANGGRAPH_NODE_LATENCY.labels(node_name="detect_node").observe(time.time() - start_time_metric)
    return state

async def reason_node(state: AgentState) -> AgentState:
    start_time_metric = time.time()
    try:
        anomalies = state.get("anomalies", [])
        if not anomalies:
            state["claude_reasoning"] = "{}"
            state["reroute_plan"] = None
            state["incident_report"] = None
            await log_agent("reason_node", "[RAILMIND] [OK] All trains nominal, skipping AI reasoning")
            return state

        await log_agent("reason_node", f"[RAILMIND] Contacting AI to reason about {len(anomalies)} anomalies...")
        
        start_time = time.time()
        
        result = await reason_with_ai(anomalies)
        
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
        LANGGRAPH_ERROR_COUNT.labels(node_name="reason_node").inc()
        logger.error(f"Error in reason_node: {e}")
        await log_agent("reason_node", f"[RAILMIND] [ERROR] Reason node failed: {e}")
    finally:
        LANGGRAPH_NODE_LATENCY.labels(node_name="reason_node").observe(time.time() - start_time_metric)
    return state

async def reroute_node(state: AgentState) -> AgentState:
    start_time_metric = time.time()
    try:
        await log_agent("reroute_node", "[RAILMIND] Checking and resolving rerouting options...")
    except Exception as e:
        LANGGRAPH_ERROR_COUNT.labels(node_name="reroute_node").inc()
        logger.error(f"Error in reroute_node: {e}")
        await log_agent("reroute_node", f"[RAILMIND] [ERROR] Reroute node failed: {e}")
    finally:
        LANGGRAPH_NODE_LATENCY.labels(node_name="reroute_node").observe(time.time() - start_time_metric)
    return state

async def coordination_node(state: AgentState) -> AgentState:
    start_time_metric = time.time()
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
                "timestamp": datetime.now(timezone.utc)
            })

        try:
            await db_client.insert_department_tasks(mongo_tasks)
        except Exception as e:
            logger.warning(f"Failed to save department tasks to MongoDB: {e}")

        await log_agent("coordination_node", "[RAILMIND] Dispatched tasks to 3 departments simultaneously")
    except Exception as e:
        LANGGRAPH_ERROR_COUNT.labels(node_name="coordination_node").inc()
        logger.error(f"Error in coordination_node: {e}")
        await log_agent("coordination_node", f"[RAILMIND] [ERROR] Coordination node failed: {e}")
    finally:
        LANGGRAPH_NODE_LATENCY.labels(node_name="coordination_node").observe(time.time() - start_time_metric)
    return state

async def alert_node(state: AgentState) -> AgentState:
    start_time_metric = time.time()
    try:
        await log_agent("alert_node", "[RAILMIND] Sending Twilio notifications...")
        m_phone = settings.maintenance_phone
        o_phone = settings.operations_phone
        s_phone = settings.station_phone
        p_phone = settings.demo_passenger_phone

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
        LANGGRAPH_ERROR_COUNT.labels(node_name="alert_node").inc()
        logger.error(f"Error in alert_node: {e}")
        await log_agent("alert_node", f"[RAILMIND] [ERROR] Alert node failed: {e}")
    finally:
        LANGGRAPH_NODE_LATENCY.labels(node_name="alert_node").observe(time.time() - start_time_metric)
    return state

async def save_incident_if_not_duplicate(db, incident):
    # Check last 5 minutes for same train number
    from datetime import datetime, timedelta, timezone
    five_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
    
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
    start_time_metric = time.time()
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
        state["anomalies"] = []
        state["department_tasks"] = []
        state["sms_alerts_sent"] = []
        state["loop_count"] = state.get("loop_count", 0) + 1

        import asyncio
        await log_agent("report_node", "[RAILMIND] Sleeping for 10 seconds before next iteration...")
        await asyncio.sleep(10)
    except Exception as e:
        LANGGRAPH_ERROR_COUNT.labels(node_name="report_node").inc()
        logger.error(f"Error in report_node: {e}")
        await log_agent("report_node", f"[RAILMIND] [ERROR] Report node failed: {e}")
    finally:
        LANGGRAPH_NODE_LATENCY.labels(node_name="report_node").observe(time.time() - start_time_metric)
    return state
