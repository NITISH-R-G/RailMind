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

# Token Bucket Rate Limiter
class RedisTokenBucketRateLimiter:
    def __init__(self, capacity: int, fill_rate: float, redis_client):
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.redis = redis_client
        self.key = "arq_rate_limit"

    async def consume(self, tokens: int = 1):
        now = time.time()
        window_start = now - (self.capacity / self.fill_rate)

        pipeline = self.redis.pipeline()
        pipeline.zremrangebyscore(self.key, "-inf", window_start)
        pipeline.zcard(self.key)
        results = await pipeline.execute()

        current_tokens = results[1]

        if current_tokens + tokens > self.capacity:
            raise ValueError(f"Rate limit exceeded. Requesting {tokens}, but capacity is full.")

        # Add new token request timestamps to sorted set
        add_pipeline = self.redis.pipeline()
        for i in range(tokens):
            add_pipeline.zadd(self.key, {f"{now}-{uuid.uuid4()}": now})
        await add_pipeline.execute()


async def startup(ctx):
    logger.info("Starting ARQ worker...")
    await db_client.init_indexes()

    # Store global rate limiter instance
    ctx['rate_limiter'] = RedisTokenBucketRateLimiter(
        capacity=5,
        fill_rate=5.0,
        redis_client=ctx['redis']
    )

async def shutdown(ctx):
    logger.info("Shutting down ARQ worker...")


async def process_train_telemetry(ctx, telemetry_chunks: list):
    """
    Decoupled task to run the LangGraph agent graph directly processing incoming chunks.
    """
    rate_limiter = ctx['rate_limiter']
    try:
        # Rate limit enforcement
        await rate_limiter.consume(1)
    except ValueError as e:
        logger.error(f"Rate limiting in worker: {e}. Retrying job.")
        raise Retry(defer=1)

    try:
        initial_state = AgentState(
            raw_train_data=telemetry_chunks,
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
            target_trains=[]
        )

        thread_id = f"arq_worker_{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}

        logger.info(f"Invoking graph with {len(telemetry_chunks)} telemetry chunks...")
        result = await railmind_graph.ainvoke(initial_state, config)
        logger.info(f"Graph invocation completed with loop_count {result.get('loop_count')}")
    except Exception as e:
        logger.error(f"Agent graph error in worker: {e}")

class WorkerSettings:
    functions = [process_train_telemetry]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings(host=os.getenv("REDIS_HOST", "localhost"), port=6379)
