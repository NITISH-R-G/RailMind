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

async def process_train_telemetry(ctx, raw_train_data: list):
    """
    Decoupled task to run the LangGraph agent graph directly with raw telemetry chunks.
    """
    try:
        initial_state = AgentState(
            raw_train_data=raw_train_data,
            anomalies=[],
            claude_reasoning="",
            reroute_plan=None,
            department_tasks=[],
            sms_alerts_sent=[],
            incident_report=None,
            loop_count=0,
            should_continue=False,
            last_api_call="Never",
            railways_latency_ms=0,
            ai_latency_ms=0,
            processed_trains=[],
            # In decentralized ingestion, target_trains isn't needed for fetching
            target_trains=[t.get("train_number") for t in raw_train_data if t.get("train_number")]
        )

        thread_id = f"arq_worker_{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}

        logger.info(f"Invoking graph for telemetry chunk of {len(raw_train_data)} trains...")
        result = await railmind_graph.ainvoke(initial_state, config)
        logger.info(f"Graph invocation completed with loop_count {result.get('loop_count')}")
    except Exception as e:
        logger.error(f"Agent graph error in worker: {e}")


class WorkerSettings:
    functions = [process_train_telemetry]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings(host=os.getenv("REDIS_HOST", "localhost"), port=6379)
