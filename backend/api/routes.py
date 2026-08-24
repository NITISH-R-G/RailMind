from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, List
import time

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Check API health and status.
    """
    return {"status": "healthy", "agent": "RailMind"}

@router.post("/telemetry/ingest")
async def ingest_telemetry(request: Request, payload: List[dict]):
    """
    Async endpoint to decouple telemetry ingestion using ARQ.
    """
    redis_client = request.app.state.global_redis_client

    # Rate limit: 100 requests per 60 seconds
    now = time.time()
    window_start = now - 60
    key = "rate_limit:telemetry_ingest"

    try:
        if redis_client:
            # Read current token count
            await redis_client.zremrangebyscore(key, 0, window_start)
            current_requests = await redis_client.zcard(key)
            if current_requests >= 100:
                raise HTTPException(status_code=429, detail="Too Many Requests")

            # Write new token
            await redis_client.zadd(key, {str(now): now})
            await redis_client.expire(key, 60)
    except HTTPException:
        raise
    except Exception as e:
        # Silently fail Redis errors to prevent taking down the endpoint, unless rate limit was exceeded
        print(f"Redis rate limiting error: {e}")

    try:
        pool = request.app.state.redis_pool
        await pool.enqueue_job("process_train_telemetry", payload)
        return {"status": "accepted", "message": "Telemetry enqueued for processing"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to enqueue job: {e}")
