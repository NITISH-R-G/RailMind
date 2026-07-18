from prometheus_client import Counter, Histogram

# Latency tracking
NODE_LATENCY = Histogram(
    'railmind_node_latency_seconds',
    'Time spent in LangGraph nodes',
    ['node_name']
)

# Token tracking (simplified as a counter of invocations or manual token increments)
AI_TOKEN_CONSUMPTION = Counter(
    'railmind_ai_token_consumption_total',
    'Tokens consumed by AI requests',
    ['model']
)

# Error rates
ERROR_SPIKES = Counter(
    'railmind_error_spikes_total',
    'Errors encountered during agent operations',
    ['error_type', 'node_name']
)

# Twilio API Status Array
TWILIO_API_STATUS = Counter(
    'railmind_twilio_api_status_total',
    'Twilio API response statuses',
    ['status_code']
)
