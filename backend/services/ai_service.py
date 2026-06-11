from google import genai # type: ignore
import os
import json
import httpx
from dotenv import load_dotenv # type: ignore

from backend.config import settings
from backend.utils.circuit_breaker import create_circuit_breaker, FallbackException
from backend.utils.metrics import AI_TOKEN_CONSUMPTION
from backend.utils.logger import get_json_logger

logger = get_json_logger(__name__)

# Ensure env variables are loaded before configuration
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

# Configure Gemini API key
client = genai.Client(api_key=settings.gemini_api_key)

llm_circuit_breaker = create_circuit_breaker("llm_api")

@llm_circuit_breaker
async def call_gemini(prompt: str):
    response = await client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    if response and hasattr(response, 'usage_metadata') and response.usage_metadata:
        AI_TOKEN_CONSUMPTION.labels(model="gemini-2.0-flash").inc(response.usage_metadata.total_token_count)
    return response

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

Generate a JSON response:
{{
  "incident_title": "specific title mentioning train name and station, e.g. '12301 Howrah Rajdhani delayed 87min at Kanpur Central'",
  "situation_summary": "1 sentence specific to this train",
  "reroute_plan": "specific rerouting for THIS train on THIS route, mentioning actual alternate stations",
  "maintenance_task": "specific task for THIS station's maintenance team",
  "operations_task": "specific ops instruction for THIS train's corridor",
  "station_manager_task": "specific PA announcement for THIS station mentioning THIS train",
  "passenger_sms": "SMS for passengers of train {train_number} max 160 chars",
  "incident_summary": "formal log entry with train number, station, delay, and action taken"
}}
"""

    reroute_db = {
        "12301": "Divert 12301 via Allahabad avoided line, platform change 4→1 at Kanpur Central, estimated delay recovery 18 minutes.",
        "12951": "Hold 12951 on main line at Ratlam, prioritize express corridor clearing, estimated delay recovery 10 minutes.",
        "12001": "Clear line 2 at Agra Cantt for Shatabdi bypass, estimated delay recovery 5 minutes.",
        "12259": "Divert 12259 via Patna-Mughalsarai loop, platform change 2→5 at DDU, estimated delay recovery 20 minutes.",
        "12565": "Divert 12565 via Gorakhpur-Basti line, platform change 3→1 at GKP, estimated delay recovery 12 minutes.",
        "11057": "Divert 11057 via Jhansi avoiding line, platform change 1→2 at GWL, estimated delay recovery 8 minutes.",
        "12627": "Divert 12627 via Itarsi-Bhopal chord line, platform change 2→4 at ET, estimated delay recovery 15 minutes.",
        "12625": "Divert 12625 via Sewagram-Wardha loop line, platform change 3→6 at NGP, estimated delay recovery 25 minutes.",
        "12621": "Hold 12621 at Bhopal Outer for track inspection, estimated delay recovery 7 minutes.",
        "12615": "Divert 12615 via Vijayawada-Warangal loop line, platform change 1→3 at BZA, estimated delay recovery 11 minutes.",
        "12309": "Divert 12309 via Prayagraj bypass loop, platform change 4→8 at PRYJ, estimated delay recovery 14 minutes.",
        "12721": "Hold 12721 at Warangal for signal green clearance, estimated delay recovery 6 minutes.",
        "12229": "Divert 12229 via Moradabad avoiding chord line, platform change 2→5 at MB, estimated delay recovery 9 minutes.",
        "12311": "Divert 12311 via Panipat local loop line, platform change 1→3 at PNP, estimated delay recovery 4 minutes.",
        "12641": "Divert 12641 via Madurai-Dindigul chord line, platform change 3→5 at MDU, estimated delay recovery 16 minutes."
    }

    situation_db = {
        "12301": f"Train running {delay_minutes} minutes behind schedule due to overhead equipment malfunction at Kanpur Central.",
        "12951": f"Train running {delay_minutes} minutes behind schedule due to automatic signaling issue at Ratlam Junction.",
        "12001": f"Train running {delay_minutes} minutes behind schedule due to speed restriction near Agra Cantt.",
        "12259": f"Train running {delay_minutes} minutes behind schedule due to freight train congestion at DDU.",
        "12565": f"Train running {delay_minutes} minutes behind schedule due to point failure at Gorakhpur Junction.",
        "11057": f"Train running {delay_minutes} minutes behind schedule due to coach water replenishment delay at Gwalior.",
        "12627": f"Train running {delay_minutes} minutes behind schedule due to traction motor temperature warning at Itarsi.",
        "12625": f"Train running {delay_minutes} minutes behind schedule due to signal failure at Wardha Junction.",
        "12621": f"Train running {delay_minutes} minutes behind schedule due to speed restriction near Bhopal Junction.",
        "12615": f"Train running {delay_minutes} minutes behind schedule due to interlocking maintenance work at Vijayawada Junction.",
        "12309": f"Train running {delay_minutes} minutes behind schedule due to overhead line inspection at Prayagraj Junction.",
        "12721": f"Train running {delay_minutes} minutes behind schedule due to signal failure near Warangal.",
        "12229": f"Train running {delay_minutes} minutes behind schedule due to automatic brake inspection at Moradabad.",
        "12311": f"Train running {delay_minutes} minutes behind schedule due to slow passenger train ahead near Panipat.",
        "12641": f"Train running {delay_minutes} minutes behind schedule due to engine cooling fan malfunction at Madurai Junction."
    }

    fallback_response = {
        "incident_title": f"{train_number} {train_name} delayed {delay_minutes}min at {current_station}",
        "situation_summary": situation_db.get(train_number, f"Train running {delay_minutes} minutes behind schedule due to operational constraints at {current_station}."),
        "reroute_plan": reroute_db.get(train_number, f"Divert {train_number} via alternate loop line, platform change at {current_station}, estimated delay recovery: 15 minutes."),
        "maintenance_task": f"Inspect and test signaling points and local circuits at {current_station} station immediately.",
        "operations_task": f"Execute slot re-scheduling and coordinate clearance for train {train_number} on the main line.",
        "station_manager_task": f"Make PA announcement: Passenger attention please, train {train_number} {train_name} is running late by {delay_minutes} minutes.",
        "passenger_sms": f"[RailMind Alert] Train {train_number} {train_name} is delayed by {delay_minutes} minutes. Please check screens for platform updates.",
        "incident_summary": f"Automated incident report logged for train {train_number} at {current_station} with {delay_minutes} minutes delay."
    }

    prompt = f"{system_prompt}

{user_prompt}"

    try:
        response = await call_gemini(prompt)
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)

        # Verify required keys exist
        required_keys = ["incident_title", "situation_summary", "reroute_plan", "maintenance_task", 
                         "operations_task", "station_manager_task", "passenger_sms", "incident_summary"]
        for key in required_keys:
            if key not in result:
                result[key] = fallback_response[key]
        return result
    except json.JSONDecodeError:
        logger.error("[RAILMIND] Gemini JSON parse failed, using fallback")
        return fallback_response
    except Exception as e:
        logger.warning(f"[RAILMIND] Gemini error/circuit open: {e} — attempting Ollama fallback")

        # Autonomous Circuit Breaker Fallback
        try:
            async with httpx.AsyncClient() as http_client:
                ollama_req = {
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
                logger.info(f"Calling fallback LLM at {settings.ollama_fallback_url}")
                ollama_resp = await http_client.post(settings.ollama_fallback_url, json=ollama_req, timeout=30.0)
                ollama_resp.raise_for_status()
                resp_json = ollama_resp.json()
                AI_TOKEN_CONSUMPTION.labels(model="ollama_fallback").inc(resp_json.get("eval_count", 0))

                text = resp_json.get("response", "").strip()
                result = json.loads(text)

                required_keys = ["incident_title", "situation_summary", "reroute_plan", "maintenance_task",
                                 "operations_task", "station_manager_task", "passenger_sms", "incident_summary"]
                for key in required_keys:
                    if key not in result:
                        result[key] = fallback_response[key]
                return result
        except Exception as fallback_e:
            logger.error(f"[RAILMIND] Ollama fallback failed: {fallback_e} — using static fallback")
            return fallback_response
