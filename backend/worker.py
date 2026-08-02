import asyncio
import os
import uuid
import time
import logging
from datetime import datetime

from arq import worker, Retry # type: ignore
from arq.connections import RedisSettings # type: ignore

from backend.agents.state import AgentState
from backend.agents.graph import railmind_graph
from backend.services.db_client import db_client

logger = logging.getLogger(__name__)

async def startup(ctx):
    logger.info("Starting ARQ worker...")
    await db_client.init_indexes()

async def shutdown(ctx):
    logger.info("Shutting down ARQ worker...")

async def check_rate_limit(redis_client, key: str, capacity: int, window_sec: int):
    """
    Redis-backed sliding-window token bucket using ZSET.
    """
    now = time.time()
    window_start = now - window_sec

    # Remove older entries
    await redis_client.zremrangebyscore(key, 0, window_start)

    # Count current entries
    current_count = await redis_client.zcard(key)
    if current_count >= capacity:
        raise ValueError(f"Rate limit exceeded. Try again in {window_sec}s.")

    # Add new request timestamp
    await redis_client.zadd(key, {str(uuid.uuid4()): now})

async def process_train_telemetry(ctx, raw_telemetry_chunk: list):
    """
    Directly injects parsed HTTP/WebSocket telemetry into the LangGraph state.
    """
    redis_client = ctx["redis"]
    try:
        # Enforce rate limit (max 5 requests per second)
        await check_rate_limit(redis_client, "worker_telemetry_rl", capacity=5, window_sec=1)
    except ValueError as e:
        logger.warning(f"Rate limit hit: {e}. Deferring job.")
        raise Retry(defer=1)

    try:
        initial_state = AgentState(
            raw_train_data=raw_telemetry_chunk,  # Injected directly, skipping blocking fetches
            anomalies=[],
            claude_reasoning="",
            reroute_plan=None,
            department_tasks=[],
            sms_alerts_sent=[],
            incident_report=None,
            loop_count=0,
            should_continue=False,
            last_api_call=datetime.utcnow().isoformat(),
            railways_latency_ms=0,
            ai_latency_ms=0,
            processed_trains=[],
            target_trains=[]
        )

        thread_id = f"arq_telemetry_{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}

        logger.info(f"Invoking graph with {len(raw_telemetry_chunk)} telemetry records...")
        result = await railmind_graph.ainvoke(initial_state, config)
        logger.info(f"Graph invocation completed with loop_count {result.get('loop_count')}")
    except Exception as e:
        logger.error(f"Agent graph error in worker: {e}")

async def run_agent_graph(ctx, train_numbers: list):
    """
    Legacy entry point. Maintained for backward compatibility.
    """
    pass

# Provide the background poller function that enqueues jobs
async def poll_railways_api(ctx):
    """
    Periodic job that enqueue the run_agent_graph job.
    """
    # Dynamic train numbers to ingest
    train_numbers = [
        "12301", "12951", "12001", "12259", "12565",
        "11057", "12627", "12625", "12621", "12615",
        "12309", "12721", "12229", "12311", "12641"
    ]
    logger.info("Enqueuing run_agent_graph job...")
    await ctx["redis"].enqueue_job("run_agent_graph", train_numbers)

class WorkerSettings:
    functions = [process_train_telemetry, run_agent_graph]
    cron_jobs = [
        worker.cron(poll_railways_api, minute=set(range(60)))
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings(host=os.getenv("REDIS_HOST", "localhost"), port=6379)
