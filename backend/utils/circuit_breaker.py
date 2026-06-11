from circuitbreaker import circuit
import logging

class FallbackException(Exception):
    pass

def circuit_breaker_logger(cb):
    logging.warning(f"Circuit Breaker {cb.name} is now {cb.state}")

# We configure 5 failures allowed before opening circuit
def create_circuit_breaker(name: str):
    return circuit(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=Exception,
        name=name
    )
