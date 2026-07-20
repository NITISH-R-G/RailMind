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

import redis.asyncio as redis_async

# Redis Sliding Window Rate Limiter
class RedisSlidingWindowRateLimiter:
    def __init__(self, capacity: int, window_seconds: float):
        self.capacity = capacity
        self.window_seconds = window_seconds
        self.redis = redis_async.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
        self.key = "rate_limit:sliding_window"

    async def consume(self, tokens: int = 1):
        now = time.time()
        window_start = now - self.window_seconds

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(self.key, 0, window_start)
            pipe.zcard(self.key)
            results = await pipe.execute()

        current_count = results[1]

        if current_count + tokens > self.capacity:
            raise ValueError(f"Rate limit exceeded. Capacity {self.capacity}, current {current_count}.")

        async with self.redis.pipeline(transaction=True) as pipe:
            for _ in range(tokens):
                # Unique member score
                member = f"{now}-{uuid.uuid4().hex[:8]}"
                pipe.zadd(self.key, {member: now})
            pipe.expire(self.key, int(self.window_seconds * 2))
            await pipe.execute()

# Limit to 5 requests per second
rate_limiter = RedisSlidingWindowRateLimiter(capacity=5, window_seconds=1.0)

async def startup(ctx):
    logger.info("Starting ARQ worker...")
    await db_client.init_indexes()

async def shutdown(ctx):
    logger.info("Shutting down ARQ worker...")

async def process_train_telemetry(ctx, train_numbers: list):
    """
    Decoupled task to run the LangGraph agent graph.
    """
    try:
        # Rate limit enforcement
        await rate_limiter.consume(1)
    except ValueError as e:
        logger.error(f"Rate limiting in worker: {e}. Retrying job.")
        raise Retry(defer=1)  # Retry in 1 second

    try:
        initial_state = AgentState(
            raw_train_data=[],
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
            target_trains=train_numbers
        )

        thread_id = f"arq_worker_{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}

        logger.info(f"Invoking graph for {len(train_numbers)} trains...")
        result = await railmind_graph.ainvoke(initial_state, config)
        logger.info(f"Graph invocation completed with loop_count {result.get('loop_count')}")
    except Exception as e:
        logger.error(f"Agent graph error in worker: {e}")

# Provide the background poller function that enqueues jobs
async def poll_railways_api(ctx):
    """
    Periodic job that enqueue the process_train_telemetry job.
    """
    # Dynamic train numbers to ingest
    train_numbers = [
        "12301", "12951", "12001", "12259", "12565",
        "11057", "12627", "12625", "12621", "12615",
        "12309", "12721", "12229", "12311", "12641"
    ]
    logger.info("Enqueuing process_train_telemetry job...")
    await ctx["redis"].enqueue_job("process_train_telemetry", train_numbers)

class WorkerSettings:
    functions = [process_train_telemetry]
    cron_jobs = [
        # Run every minute
        worker.cron(poll_railways_api, minute=set(range(60)))
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings(host=os.getenv("REDIS_HOST", "localhost"), port=6379)
