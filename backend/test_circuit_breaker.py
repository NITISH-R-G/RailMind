import pytest
import asyncio
from backend.circuit_breaker import CircuitBreaker

@pytest.mark.asyncio
async def test_circuit_breaker_failures():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

    @cb
    async def failing_func():
        raise ValueError("Intentional Failure")

    with pytest.raises(ValueError):
        await failing_func()

    with pytest.raises(ValueError):
        await failing_func()

    assert cb.state == "OPEN"

    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        await failing_func()

    await asyncio.sleep(1.1)

    # After sleep, it should be HALF_OPEN, attempt execution and fail again
    with pytest.raises(ValueError):
        await failing_func()

    assert cb.state == "OPEN"

@pytest.mark.asyncio
async def test_circuit_breaker_recovery():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

    should_fail = True

    @cb
    async def maybe_failing_func():
        if should_fail:
            raise ValueError("Intentional Failure")
        return "Success"

    with pytest.raises(ValueError):
        await maybe_failing_func()

    with pytest.raises(ValueError):
        await maybe_failing_func()

    assert cb.state == "OPEN"

    await asyncio.sleep(1.1)
    should_fail = False

    result = await maybe_failing_func()
    assert result == "Success"
    assert cb.state == "CLOSED"
    assert cb.failures == 0
