import re

with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# I see a duplicated report_node or partially duplicated one around line 1226. Let's inspect the `except Exception as e:` block.
# Look at this:
#  1222	    except Exception as e:
#  1223	        logger.exception(ERR_OCCURRED_MSG, e)
#  1224	        await log_agent("report_node", f"[RAILMIND] [ERROR] Report node failed: {e}")
#  1225	        return {"last_node_executed": "report_node", "errors": [f"report error: {e}"]}
#  1226
#  1227	        anomaly = anomalies[0]
# ... and later again:
#  1383	    except Exception as e:
#  1384	        logger.exception(ERR_OCCURRED_MSG, e)
#  1385	        await log_agent("report_node", f"[RAILMIND] [ERROR] Report node failed: {e}")
#  1386	    return {}
# This indicates that the regex replacement duplicated parts of `report_node`.

# Let's cleanly replace the entire report_node. We'll find its start and delete it up to supervisor_node.
start = content.find("async def report_node(state: AgentState) -> dict:")
end = content.find("async def supervisor_node(state: AgentState) -> dict:")

report_node_clean = '''async def report_node(state: AgentState) -> dict:
    try:
        await log_agent("report_node", "[RAILMIND] Broadcasting operations report...")
        diff = {"last_node_executed": "report_node"}
        anomalies = state.get("anomalies", [])
        if not anomalies:
            return diff

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

        confidence_score = None
        reasoning_steps = []
        situation_summary = ""

        maintenance_task = DEFAULT_MAINT_TASK
        operations_task = DEFAULT_OPS_TASK
        station_manager_task = DEFAULT_STATION_TASK
        passenger_sms = DEFAULT_SMS_TASK

        if "perception" in claude_response and "decision" in claude_response:
            perception = claude_response["perception"]
            decision = claude_response["decision"]
            situation_summary = perception.get("situation", "")
            confidence_score = int(decision.get("confidence", 0) * 100) if decision.get("confidence") is not None else None

            actions = decision.get("actions", [])
            for action in actions:
                tool = action.get("tool")
                reason = action.get("reason", "")
                params = action.get("params", {})
                if tool == "alert_department":
                    dept = params.get("dept", "").lower()
                    msg = params.get("message", reason)
                    if "maintenance" in dept:
                        maintenance_task = msg
                    elif "operations" in dept:
                        operations_task = msg
                    elif "station" in dept or "manager" in dept:
                        station_manager_task = msg
                elif tool == "send_passenger_alert":
                    passenger_sms = params.get("message", reason)
                elif tool == "reroute_train":
                    operations_task = f"Reroute train {params.get('train_no')} via {params.get('via_station')}: {reason}"

            reasoning_steps = [
                f"PERCEIVE: {perception.get('situation')}",
                f"ASSESS: Corridor = {perception.get('affected_corridor')}, Cascade risk = {perception.get('is_cascade')}",
                f"DECIDE: {decision.get('decision')}",
                f"ACTION SLOTS: Dispatched {len(actions)} tasks to departments"
            ]
        else:
            situation_summary = claude_response.get("situation_summary") or f"Train {train_number} {train_name} is running {delay_minutes} minutes behind schedule at {current_station}."
            maintenance_task = claude_response.get("maintenance_task") or DEFAULT_MAINT_TASK
            operations_task = claude_response.get("operations_task") or DEFAULT_OPS_TASK
            station_manager_task = claude_response.get("station_manager_task") or DEFAULT_STATION_TASK
            passenger_sms = claude_response.get("passenger_sms") or DEFAULT_SMS_TASK
            confidence_score = claude_response.get("confidence_score")
            reasoning_steps = claude_response.get("reasoning_steps") or []

        cascade_title = None
        cascade_info = await detect_cascade(anomalies)
        if cascade_info.get("is_cascade"):
            cascade_title = f"NETWORK EVENT: {cascade_info['corridor']} Corridor Disruption"

        incident_id = str(uuid4())

        pred = state.get("prediction", {})
        worst_case = pred.get("worst_case")
        if not worst_case:
            at_risk_count = len(pred.get("at_risk_trains", [])) or 3
            future_time = "14:30"
            try:
                ts_str = state.get("last_api_call") or datetime.now(timezone.utc).isoformat()
                from datetime import timedelta
                dt = datetime.fromisoformat(str(ts_str))
                future_dt = dt + timedelta(minutes=30)
                future_time = future_dt.strftime("%H:%M")
            except Exception:
                pass
            worst_case = f"If unresolved: {at_risk_count} more trains will be delayed by {future_time}"

        incident_report = {
            "incident_id": incident_id,
            "loop_created": state.get("loop_count", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "train_number": train_number,
            "train_name": train_name,
            "incident_title": cascade_title or f"{train_number} {train_name} delayed {delay_minutes}min at {current_station}",
            "current_station": current_station,
            "delay_minutes": delay_minutes,
            "severity": severity,
            "situation_summary": situation_summary,
            "reroute_plan": state.get("reroute_plan") or "Redirect affected trains via alternate route.",
            "maintenance_task": maintenance_task,
            "operations_task": operations_task,
            "station_manager_task": station_manager_task,
            "passenger_sms": passenger_sms,
            "resolution_status": "pending",
            "departments_notified": ["maintenance", "operations", "station_manager"],
            "sms_sent": len(state.get("sms_alerts_sent", [])),
            "detour_route": state.get("detour_route") or [],
            "confidence_score": confidence_score,
            "reasoning_steps": reasoning_steps,
            "passenger_impact": state.get("decision", {}).get("passenger_impact") or DEFAULT_PASSENGER_IMPACT,
            "prediction": worst_case,
            "memory_used": state.get("memory_used")
        }

        saved = await save_incident_if_not_duplicate(incident_report)
        if saved:
            try:
                await websocket_manager.broadcast(json.dumps({
                    "type": "INCIDENT_UPDATE",
                    "data": incident_report
                }))
            except Exception as e:
                logger.exception(ERR_BROADCAST_MSG, e)

            await log_agent("LOGGED", f"Incident #RM-{incident_id[:3].upper()} saved to database")
        else:
            await log_agent("report_node", f"[RAILMIND] Duplicate incident check: train {train_number} has an active report in the last 5 minutes. Skipping DB insertion and broadcast.")

        processed_trains = state.get("processed_trains", [])
        processed_trains.append(anomaly["train_number"])

        diff["loop_count"] = state.get("loop_count", 0) + 1
        diff["next_node"] = "END"

        passengers = state.get("decision", {}).get("passenger_impact", DEFAULT_PASSENGER_IMPACT)
        if isinstance(passengers, str):
            passengers_str = passengers
        else:
            passengers_str = f"{passengers} passengers affected"
        await log_agent("COMPLETE", f"Loop {diff['loop_count']} done. {passengers_str}. Next scan: 30 seconds.")

        diff.update({
            "processed_trains": processed_trains,
            "anomalies": ["CLEAR"],
            "sms_alerts_sent": ["CLEAR"],
            "department_tasks": ["CLEAR"],
            "claude_reasoning": "{}"
        })
        return diff

    except Exception as e:
        logger.exception(ERR_OCCURRED_MSG, e)
        await log_agent("report_node", f"[RAILMIND] [ERROR] Report node failed: {e}")
        return {"last_node_executed": "report_node", "errors": [f"report error: {e}"]}

'''

content = content[:start] + report_node_clean + content[end:]

with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
