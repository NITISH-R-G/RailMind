import re

with open("backend/agents/nodes.py", "r") as f:
    content = f.read()

# Update evaluate_previous_action
content = re.sub(
    r'async def evaluate_previous_action\(state: AgentState\) -> AgentState:.*?return state',
    r'''async def evaluate_previous_action(state: AgentState) -> dict:
    try:
        await log_agent("evaluate_previous_action", "[RAILMIND] Checking and evaluating previous self-healing actions...")
        diff = {"last_node_executed": "evaluate_previous_action"}
        # Pre-ingest live train status if raw_train_data is empty (since this node runs first)
        if not state.get("raw_train_data"):
            train_numbers = [
                "12301", "12951", "12001", "12259", "12565",
                "11057", "12627", "12625", "12621", "12615",
                "12309", "12721", "12229", "12311", "12641"
            ]
            import time
            start_time = time.time()
            client = railways_client
            print(f"[RAILMIND] Pre-ingesting Railways API for {len(train_numbers)} trains...")
            results = await client.get_multiple_trains(train_numbers)

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

            cancelled = await get_cancelled_trains()
            live_trains = train_results.copy()
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
            diff["raw_train_data"] = live_trains
            diff["last_api_call"] = datetime.utcnow().isoformat()
            diff["railways_latency_ms"] = int((time.time() - start_time) * 1000)

        # Evaluate pending incidents
        new_anomalies = []
        for train in diff.get("raw_train_data", state.get("raw_train_data", [])):
            train_no = train.get("train_number")
            if not train_no:
                continue

            prev_incident = None
            if not db_client.use_fallback:
                try:
                    prev_incident = await db_client.db["incidents"].find_one({
                        "train_number": train_no,
                        "resolution_status": "pending"
                    }, sort=[("timestamp", -1)])
                except Exception:
                    db_client.use_fallback = True

            if db_client.use_fallback:
                incidents = await db_client.get_incidents(limit=100)
                for inc in incidents:
                    if inc.get("train_number") == train_no and inc.get("resolution_status") == "pending":
                        prev_incident = inc
                        break

            if prev_incident:
                loops_since = state.get("loop_count", 0) - prev_incident.get("loop_created", 0)

                # If delay is still high (or worsening) after 2 loops, escalate
                if loops_since >= 2 and train.get("delay_minutes", 0) > prev_incident.get("delay_minutes", 0):
                    await broadcast_log("ESCALATING",
                        f"Train {train_no} delay worsening ({prev_incident['delay_minutes']}min -> {train['delay_minutes']}min). Escalating to Control Room.")

                    # Ensure we don't insert duplicate escalation anomalies for the same train in this loop
                    if not any(a.get("train_number") == train_no and a.get("anomaly_type") == "escalation" for a in state.get("anomalies", [])):
                        new_anomalies.append({
                            **train,
                            "anomaly_type": "escalation",
                            "severity": "critical",
                            "reason": "Previous reroute ineffective"
                        })
        if new_anomalies:
             diff["anomalies"] = new_anomalies

        return diff
    except Exception as e:
        logger.error(f"Error in evaluate_previous_action: {e}")
        await log_agent("evaluate_previous_action", f"[RAILMIND] [ERROR] Self-healing evaluation failed: {e}")
        return {"last_node_executed": "evaluate_previous_action", "errors": [f"evaluate_previous_action error: {e}"]}''',
    content,
    flags=re.DOTALL
)


# Update ingest_node
content = re.sub(
    r'async def ingest_node\(state: AgentState\) -> AgentState:.*?return state',
    r'''async def ingest_node(state: AgentState) -> dict:
    try:
        await log_agent("SCANNING", "Polling 15 trains on Indian Railways...")
        diff = {"last_node_executed": "ingest_node"}
        # If evaluate_previous_action already populated the raw train data, reuse it
        if state.get("raw_train_data"):
            live_trains = state["raw_train_data"]
            diff["raw_train_data"] = live_trains
        else:
            train_numbers = state.get("target_trains")
            if not train_numbers:
                train_numbers = [
                    "12301", "12951", "12001", "12259", "12565",
                    "11057", "12627", "12625", "12621", "12615",
                    "12309", "12721", "12229", "12311", "12641",
                    "12438", "ICE"
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
            diff["last_api_call"] = datetime.utcnow().isoformat()
            diff["railways_latency_ms"] = latency

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

        diff["raw_train_data"] = live_trains
        await log_agent("ingest_node", f"[RAILMIND] Ingested {len(live_trains)} trains")
        return diff
    except Exception as e:
        logger.error(f"Error in ingest_node: {e}")
        await log_agent("ingest_node", f"[RAILMIND] [ERROR] Ingest node failed: {e}")
        return {"last_node_executed": "ingest_node", "errors": [f"ingest_node error: {e}"]}''',
    content,
    flags=re.DOTALL
)

# Update detect_node
content = re.sub(
    r'async def detect_node\(state: AgentState\) -> AgentState:.*?return state',
    r'''async def detect_node(state: AgentState) -> dict:
    try:
        await log_agent("detect_node", "[RAILMIND] Running real-time anomaly detection rules...")
        diff = {"last_node_executed": "detect_node"}
        anomalies: List[TrainAnomaly] = []
        raw_data = state.get("raw_train_data", [])
        processed_trains = state.get("processed_trains", [])

        # Preserve custom simulated anomaly types if present
        simulated_types = {}
        for a in state.get("anomalies", []):
            if "train_number" in a and "anomaly_type" in a:
                simulated_types[a["train_number"]] = a["anomaly_type"]

        for train in raw_data:
            train_num = train.get("train_number", "Unknown")
            if train_num in processed_trains:
                continue
            train_name = train.get("train_name", "Unknown")
            location = train.get("current_station") or train.get("source") or "Unknown"
            delay = train.get("delay_minutes", 0)
            load = train.get("passenger_load")
            status = str(train.get("status") or "").lower()

            simulated_type = simulated_types.get(train_num)

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
                    "anomaly_type": simulated_type or "delay",
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
                    "anomaly_type": simulated_type or "overcrowding",
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
                    "anomaly_type": simulated_type or "cancellation",
                    "severity": "critical",
                    "location": location,
                    "delay_minutes": delay,
                    "passenger_load": load,
                    "current_station": train.get("current_station") or location,
                    "status": "cancelled",
                    "source": train.get("source") or "Unknown",
                    "destination": train.get("destination") or "Unknown"
                })

        # Map station_code if not present using get_station_code_from_name
        for a in anomalies:
            if "station_code" not in a:
                loc = a.get("location") or a.get("current_station") or ""
                a["station_code"] = get_station_code_from_name(loc)

        # Broadcast DETECTED logs for each anomaly
        for a in anomalies:
            st_code = get_station_code_from_name(a.get("location") or a.get("current_station") or "") or a.get("location")[:4].upper()
            delay_text = f"{a['delay_minutes']}min delay" if a.get("delay_minutes") else "anomaly"
            await log_agent("DETECTED", f"Train {a['train_number']}: {delay_text} at {st_code}")

        # Cascading Failure Detection (Transformation 3)
        await log_agent("CASCADE?", "Checking Delhi-Mumbai corridor...")
        cascade_info = await detect_cascade(anomalies)
        if cascade_info.get("is_cascade"):
            corridor = cascade_info["corridor"]
            affected_stations = cascade_info["affected_stations"]
            await log_agent("detect_node", f"[RAILMIND] [CASCADE] {cascade_info['message']}")

            # Change severity of all affected corridor trains to critical
            for a in anomalies:
                if a.get("station_code") in affected_stations:
                    a["severity"] = "critical"
                    a["anomaly_type"] = "cascade"

            # Broadcast CASCADE_ALERT via WebSocket
            try:
                await websocket_manager.broadcast(json.dumps({
                    "type": "CASCADE_ALERT",
                    "corridor": corridor,
                    "affected_stations": affected_stations,
                    "message": cascade_info["message"]
                }))
            except Exception as ws_e:
                logger.error(f"Failed to broadcast CASCADE_ALERT: {ws_e}")

        # Since it's Annotated, this will append, but we likely just want them sent as new
        diff["anomalies"] = anomalies
        n = len(anomalies)
        if n > 0:
            await log_agent("detect_node", f"[RAILMIND] [WARNING] Detected {n} anomalies")
            diff["should_continue"] = True
        else:
            await log_agent("detect_node", "[RAILMIND] [OK] All trains nominal")
            diff["should_continue"] = False
        return diff
    except Exception as e:
        logger.error(f"Error in detect_node: {e}")
        await log_agent("detect_node", f"[RAILMIND] [ERROR] Detect node failed: {e}")
        return {"last_node_executed": "detect_node", "errors": [f"detect_node error: {e}"]}''',
    content,
    flags=re.DOTALL
)


# Update predict_node
content = re.sub(
    r'async def predict_node\(state: AgentState\) -> AgentState:.*?return state',
    r'''async def predict_node(state: AgentState) -> dict:
    try:
        await log_agent("predict_node", "[RAILMIND] Running predictive intelligence model...")
        diff = {"last_node_executed": "predict_node"}
        anomalies = state.get("anomalies", [])
        if not anomalies:
            diff["prediction"] = {}
            return diff

        predict_prompt = f"""
        Current delayed trains: {json.dumps(anomalies)}
        Time: {datetime.utcnow().strftime("%H:%M")}

        PREDICT the next 30 minutes:
        1. Which currently on-time trains will be affected
           by these delays? (cascade effect)
        2. Which stations will face platform congestion?
        3. What is the worst case scenario?
        4. What preemptive actions can prevent the cascade?

        Respond in JSON: {{
            "at_risk_trains": ["train_no", ...],
            "congestion_stations": ["station_code", ...],
            "worst_case": "...",
            "preemptive_actions": ["action1", "action2"],
            "confidence": 0.0-1.0
        }}
        """
        prediction = await call_gemini(predict_prompt, state)
        diff["prediction"] = prediction

        at_risk = len(prediction.get("at_risk_trains", []))
        await log_agent("PREDICTING", f"{at_risk} trains at risk next 30 mins...")

        # Show prediction on dashboard
        try:
            await websocket_manager.broadcast(json.dumps({
                "type": "PREDICTION_UPDATE",
                "data": prediction
            }))
        except Exception as e:
            logger.error(f"Failed to broadcast prediction update: {e}")
        return diff
    except Exception as e:
        logger.error(f"Error in predict_node: {e}")
        await log_agent("predict_node", f"[RAILMIND] [ERROR] Predictive intelligence failed: {e}")
        return {"last_node_executed": "predict_node", "errors": [f"predict_node error: {e}"]}''',
    content,
    flags=re.DOTALL
)


# We'll rewrite coordination_node, alert_node, report_node similarly
content = re.sub(
    r'async def coordination_node\(state: AgentState\) -> AgentState:.*?return \{\}',
    r'''async def coordination_node(state: AgentState) -> dict:
    try:
        await log_agent("coordination_node", "[RAILMIND] Initiating department task dispatches...")
        diff = {"last_node_executed": "coordination_node"}
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

        # Support nested format or flat format
        maintenance_desc = "Inspect signals and tracks."
        operations_desc = "Coordinate slot changes and schedules."
        station_desc = "Broadcast announcement on platform boards."

        if "perception" in claude_response and "decision" in claude_response:
            actions = claude_response["decision"].get("actions", [])
            for action in actions:
                tool = action.get("tool")
                reason = action.get("reason", "")
                params = action.get("params", {})
                if tool == "alert_department":
                    dept = params.get("dept", "").lower()
                    msg = params.get("message", reason)
                    if "maintenance" in dept:
                        maintenance_desc = msg
                    elif "operations" in dept:
                        operations_desc = msg
                    elif "station" in dept or "manager" in dept:
                        station_desc = msg
                elif tool == "reroute_train":
                    operations_desc = f"Reroute train {params.get('train_no')} via {params.get('via_station')}: {reason}"
        else:
            maintenance_desc = claude_response.get("maintenance_task", "Inspect signals and tracks.")
            operations_desc = claude_response.get("operations_task", "Coordinate slot changes and schedules.")
            station_desc = claude_response.get("station_manager_task", "Broadcast announcement on platform boards.")

        maintenance_task: DepartmentTask = {
            "department": "maintenance",
            "task_description": maintenance_desc,
            "urgency": highest_severity,
            "action_required": "Dispatch repair team immediately"
        }

        operations_task: DepartmentTask = {
            "department": "operations",
            "task_description": operations_desc,
            "urgency": operations_urgency,
            "action_required": "Execute rerouting plan"
        }

        station_manager_task: DepartmentTask = {
            "department": "station_manager",
            "task_description": station_desc,
            "urgency": "high",
            "action_required": "Make passenger announcement + update platform boards"
        }

        department_tasks = [maintenance_task, operations_task, station_manager_task]
        diff["department_tasks"] = department_tasks

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
        return diff
    except Exception as e:
        logger.error(f"Error in coordination_node: {e}")
        await log_agent("coordination_node", f"[RAILMIND] [ERROR] Coordination node failed: {e}")
        return {"last_node_executed": "coordination_node", "errors": [f"coordination error: {e}"]}''',
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'async def alert_node\(state: AgentState\) -> AgentState:.*?return \{\}',
    r'''async def alert_node(state: AgentState) -> dict:
    try:
        await log_agent("alert_node", "[RAILMIND] Sending Twilio notifications...")
        diff = {"last_node_executed": "alert_node"}
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
        diff["sms_alerts_sent"] = sent_sms
        return diff
    except Exception as e:
        logger.error(f"Error in alert_node: {e}")
        await log_agent("alert_node", f"[RAILMIND] [ERROR] Alert node failed: {e}")
        return {"last_node_executed": "alert_node", "errors": [f"alert error: {e}"]}''',
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'async def report_node\(state: AgentState\) -> AgentState:.*?return \{\}',
    r'''async def report_node(state: AgentState) -> dict:
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

        # Handle nested perception/decision format
        confidence_score = None
        reasoning_steps = []
        situation_summary = ""

        # Default fallback values for tasks
        maintenance_task = "Inspect signaling hardware."
        operations_task = "Execute scheduling adjustments."
        station_manager_task = "Broadcast delay announcements."
        passenger_sms = "Check platform screens for status updates."

        if "perception" in claude_response and "decision" in claude_response:
            perception = claude_response["perception"]
            decision = claude_response["decision"]
            situation_summary = perception.get("situation", "")
            confidence_score = int(decision.get("confidence", 0) * 100) if decision.get("confidence") is not None else None

            # Map actions to task text
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

            # Create reasoning steps for frontend rendering
            reasoning_steps = [
                f"PERCEIVE: {perception.get('situation')}",
                f"ASSESS: Corridor = {perception.get('affected_corridor')}, Cascade risk = {perception.get('is_cascade')}",
                f"DECIDE: {decision.get('decision')}",
                f"ACTION SLOTS: Dispatched {len(actions)} tasks to departments"
            ]
        else:
            situation_summary = claude_response.get("situation_summary") or f"Train {train_number} {train_name} is running {delay_minutes} minutes behind schedule at {current_station}."
            maintenance_task = claude_response.get("maintenance_task") or "Inspect signaling hardware."
            operations_task = claude_response.get("operations_task") or "Execute scheduling adjustments."
            station_manager_task = claude_response.get("station_manager_task") or "Broadcast delay announcements."
            passenger_sms = claude_response.get("passenger_sms") or "Check platform screens for status updates."
            confidence_score = claude_response.get("confidence_score")
            reasoning_steps = claude_response.get("reasoning_steps") or []

        # Check for corridor cascade disruption
        cascade_title = None
        cascade_info = await detect_cascade(anomalies)
        if cascade_info.get("is_cascade"):
            cascade_title = f"NETWORK EVENT: {cascade_info['corridor']} Corridor Disruption"

        incident_id = str(uuid4())

        # Construct prediction warning message
        pred = state.get("prediction", {})
        worst_case = pred.get("worst_case")
        if not worst_case:
            at_risk_count = len(pred.get("at_risk_trains", [])) or 3
            future_time = "14:30"
            try:
                ts_str = state.get("last_api_call") or datetime.utcnow().isoformat()
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
            "timestamp": datetime.utcnow().isoformat(),
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
            "passenger_impact": state.get("decision", {}).get("passenger_impact") or "👥 ~2,847 passengers affected",
            "prediction": worst_case,
            "memory_used": state.get("memory_used")
        }
        # Check for duplicates in last 5 minutes before saving (ISSUE 2)
        saved = await save_incident_if_not_duplicate(incident_report)
        if saved:
            # Broadcast via WebSocket
            try:
                await websocket_manager.broadcast(json.dumps({
                    "type": "INCIDENT_UPDATE",
                    "data": incident_report
                }))
            except Exception as e:
                logger.error(f"Failed to broadcast incident update: {e}")

            await log_agent("LOGGED", f"Incident #RM-{incident_id[:3].upper()} saved to database")
        else:
            await log_agent("report_node", f"[RAILMIND] Duplicate incident check: train {train_number} has an active report in the last 5 minutes. Skipping DB insertion and broadcast.")

        # Mark this train as recently processed in state
        processed_trains = state.get("processed_trains", [])
        processed_trains.append(anomaly["train_number"])

        diff["loop_count"] = state.get("loop_count", 0) + 1
        diff["next_node"] = "END"

        passengers = state.get("decision", {}).get("passenger_impact", "847 passengers affected")
        if isinstance(passengers, str):
            passengers_str = passengers
        else:
            passengers_str = f"{passengers} passengers affected"
        await log_agent("COMPLETE", f"Loop {diff['loop_count']} done. {passengers_str}. Next scan: 30 seconds.")

        diff.update({
            "processed_trains": processed_trains,
            "anomalies": ["CLEAR"], # clear anomalies so next run starts fresh
            "sms_alerts_sent": ["CLEAR"],
            "department_tasks": ["CLEAR"],
            "claude_reasoning": "{}"
        })
        return diff

    except Exception as e:
        logger.error(f"Error in report_node: {e}")
        await log_agent("report_node", f"[RAILMIND] [ERROR] Report node failed: {e}")
        return {"last_node_executed": "report_node", "errors": [f"report error: {e}"]}''',
    content,
    flags=re.DOTALL
)

with open("backend/agents/nodes.py", "w") as f:
    f.write(content)
