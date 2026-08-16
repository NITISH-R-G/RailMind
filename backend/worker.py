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
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.window_size = 1.0

    async def consume(self, redis_conn, tokens: int = 1):
        now = time.time()
        window_start = now - self.window_size
        key = "rate_limit:sliding_window"

        lua_script = """
        local key = KEYS[1]
        local window_start = tonumber(ARGV[1])
        local now = tonumber(ARGV[2])
        local capacity = tonumber(ARGV[3])
        local req_id = ARGV[4]

        redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
        local count = redis.call('ZCOUNT', key, '-inf', '+inf')

        if count >= capacity then
            return 0
        end

        redis.call('ZADD', key, now, req_id)
        return 1
        """
        req_id = str(uuid.uuid4())

        allowed = await redis_conn.eval(lua_script, 1, key, window_start, now, self.capacity, req_id)
        if not allowed:
            raise ValueError(f"Rate limit exceeded. Capacity {self.capacity}.")

# Limit to 5 requests per second
rate_limiter = RedisTokenBucketRateLimiter(capacity=5, fill_rate=5.0)
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
        await rate_limiter.consume(ctx['redis'], 1)
    except ValueError as e:
        logger.error(f"Rate limiting in worker: {e}. Retrying job.")
        raise Retry(defer=1)  # Retry in 1 second

    try:
        # Instead of doing ingestion inside nodes.py, we could pass train_numbers in state
        # or just trigger it. In our nodes.py, `ingest_node` ignores what we pass and uses a hardcoded list.
        # We will modify nodes.py to read `target_trains` from state, or fallback to the list.

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
            # Inject dynamic configuration
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
    Periodic job that enqueue the run_agent_graph job.
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
