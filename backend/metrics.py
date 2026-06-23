from prometheus_client import Counter, Histogram, make_asgi_app

# Metrics definitions
NODE_LATENCY = Histogram(
    "railmind_node_latency_seconds",
    "Time spent processing a LangGraph node",
    ["node_name"]
)

TOKEN_CONSUMPTION = Counter(
    "railmind_token_consumption_total",
    "Total tokens consumed by AI models",
    ["model_name"]
)

ERROR_RATE = Counter(
    "railmind_error_rate_total",
    "Total errors encountered in processing",
    ["node_name", "error_type"]
)

TWILIO_STATUS = Counter(
    "railmind_twilio_status_total",
    "Status of Twilio SMS API responses",
    ["status"]
)

# Application to mount
metrics_app = make_asgi_app()
