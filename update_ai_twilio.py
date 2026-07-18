import re

with open('backend/services/ai_service.py', 'r') as f:
    content = f.read()

# Introduce Circuit Breaker
cb_import = """
from ..circuit_breaker import ai_circuit_breaker
from ..agents.metrics import AI_TOKEN_CONSUMPTION
"""
if "ai_circuit_breaker" not in content:
    content = content.replace("from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage", f"from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage{cb_import}")

if "result = await agent.ainvoke" in content:
    content = content.replace("result = await agent.ainvoke({\"messages\": messages})", """
        AI_TOKEN_CONSUMPTION.labels(model="claude-3-5-sonnet").inc(1)
        result = await ai_circuit_breaker.call(agent.ainvoke, {"messages": messages})""")

with open('backend/services/ai_service.py', 'w') as f:
    f.write(content)


with open('backend/services/twilio_service.py', 'r') as f:
    content = f.read()

cb_import_twilio = """
from ..circuit_breaker import twilio_circuit_breaker
from ..agents.metrics import TWILIO_API_STATUS
"""

if "twilio_circuit_breaker" not in content:
    content = content.replace("import logging", f"import logging{cb_import_twilio}")

if "message = await asyncio.to_thread(" in content:
    content = content.replace("message = await asyncio.to_thread(", """
            TWILIO_API_STATUS.labels(status_code="200").inc(1)
            message = await twilio_circuit_breaker.call(asyncio.to_thread, """)

with open('backend/services/twilio_service.py', 'w') as f:
    f.write(content)
