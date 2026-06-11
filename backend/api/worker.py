import os
import logging
import json
from arq import cron
from arq.connections import RedisSettings
from dotenv import load_dotenv
import redis.asyncio as aioredis # type: ignore

from ..agents.graph import railmind_graph
from ..agents.state import AgentState

logger = logging.getLogger(__name__)

# Ensure env variables are loaded
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

async def startup(ctx):
    logger.info("Worker started")
    ctx["redis"] = aioredis.from_url(REDIS_URL, decode_responses=True)

async def shutdown(ctx):
    logger.info("Worker shutdown")
    if "redis" in ctx:
        await ctx["redis"].close()

async def run_ingestion_pipeline(ctx):
    """
    Runs the LangGraph agent graph to ingest and process data.
    This replaces the continuous manual loop in main.py.
    """
    logger.info("Starting scheduled ingestion pipeline run")
    redis = ctx.get("redis")
    try:
        # Load current state from Redis
        state_str = await redis.get("railmind_agent_state") if redis else None
        current_state = json.loads(state_str) if state_str else {}

        initial_state = AgentState(
            raw_train_data=[],
            anomalies=[],
            claude_reasoning="",
            reroute_plan=None,
            department_tasks=[],
            sms_alerts_sent=[],
            incident_report=None,
            loop_count=current_state.get("loop_count", 0),
            should_continue=False,
            last_api_call=current_state.get("last_api_call", "Never"),
            railways_latency_ms=current_state.get("railways_latency_ms", 0),
            ai_latency_ms=current_state.get("ai_latency_ms", 0),
            processed_trains=current_state.get("processed_trains", [])
        )
        # Invoke graph using ainvoke
        result = await railmind_graph.ainvoke(initial_state)

        # Increment loop count on successful iteration
        if result:
            result["loop_count"] = result.get("loop_count", 0) + 1
            # Sync back to Redis
            if redis:
                await redis.set("railmind_agent_state", json.dumps(result))

        logger.info("Completed scheduled ingestion pipeline run")
    except Exception:
        logger.exception("[RAILMIND] Ingestion pipeline error")

class WorkerSettings:
    functions = [run_ingestion_pipeline]
    cron_jobs = [
        cron(run_ingestion_pipeline, minute=set(range(0, 60)), second=0) # Run every minute
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
