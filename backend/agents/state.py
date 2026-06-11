from typing import TypedDict, List, Optional, Annotated


def append_to_list(a: Optional[List], b: Optional[List]) -> List:
    if a is None:
        a = []
    if b is None:
        b = []
    return a + b


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
    anomalies: Annotated[List[TrainAnomaly], append_to_list]
    claude_reasoning: str
    reroute_plan: Optional[str]
    department_tasks: Annotated[List[DepartmentTask], append_to_list]
    sms_alerts_sent: Annotated[List[str], append_to_list]
    incident_report: Optional[str]
    loop_count: int
    should_continue: bool
    last_api_call: str
    railways_latency_ms: int
    ai_latency_ms: int
    processed_trains: List[str]
    errors: Annotated[List[str], append_to_list]
    next_node: str
    messages: Annotated[list, append_to_list]
    tools_used: Annotated[List[str], append_to_list]
