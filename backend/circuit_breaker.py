import asyncio
import time
import logging
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED" # CLOSED, OPEN, HALF_OPEN

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit Breaker opened! Failures: {self.failures}")

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit Breaker half-open, trying...")
            else:
                logger.error("Circuit Breaker is OPEN. Executing fallback.")
                raise Exception("Circuit Breaker is OPEN")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            if self.state == "HALF_OPEN":
                logger.info("Circuit Breaker recovered, closing.")
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            logger.error(f"Function call failed: {e}")
            raise

# Global circuit breakers
ai_circuit_breaker = CircuitBreaker()
twilio_circuit_breaker = CircuitBreaker()
