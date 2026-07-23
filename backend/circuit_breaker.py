import logging
import asyncio
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = reset_timeout_seconds
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time: Optional[float] = None
        self.lock = asyncio.Lock()

    async def _handle_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_failure_time = asyncio.get_event_loop().time()
            logger.warning("Circuit Breaker OPENED. Threshold reached: %s", self.failure_threshold)

    async def _handle_success(self):
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
            self.last_failure_time = None
            logger.info("Circuit Breaker CLOSED. Service recovered.")

    async def can_execute(self) -> bool:
        async with self.lock:
            if self.state == "CLOSED":
                return True
            elif self.state == "OPEN":
                current_time = asyncio.get_event_loop().time()
                if self.last_failure_time and (current_time - self.last_failure_time) >= self.reset_timeout_seconds:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit Breaker HALF_OPEN. Testing connection.")
                    return True
                return False
            elif self.state == "HALF_OPEN":
                # Only allow one request to test the waters if half-open
                return True
        return False

    async def execute(self, fallback_func: Callable, target_func: Callable, *args, **kwargs) -> Any:
        can_exec = await self.can_execute()
        if not can_exec:
            logger.warning("Circuit breaker is OPEN. Executing fallback.")
            return await fallback_func(*args, **kwargs)

        try:
            result = await target_func(*args, **kwargs)
            async with self.lock:
                await self._handle_success()
            return result
        except Exception as e:
            logger.error("Execution failed: %s", e, exc_info=True)
            async with self.lock:
                await self._handle_failure()
            logger.warning("Executing fallback after failure.")
            return await fallback_func(*args, **kwargs)

# Global Circuit Breakers
llm_circuit_breaker = CircuitBreaker()
twilio_circuit_breaker = CircuitBreaker()
