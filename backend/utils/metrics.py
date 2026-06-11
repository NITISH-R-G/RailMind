from prometheus_client import Counter, Histogram

LANGGRAPH_NODE_LATENCY = Histogram(
    'langgraph_node_latency_seconds',
    'Latency of LangGraph node execution in seconds',
    ['node_name']
)

LANGGRAPH_ERROR_COUNT = Counter(
    'langgraph_error_count',
    'Number of errors in LangGraph nodes',
    ['node_name']
)

AI_TOKEN_CONSUMPTION = Counter(
    'ai_token_consumption_total',
    'Total tokens consumed by AI models',
    ['model']
)

TWILIO_RESPONSE_STATUS = Counter(
    'twilio_response_status',
    'Twilio API response status counts',
    ['status']
)
