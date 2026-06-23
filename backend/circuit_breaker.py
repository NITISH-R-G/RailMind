import time
import logging

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            if self.state != "OPEN":
                logger.warning(f"Circuit Breaker OPEN. Too many failures ({self.failure_count}).")
            self.state = "OPEN"

    def record_success(self):
        if self.state == "HALF_OPEN":
            logger.info("Circuit Breaker CLOSED. Service recovered.")
        self.failure_count = 0
        self.state = "CLOSED"

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit Breaker HALF_OPEN. Attempting recovery.")
                return True
            return False
        if self.state == "HALF_OPEN":
            return True
        return True

anthropic_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
twilio_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
