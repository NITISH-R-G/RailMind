import re

with open('backend/agents/nodes.py', 'r') as f:
    content = f.read()

# Replace stdout logging with JSON logging
imports_to_add = """
import time
from pythonjsonlogger import jsonlogger
from .metrics import NODE_LATENCY, AI_TOKEN_CONSUMPTION, ERROR_SPIKES
from ..config import settings
"""

if "from pythonjsonlogger import jsonlogger" not in content:
    content = content.replace('from datetime import datetime', f'from datetime import datetime{imports_to_add}')

log_setup = """
logger = logging.getLogger(__name__)

# JSON Logging setup
logHandler = logging.handlers.RotatingFileHandler('/var/log/railmind/app.json', maxBytes=10485760, backupCount=5)
# Fallback to local if permission denied
except PermissionError:
    logHandler = logging.handlers.RotatingFileHandler('app.json', maxBytes=10485760, backupCount=5)
"""
# We'll use a more surgical approach for logging setup
if "RotatingFileHandler" not in content:
    content = content.replace("logger = logging.getLogger(__name__)", """
logger = logging.getLogger(__name__)
try:
    import logging.handlers
    logHandler = logging.handlers.RotatingFileHandler('/var/log/railmind/app.json', maxBytes=10485760, backupCount=5)
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
except Exception as e:
    print(f"Could not setup JSON logging: {e}")
""")

# Instrument nodes with Latency Tracking
content = content.replace('async def ingest_node(state: AgentState) -> AgentState:\n    try:', 'async def ingest_node(state: AgentState) -> AgentState:\n    start_time = time.time()\n    try:')
content = content.replace('await log_agent("ingest_node", f"[RAILMIND] [ERROR] Ingest node failed: {e}")\n    return state', 'await log_agent("ingest_node", f"[RAILMIND] [ERROR] Ingest node failed: {e}")\n        ERROR_SPIKES.labels(error_type="exception", node_name="ingest_node").inc()\n    finally:\n        NODE_LATENCY.labels(node_name="ingest_node").observe(time.time() - start_time)\n    return state')

content = content.replace('async def detect_node(state: AgentState) -> AgentState:\n    try:', 'async def detect_node(state: AgentState) -> AgentState:\n    start_time = time.time()\n    try:')
content = content.replace('await log_agent("detect_node", f"[RAILMIND] [ERROR] Detect node failed: {e}")\n    return state', 'await log_agent("detect_node", f"[RAILMIND] [ERROR] Detect node failed: {e}")\n        ERROR_SPIKES.labels(error_type="exception", node_name="detect_node").inc()\n    finally:\n        NODE_LATENCY.labels(node_name="detect_node").observe(time.time() - start_time)\n    return state')

content = content.replace('async def reason_node(state: AgentState) -> AgentState:\n    try:', 'async def reason_node(state: AgentState) -> AgentState:\n    start_time_metric = time.time()\n    try:')
content = content.replace('await log_agent("reason_node", f"[RAILMIND] [ERROR] Reason node failed: {e}")\n    return state', 'await log_agent("reason_node", f"[RAILMIND] [ERROR] Reason node failed: {e}")\n        ERROR_SPIKES.labels(error_type="exception", node_name="reason_node").inc()\n    finally:\n        NODE_LATENCY.labels(node_name="reason_node").observe(time.time() - start_time_metric)\n    return state')

with open('backend/agents/nodes.py', 'w') as f:
    f.write(content)
