import re

with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# For ingest_node: (160)
ingest_node_new = """async def _fetch_train_data(train_numbers):
    import time
    start_time = time.time()
    print(f"[RAILMIND] Calling Railways API for {len(train_numbers)} trains...")
    results = await railways_client.get_multiple_trains(train_numbers)

    train_results = []
    for tn in train_numbers:
        r = next((x for x in results if x.get("train_number") == tn), None)
        if not r:
            from ..services.railways_api import get_mock_rapidapi_train, parse_rapidapi_train_for_agent
            mock_data = get_mock_rapidapi_train(tn)
            parsed_mock = parse_rapidapi_train_for_agent(mock_data, tn)
            if parsed_mock:
                train_results.append(parsed_mock)
        else:
            train_results.append(r)
    return train_results, int((time.time() - start_time) * 1000)

async def _get_live_trains(results):
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
    return live_trains

async def ingest_node(state: AgentState) -> dict:
    try:
        await log_agent("SCANNING", "Polling 15 trains on Indian Railways...")
        if state.get("raw_train_data"):
            live_trains = state["raw_train_data"]
        else:
            train_numbers = state.get("target_trains") or ["12301", "12951", "12001", "12259", "12565", "11057", "12627", "12625", "12621", "12615", "12309", "12721", "12229", "12311", "12641", "12438", "ICE"]

            results, latency = await _fetch_train_data(train_numbers)
            state["last_api_call"] = datetime.utcnow().isoformat()
            state["railways_latency_ms"] = latency

            if not results:
                await log_agent("ingest_node", "[RAILMIND] WARNING: Railways API returned no data, check RAILWAYS_API_KEY in .env. Using mock fallback.")
                results = mock_train_data()

            live_trains = await _get_live_trains(results)

        for train in live_trains:
            await websocket_manager.broadcast(json.dumps({"type": "TRAIN_UPDATE", "data": train}))

        await log_agent("ingest_node", f"[RAILMIND] Ingested {len(live_trains)} trains")
        return {
            "raw_train_data": live_trains,
            "last_api_call": state.get("last_api_call"),
            "railways_latency_ms": state.get("railways_latency_ms")
        }
    except Exception as e:
        logger.error(f"Error in ingest_node: {e}")
        await log_agent("ingest_node", f"[RAILMIND] [ERROR] Ingest node failed: {e}")
    return {}
"""
content = re.sub(r'async def ingest_node\(state: AgentState\) -> dict:.*?return \{\}\n(?=\nasync def detect_node)', ingest_node_new, content, flags=re.DOTALL)


# For detect_node: (224)
detect_node_new = """def _process_train_anomaly(train, simulated_type):
    train_num = train.get("train_number", "Unknown")
    train_name = train.get("train_name", "Unknown")
    location = train.get("current_station") or train.get("source") or "Unknown"
    delay = train.get("delay_minutes", 0)
    load = train.get("passenger_load")
    status = str(train.get("status") or "").lower()

    anomaly = None
    if delay > 15:
        severity = "low" if delay <= 30 else "medium" if delay <= 60 else "high" if delay <= 120 else "critical"
        anomaly = {"anomaly_type": simulated_type or "delay", "severity": severity}
    elif load == "overcrowded":
        anomaly = {"anomaly_type": simulated_type or "overcrowding", "severity": "high"}
    elif status == "cancelled":
        anomaly = {"anomaly_type": simulated_type or "cancellation", "severity": "critical", "status": "cancelled"}

    if anomaly:
        anomaly.update({
            "train_number": train_num,
            "train_name": train_name,
            "location": location,
            "delay_minutes": delay,
            "passenger_load": load,
            "current_station": train.get("current_station") or location,
            "status": anomaly.get("status", status or "delayed"),
            "source": train.get("source") or "Unknown",
            "destination": train.get("destination") or "Unknown",
            "station_code": get_station_code_from_name(train.get("current_station") or location)
        })
    return anomaly

async def detect_node(state: AgentState) -> dict:
    try:
        await log_agent("detect_node", "[RAILMIND] Running real-time anomaly detection rules...")
        anomalies: List[TrainAnomaly] = []
        raw_data = state.get("raw_train_data", [])
        processed_trains = state.get("processed_trains", [])

        simulated_types = {a.get("train_number"): a.get("anomaly_type") for a in state.get("anomalies", []) if "train_number" in a and "anomaly_type" in a}

        for train in raw_data:
            if train.get("train_number", "Unknown") in processed_trains:
                continue
            anomaly = _process_train_anomaly(train, simulated_types.get(train.get("train_number")))
            if anomaly:
                anomalies.append(anomaly)

        for a in anomalies:
            st_code = a.get("station_code") or a.get("location")[:4].upper()
            delay_text = f"{a.get('delay_minutes')}min delay" if a.get("delay_minutes") else "anomaly"
            await log_agent("DETECTED", f"Train {a['train_number']}: {delay_text} at {st_code}")

        await log_agent("CASCADE?", "Checking Delhi-Mumbai corridor...")
        cascade_info = await detect_cascade(anomalies)
        if cascade_info.get("is_cascade"):
            await log_agent("detect_node", f"[RAILMIND] [CASCADE] {cascade_info['message']}")
            for a in anomalies:
                if a.get("station_code") in cascade_info["affected_stations"]:
                    a["severity"] = "critical"
                    a["anomaly_type"] = "cascade"
            try:
                await websocket_manager.broadcast(json.dumps({
                    "type": "CASCADE_ALERT",
                    "corridor": cascade_info["corridor"],
                    "affected_stations": cascade_info["affected_stations"],
                    "message": cascade_info["message"]
                }))
            except Exception as ws_e:
                logger.error(f"Failed to broadcast CASCADE_ALERT: {ws_e}")

        n = len(anomalies)
        should_continue = n > 0
        if should_continue:
            await log_agent("detect_node", f"[RAILMIND] [WARNING] Detected {n} anomalies")
        else:
            await log_agent("detect_node", "[RAILMIND] [OK] All trains nominal")
        return {"anomalies": anomalies, "should_continue": should_continue}
    except Exception as e:
        logger.error(f"Error in detect_node: {e}")
        await log_agent("detect_node", f"[RAILMIND] [ERROR] Detect node failed: {e}")
    return {}
"""
content = re.sub(r'async def detect_node\(state: AgentState\) -> dict:.*?return \{\}\n(?=\ndef get_station_code_from_name)', detect_node_new, content, flags=re.DOTALL)


# For coordination_node: (809 -> approx 820 in new)
coordination_node_new = """def _parse_tasks(claude_response, reason=""):
    m_desc = claude_response.get("maintenance_task", "Inspect signals and tracks.")
    o_desc = claude_response.get("operations_task", "Coordinate slot changes and schedules.")
    s_desc = claude_response.get("station_manager_task", "Broadcast announcement on platform boards.")

    if "perception" in claude_response and "decision" in claude_response:
        actions = claude_response["decision"].get("actions", [])
        for action in actions:
            tool = action.get("tool")
            msg = action.get("params", {}).get("message", action.get("reason", reason))
            if tool == "alert_department":
                dept = action.get("params", {}).get("dept", "").lower()
                if "maintenance" in dept: m_desc = msg
                elif "operations" in dept: o_desc = msg
                elif "station" in dept or "manager" in dept: s_desc = msg
            elif tool == "reroute_train":
                o_desc = f"Reroute train {action.get('params', {}).get('train_no')} via {action.get('params', {}).get('via_station')}: {msg}"
    return m_desc, o_desc, s_desc

async def coordination_node(state: AgentState) -> dict:
    try:
        await log_agent("coordination_node", "[RAILMIND] Initiating department task dispatches...")
        try:
            claude_response = json.loads(state.get("claude_reasoning", "{}"))
        except Exception as e:
            logger.error(f"Error parsing Claude reasoning JSON in coordination_node: {e}")
            claude_response = {}

        severity_rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        highest_rank = max((severity_rank.get(a.get("severity", "low").lower(), 1) for a in state.get("anomalies", [])), default=1)

        m_desc, o_desc, s_desc = _parse_tasks(claude_response)

        tasks = [
            {"department": "maintenance", "task_description": m_desc, "urgency": "critical" if highest_rank == 4 else "high", "action_required": "Dispatch repair team immediately"},
            {"department": "operations", "task_description": o_desc, "urgency": "high" if highest_rank == 4 else "medium", "action_required": "Execute rerouting plan"},
            {"department": "station_manager", "task_description": s_desc, "urgency": "high", "action_required": "Make passenger announcement + update platform boards"}
        ]

        incident_uuid = str(uuid4())
        try:
            await db_client.insert_department_tasks([{**t, "incident_id": incident_uuid, "status": "pending", "timestamp": datetime.utcnow()} for t in tasks])
        except Exception as e:
            logger.warning(f"Failed to save department tasks to MongoDB: {e}")

        await log_agent("coordination_node", "[RAILMIND] Dispatched tasks to 3 departments simultaneously")
        return {"department_tasks": tasks}
    except Exception as e:
        logger.error(f"Error in coordination_node: {e}")
        await log_agent("coordination_node", f"[RAILMIND] [ERROR] Coordination node failed: {e}")
    return {}
"""
content = re.sub(r'async def coordination_node\(state: AgentState\) -> dict:.*?return \{\}\n(?=\nasync def alert_node)', coordination_node_new, content, flags=re.DOTALL)


# For report_node: (978 -> approx 990 in new)
report_node_new = """def _parse_report(claude_response):
    confidence_score = None
    reasoning_steps = []

    m_desc, o_desc, s_desc = _parse_tasks(claude_response)
    passenger_sms = claude_response.get("passenger_sms") or "Check platform screens for status updates."
    situation_summary = claude_response.get("situation_summary", "")

    if "perception" in claude_response and "decision" in claude_response:
        perception, decision = claude_response["perception"], claude_response["decision"]
        situation_summary = perception.get("situation", "")
        confidence_score = int(decision.get("confidence", 0) * 100) if decision.get("confidence") is not None else None

        for action in decision.get("actions", []):
            if action.get("tool") == "send_passenger_alert":
                passenger_sms = action.get("params", {}).get("message", action.get("reason", ""))

        reasoning_steps = [
            f"PERCEIVE: {perception.get('situation')}",
            f"ASSESS: Corridor = {perception.get('affected_corridor')}, Cascade risk = {perception.get('is_cascade')}",
            f"DECIDE: {decision.get('decision')}",
            f"ACTION SLOTS: Dispatched {len(decision.get('actions', []))} tasks to departments"
        ]
    else:
        confidence_score = claude_response.get("confidence_score")
        reasoning_steps = claude_response.get("reasoning_steps") or []

    return m_desc, o_desc, s_desc, passenger_sms, situation_summary, confidence_score, reasoning_steps

async def report_node(state: AgentState) -> dict:
    try:
        await log_agent("report_node", "[RAILMIND] Broadcasting operations report...")
        anomalies = state.get("anomalies", [])
        if not anomalies:
            return {}

        anomaly = anomalies[0]
        try:
            claude_response = json.loads(state.get("claude_reasoning", "{}"))
        except Exception:
            claude_response = {}

        m_desc, o_desc, s_desc, passenger_sms, situation_summary, confidence_score, reasoning_steps = _parse_report(claude_response)
        if not situation_summary:
            situation_summary = f"Train {anomaly.get('train_number')} {anomaly.get('train_name')} is running {anomaly.get('delay_minutes', 0)} minutes behind schedule at {anomaly.get('current_station')}."

        cascade_info = await detect_cascade(anomalies)
        cascade_title = f"NETWORK EVENT: {cascade_info['corridor']} Corridor Disruption" if cascade_info.get("is_cascade") else None

        pred = state.get("prediction", {})
        worst_case = pred.get("worst_case") or f"If unresolved: {len(pred.get('at_risk_trains', [])) or 3} more trains will be delayed by 14:30"

        incident_report = {
            "incident_id": str(uuid4()),
            "loop_created": state.get("loop_count", 0),
            "timestamp": datetime.utcnow().isoformat(),
            "train_number": anomaly.get("train_number", "Unknown"),
            "train_name": anomaly.get("train_name", "Unknown"),
            "incident_title": cascade_title or f"{anomaly.get('train_number')} {anomaly.get('train_name')} delayed {anomaly.get('delay_minutes')}min at {anomaly.get('current_station')}",
            "current_station": anomaly.get("current_station") or anomaly.get("location") or "Unknown",
            "delay_minutes": anomaly.get("delay_minutes", 0),
            "severity": anomaly.get("severity", "medium"),
            "situation_summary": situation_summary,
            "reroute_plan": state.get("reroute_plan") or "Redirect affected trains via alternate route.",
            "maintenance_task": m_desc,
            "operations_task": o_desc,
            "station_manager_task": s_desc,
            "passenger_sms": passenger_sms,
            "resolution_status": "pending",
            "departments_notified": ["maintenance", "operations", "station_manager"],
            "sms_sent": len(state.get("sms_alerts_sent", [])),
            "detour_route": state.get("detour_route") or [],
            "confidence_score": confidence_score,
            "reasoning_steps": reasoning_steps,
            "passenger_impact": state.get("decision", {}).get("passenger_impact") or "👥 ~2,847 passengers affected",
            "prediction": worst_case,
            "memory_used": state.get("memory_used")
        }
        if await save_incident_if_not_duplicate(incident_report):
            try:
                await websocket_manager.broadcast(json.dumps({"type": "INCIDENT_UPDATE", "data": incident_report}))
            except Exception as e:
                logger.error(f"Failed to broadcast incident update: {e}")
            await log_agent("LOGGED", f"Incident #RM-{incident_report['incident_id'][:3].upper()} saved to database")
        else:
            await log_agent("report_node", f"[RAILMIND] Duplicate incident check: train {anomaly.get('train_number')} has an active report in the last 5 minutes. Skipping DB insertion and broadcast.")

        processed_trains = state.get("processed_trains", [])
        processed_trains.append(anomaly.get("train_number"))

        passengers = state.get("decision", {}).get("passenger_impact", "847 passengers affected")
        await log_agent("COMPLETE", f"Loop {state.get('loop_count', 0) + 1} done. {passengers}. Next scan: 30 seconds.")

        return {
            "processed_trains": processed_trains,
            "loop_count": state.get("loop_count", 0) + 1,
            "anomalies": ["CLEAR"],
            "sms_alerts_sent": ["CLEAR"],
            "department_tasks": ["CLEAR"],
            "claude_reasoning": "{}"
        }
    except Exception as e:
        logger.error(f"Error in report_node: {e}")
        await log_agent("report_node", f"[RAILMIND] [ERROR] Report node failed: {e}")
    return {}
"""
content = re.sub(r'async def report_node\(state: AgentState\) -> dict:.*?return \{\}\n(?=\nasync def supervisor_node)', report_node_new, content, flags=re.DOTALL)


with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
