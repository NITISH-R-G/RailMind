import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning("Circuit breaker OPENED due to consecutive failures")

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def allow_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        if self.state == "HALF_OPEN":
            return True
        return False

# Global circuit breakers for APIs
anthropic_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
twilio_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=120)

def with_circuit_breaker(breaker: CircuitBreaker, fallback_func=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not breaker.allow_request():
                if fallback_func:
                    logger.warning(f"Circuit breaker open, using fallback for {func.__name__}")
                    return await fallback_func(*args, **kwargs)
                raise CircuitBreakerOpenException(f"Circuit breaker is OPEN for {func.__name__}")

            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                if fallback_func:
                    logger.warning(f"Request failed, using fallback for {func.__name__}. Error: {e}")
                    return await fallback_func(*args, **kwargs)
                raise e
        return wrapper
    return decorator
