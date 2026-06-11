from typing import TypedDict, List, Optional, Annotated

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

def reduce_tasks(left: List[DepartmentTask] | None, right: List[DepartmentTask] | None) -> List[DepartmentTask]:
    if left is None:
        left = []
    if right is None:
        return left
    if len(right) > 0 and right[0].get("department") == "CLEAR":
        return []
    return left + right

def reduce_strings(left: List[str] | None, right: List[str] | None) -> List[str]:
    if left is None:
        left = []
    if right is None:
        return left
    if len(right) > 0 and right[0] == "CLEAR":
        return []
    return left + right

class AgentState(TypedDict):
    raw_train_data: List[dict]
    anomalies: List[TrainAnomaly]
    claude_reasoning: str
    reroute_plan: Optional[str]
    department_tasks: Annotated[List[DepartmentTask], reduce_tasks]
    sms_alerts_sent: Annotated[List[str], reduce_strings]
    incident_report: Optional[str]
    loop_count: int
    should_continue: bool
    last_api_call: str
    railways_latency_ms: int
    ai_latency_ms: int
    processed_trains: List[str]

    # Supervisor routing fields
    next_node: Optional[str]
    error_vector: Optional[str]
    last_node_executed: Optional[str]
