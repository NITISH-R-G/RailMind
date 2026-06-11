import time
import asyncio

class TokenBucketRateLimiter:
    """
    A simple token bucket rate limiter to handle upstream API throttles.
    """
    def __init__(self, capacity: int, fill_rate: float):
        """
        capacity: Maximum tokens the bucket can hold.
        fill_rate: Tokens added per second.
        """
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.tokens = capacity
        self.last_fill_time = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1):
        """
        Acquire given number of tokens from the bucket, waiting if necessary.
        """
        if tokens > self.capacity:
            raise ValueError(f"Requested {tokens} tokens exceeds bucket capacity of {self.capacity}")

        while True:
            async with self.lock:
                now = time.monotonic()
                time_passed = now - self.last_fill_time
                new_tokens = time_passed * self.fill_rate

                if new_tokens > 0:
                    self.tokens = min(self.capacity, self.tokens + new_tokens)
                    self.last_fill_time = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return
                else:
                    # Need to wait
                    deficit = tokens - self.tokens
                    wait_time = deficit / self.fill_rate

            # Sleep outside the lock so other tasks can proceed when ready
            await asyncio.sleep(wait_time)

# Define a global rate limiter for the Indian Railways API
# Suppose the API allows 5 requests per second max, allowing bursts up to 20
railways_rate_limiter = TokenBucketRateLimiter(capacity=20, fill_rate=5.0)
