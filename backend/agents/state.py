from typing import TypedDict, List, Optional, Annotated
import operator

def add_with_clear(a: Optional[List], b: Optional[List]) -> List:
    if a is None:
        a = []
    if b is None:
        b = []

    # Handle specific CLEAR token to empty the list
    if b and b[0] == "CLEAR":
        return []

    return operator.add(a, b)

class TrainAnomaly(TypedDict):
    train_number: str
    train_name: str
    anomaly_type: str  # "delay", "overcrowding", "track_fault", "cancellation"
    severity: str      # "low", "medium", "high", "critical"
    location: str
    delay_minutes: Optional[int]
    passenger_load: Optional[str]

class DepartmentTask(TypedDict):
    department: str    # "maintenance", "operations", "station_manager"
    task_description: str
    urgency: str
    action_required: str

class AgentState(TypedDict):
    raw_train_data: List[dict]
    anomalies: Annotated[List[TrainAnomaly], add_with_clear]
    claude_reasoning: str
    reroute_plan: Optional[str]
    department_tasks: Annotated[List[DepartmentTask], add_with_clear]
    sms_alerts_sent: Annotated[List[str], add_with_clear]
    incident_report: Optional[str]
    loop_count: int
    should_continue: bool
    last_api_call: str
    railways_latency_ms: int
    ai_latency_ms: int
    processed_trains: List[str]
    target_trains: List[str]
    errors: Annotated[List[str], add_with_clear]
    next_node: str
    last_node_executed: str
    messages: Annotated[list, add_with_clear]
    tools_used: Annotated[List[str], add_with_clear]
    detour_route: List[str]
    perception: Optional[dict]
    decision: Optional[dict]
    incident_history: Optional[List[dict]]
    prediction: Optional[dict]
    memory_used: Optional[str]

