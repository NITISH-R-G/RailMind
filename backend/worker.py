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

async def check_rate_limit(redis_conn, key: str = "arq:rate_limit", max_requests: int = 5, window_seconds: int = 1):
    now = time.time()
    window_start = now - window_seconds

    # Use Redis ZSET for atomic sliding-window rate limit
    pipeline = redis_conn.pipeline(transaction=True)
    pipeline.zremrangebyscore(key, 0, window_start)
    pipeline.zadd(key, {str(now): now})
    pipeline.zcard(key)
    pipeline.expire(key, window_seconds + 1)
    results = await pipeline.execute()

    count = results[2]
    if count > max_requests:
        raise ValueError(f"Rate limit exceeded. Requested tokens > {max_requests}")

async def process_train_telemetry(ctx, train_numbers: list):
    """
    Decoupled task to run the LangGraph agent graph with a sliding-window rate limit token bucket.
    """
    redis_conn = ctx["redis"]
    try:
        await check_rate_limit(redis_conn)
    except ValueError as e:
        logger.error(f"Rate limiting in worker: {e}. Retrying job in 1 second.")
        raise Retry(defer=1)

    try:
        from backend.services.railways_api import RailwaysAPIClient, get_cancelled_trains
        import time
        from datetime import datetime

        client = RailwaysAPIClient(api_key=os.getenv("RAILWAYS_API_KEY", "mock_key"))
        start_time = time.time()

        results = await client.get_multiple_trains(train_numbers)
        train_results = []
        for tn in train_numbers:
            found = False
            for r in results:
                if r.get("train_number") == tn:
                    train_results.append(r)
                    found = True
                    break
            if not found:
                from backend.services.railways_api import get_mock_rapidapi_train, parse_rapidapi_train_for_agent
                mock_data = get_mock_rapidapi_train(tn)
                parsed_mock = parse_rapidapi_train_for_agent(mock_data, tn)
                if parsed_mock:
                    train_results.append(parsed_mock)

        cancelled = await get_cancelled_trains()
        live_trains = train_results.copy()
        for train in cancelled:
            live_trains.append({
                "train_number": train.get("TrainNo", "Unknown"),
                "train_name": train.get("TrainName", "Unknown"),
                "status": "cancelled",
                "delay_minutes": 999,
                "passenger_load": "overcrowded",
                "current_station": "Unknown",
                "lat": 20.5937,
                "lng": 78.9629
            })

        latency = int((time.time() - start_time) * 1000)
        last_api_call = datetime.utcnow().isoformat()

        initial_state = AgentState(
            raw_train_data=live_trains,
            anomalies=[],
            claude_reasoning="",
            reroute_plan=None,
            department_tasks=[],
            sms_alerts_sent=[],
            incident_report=None,
            loop_count=0,
            should_continue=False,
            last_api_call=last_api_call,
            railways_latency_ms=latency,
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

async def poll_railways_api(ctx):
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
        worker.cron(poll_railways_api, minute=set(range(60)))
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings(host=os.getenv("REDIS_HOST", "localhost"), port=6379)
