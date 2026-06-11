import os
import json
from dotenv import load_dotenv # type: ignore
from pydantic import BaseModel, Field # type: ignore
from langchain_anthropic import ChatAnthropic # type: ignore
from langchain_core.prompts import ChatPromptTemplate # type: ignore
from backend.agents.tools import TOOLS

# Ensure env variables are loaded before configuration
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

class AIReasoningOutput(BaseModel):
    incident_title: str = Field(..., description="Specific title mentioning train name and station")
    situation_summary: str = Field(..., description="1 sentence specific to this train")
    reroute_plan: str = Field(..., description="Specific rerouting for THIS train on THIS route, mentioning actual alternate stations")
    maintenance_task: str = Field(..., description="Specific maintenance task required")

async def reason_with_ai(anomalies: list) -> dict:
    if not anomalies:
        return {}
        
    anomaly = anomalies[0]
    
    # Extract keys safely with default fallbacks
    train_name = anomaly.get("train_name", "Unknown Train")
    train_number = anomaly.get("train_number", "Unknown")
    current_station = anomaly.get("current_station") or anomaly.get("location") or "Unknown Station"
    delay_minutes = anomaly.get("delay_minutes", 0)
    status = anomaly.get("status", "delayed")
    source = anomaly.get("source", "Unknown")
    destination = anomaly.get("destination", "Unknown")
    severity = anomaly.get("severity", "medium")

    system_prompt = """You are RailMind, India's autonomous railway operations intelligence agent. You monitor Indian Railways in real time. When anomalies are detected, you generate SPECIFIC, ACTIONABLE decisions based on the exact train, route, and station involved. Never give generic responses. Every decision must reference the specific train number, station name, and delay duration."""

    user_prompt = f"""
Anomaly detected:
Train: {train_name} ({train_number})
Current Station: {current_station}
Delay: {delay_minutes} minutes
Status: {status}
Route: {source} → {destination}

Analyze this anomaly and use tools if needed to gather more information, then provide a structured mitigation plan.
"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "mock_key":
        # Fallback to mock output for testing when no valid API key is present
        print("[RAILMIND] ANTHROPIC_API_KEY not found or mock_key, using mock AI output")
        return {
            "incident_title": f"{train_number} {train_name} delayed {delay_minutes}min at {current_station}",
            "situation_summary": f"Train {train_number} is experiencing a delay of {delay_minutes} minutes at {current_station} due to {status}.",
            "reroute_plan": f"Reroute train {train_number} via alternate tracks at {current_station}.",
            "maintenance_task": f"Inspect tracks near {current_station} for train {train_number}."
        }

    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0, api_key=api_key)

    try:
        from langgraph.prebuilt import create_react_agent # type: ignore
        from langchain_core.messages import SystemMessage, HumanMessage # type: ignore

        agent = create_react_agent(llm, TOOLS)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        # Execute the agent loop to use tools
        agent_response = await agent.ainvoke({"messages": messages})

        # Get the final reasoning as text
        final_text = agent_response["messages"][-1].content

        # Now pass this enriched context to a structured LLM to guarantee the JSON output schema
        structured_llm = llm.with_structured_output(AIReasoningOutput)

        formatting_prompt = ChatPromptTemplate.from_messages([
            ("system", "Extract and format the information strictly into the requested JSON schema."),
            ("user", f"Here is the detailed analysis report:\n\n{final_text}")
        ])

        result = await structured_llm.ainvoke(formatting_prompt.format_messages())

        return result.model_dump()

    except Exception as e:
        print(f"Error in reason_with_ai: {e}")
        # Return fallback on error to simulate recovery
        return {
            "incident_title": f"{train_number} {train_name} Error",
            "situation_summary": f"Error processing anomaly: {e}",
            "reroute_plan": "Fallback: Hold train at current station.",
            "maintenance_task": "Investigate system error."
        }
