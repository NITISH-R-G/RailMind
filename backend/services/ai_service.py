import json
import os
import aiohttp
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from ..circuit_breaker import llm_circuit_breaker
from ..monitoring import AGENT_TOKEN_CONSUMPTION
from ..config import settings
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage

from dotenv import load_dotenv # type: ignore

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

@tool
def query_line_capacity(station: str) -> str:
    """Queries the current line capacity and available platforms for a given station."""
    # Dummy mock tool implementation
    if "Kanpur" in station:
        return json.dumps({"station": station, "available_platforms": ["1"], "restricted_lines": ["2", "3", "4"]})
    return json.dumps({"station": station, "available_platforms": ["1", "2"], "restricted_lines": []})

@tool
def check_weather_grids(lat: float, lng: float) -> str:
    """Checks the local weather grids for anomalies like heavy rain or fog."""
    # Dummy mock tool implementation
    return json.dumps({"lat": lat, "lng": lng, "weather": "Clear", "visibility": "10km"})

@tool
def review_historical_incidents(train_num: str) -> str:
    """Reviews historical incident databases for a given train number."""
    # Dummy mock tool implementation
    return json.dumps({"train_number": train_num, "historical_incidents": 0, "notes": "No recent major issues."})

class MitigationPlan(BaseModel):
    incident_title: str
    situation_summary: str
    maintenance_task: str
    operations_task: str
    station_manager_task: str
    passenger_sms: str
    incident_summary: str

tools = [query_line_capacity, check_weather_grids, review_historical_incidents]
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", max_tokens=1024)
llm_with_tools = llm.bind_tools(tools)
structured_llm = llm.with_structured_output(MitigationPlan)
tool_map = {tool.name: tool for tool in tools}

@llm_circuit_breaker
async def reason_with_ai_primary(messages, tools):
    from langgraph.prebuilt import create_react_agent
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", max_tokens=1024, api_key=settings.ANTHROPIC_API_KEY.get_secret_value())
    agent = create_react_agent(llm, tools)
    result = await agent.ainvoke({"messages": messages})
    return result, llm

async def reason_with_ai_fallback(messages, tools):
    from langgraph.prebuilt import create_react_agent
    llm = ChatOllama(model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_URL)
    agent = create_react_agent(llm, tools)
    result = await agent.ainvoke({"messages": messages})
    return result, llm

async def reason_with_ai(anomalies: list, errors: list = None) -> dict:
    if not anomalies:
        return {}

    if errors is None:
        errors = []

    anomaly = anomalies[0]
    
    train_name = anomaly.get("train_name", "Unknown Train")
    train_number = anomaly.get("train_number", "Unknown")
    current_station = anomaly.get("current_station") or anomaly.get("location") or "Unknown Station"
    delay_minutes = anomaly.get("delay_minutes", 0)
    status = anomaly.get("status", "delayed")
    source = anomaly.get("source", "Unknown")
    destination = anomaly.get("destination", "Unknown")
    severity = anomaly.get("severity", "medium")

    system_prompt = """You are RailMind, India's autonomous railway operations intelligence agent.
You must investigate the current anomaly and generate a mitigation plan.
You have access to tools: query_line_capacity, check_weather_grids, and review_historical_incidents.
Use these tools to gather information before making a decision.
Never guess mitigations without using tools.
Generate SPECIFIC, ACTIONABLE decisions based on the exact train, route, and station involved.
"""

    user_prompt = f"""
Anomaly detected:
Train: {train_name} ({train_number})
Current Station: {current_station}
Delay: {delay_minutes} minutes
Status: {status}
Route: {source} -> {destination}
Severity: {severity}

Previous errors from Supervisor (if any, please correct your plan):
{json.dumps(errors)}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    try:
        result, llm_used = await reason_with_ai_primary(messages, tools)
        AGENT_TOKEN_CONSUMPTION.labels(node='reason_node', model='claude').inc()
    except Exception as e:
        print(f"[RAILMIND] Primary AI Failed, falling back to local model: {e}")
        try:
            result, llm_used = await reason_with_ai_fallback(messages, tools)
            AGENT_TOKEN_CONSUMPTION.labels(node='reason_node', model='ollama').inc()
        except Exception as e_fallback:
            print(f"[RAILMIND] Fallback AI also failed: {e_fallback}")
            raise e_fallback

    try:
        final_messages = result["messages"]
        structured_llm = llm_used.with_structured_output(MitigationPlan)
        final_plan: MitigationPlan = await structured_llm.ainvoke(final_messages)
        return final_plan.dict()
    except Exception as e:
        print(f"[RAILMIND] AI Reasoning or structured output failed: {e}")
        return {
            "incident_title": f"{train_number} {train_name} delayed {delay_minutes}min at {current_station}",
            "situation_summary": f"Train running {delay_minutes} minutes behind schedule due to operational constraints at {current_station}.",
            "maintenance_task": f"Inspect and test signaling points and local circuits at {current_station} station immediately.",
            "operations_task": f"Execute slot re-scheduling and coordinate clearance for train {train_number} on the main line.",
            "station_manager_task": f"Make PA announcement: Passenger attention please, train {train_number} {train_name} is running late by {delay_minutes} minutes.",
            "passenger_sms": f"[RailMind Alert] Train {train_number} {train_name} is delayed by {delay_minutes} minutes. Please check screens for platform updates.",
            "incident_summary": f"Automated incident report logged for train {train_number} at {current_station} with {delay_minutes} minutes delay."
        }
