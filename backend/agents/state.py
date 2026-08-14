from typing import TypedDict, List, Optional, Annotated
import operator

def append_to_list(a: Optional[List], b: Optional[List]) -> List:
    if a is None:
        a = []
    if b is None:
        b = []

    # Handle specific CLEAR token to empty the list
    if b and b[0] == "CLEAR":
        return []

    return a + b

class TrainAnomaly(TypedDict, total=False):
    train_number: Optional[str]
    train_name: Optional[str]
    anomaly_type: Optional[str]  # "delay", "overcrowding", "track_fault", "cancellation"
    severity: Optional[str]      # "low", "medium", "high", "critical"
    location: Optional[str]
    delay_minutes: Optional[int]
    passenger_load: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    current_station: Optional[str]
    destination: Optional[str]
    source: Optional[str]
    status: Optional[str]
    station_code: Optional[str]
    reason: Optional[str]

class DepartmentTask(TypedDict):
    department: str    # "maintenance", "operations", "station_manager"
    task_description: str
    urgency: str
    action_required: str

class AgentState(TypedDict, total=False):
    raw_train_data: Optional[List[dict]]
    anomalies: Annotated[List[TrainAnomaly], append_to_list]
    claude_reasoning: Optional[str]
    reroute_plan: Optional[str]
    department_tasks: Annotated[List[DepartmentTask], operator.add]
    sms_alerts_sent: Annotated[List[str], append_to_list]
    incident_report: Optional[str]
    loop_count: Optional[int]
    should_continue: Optional[bool]
    last_api_call: Optional[str]
    railways_latency_ms: Optional[int]
    ai_latency_ms: Optional[int]
    processed_trains: Optional[List[str]]
    target_trains: Optional[List[str]]
    errors: Annotated[List[str], append_to_list]
    next_node: Optional[str]
    last_node_executed: Optional[str]
    messages: Annotated[list, operator.add]
    tools_used: Annotated[List[str], append_to_list]
    detour_route: Optional[List[str]]
    perception: Optional[dict]
    decision: Optional[dict]
    incident_history: Optional[List[dict]]
    prediction: Optional[dict]
    memory_used: Optional[str]

