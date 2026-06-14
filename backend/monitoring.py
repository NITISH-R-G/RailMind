import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram

# Metrics
AGENT_TOKEN_CONSUMPTION = Counter('agent_token_consumption_total', 'Total tokens consumed by agent nodes', ['node', 'model'])
NODE_EXECUTION_LATENCY = Histogram('node_execution_latency_seconds', 'Latency of node execution in seconds', ['node'])
ERROR_RATES = Counter('error_rates_total', 'Total error rates', ['node', 'type'])
TWILIO_API_STATUS = Counter('twilio_api_status_total', 'Twilio API response status arrays', ['status'])

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logHandler = RotatingFileHandler('/var/log/railmind/app.json', maxBytes=10*1024*1024, backupCount=5)
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

setup_logging()
