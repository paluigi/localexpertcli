"""Rate limiter for polite web crawling.

This module provides rate limiting functionality to ensure crawlers
are polite and don't overwhelm target servers with requests.
"""

import random
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimiterConfig:
    """Configuration for the rate limiter.

    Attributes:
        min_delay: Minimum delay between requests in seconds.
        max_delay: Maximum delay between requests in seconds.
    """

    min_delay: float = 1.0
    max_delay: float = 3.0

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.min_delay < 0:
            raise ValueError("min_delay must be non-negative")
        if self.max_delay < self.min_delay:
            raise ValueError("max_delay must be greater than or equal to min_delay")


class RateLimiter:
    """Rate limiter for controlling request frequency.

    Implements a random delay between requests to avoid overwhelming
    target servers and to appear more like natural browsing behavior.

    Example:
        >>> config = RateLimiterConfig(min_delay=1.0, max_delay=3.0)
        >>> limiter = RateLimiter(config)
        >>> # Before each request:
        >>> limiter.wait()  # Sleeps for 1.0-3.0 seconds
        >>> fetcher.fetch(url)
    """

    def __init__(self, config: Optional[RateLimiterConfig] = None) -> None:
        """Initialize the rate limiter.

        Args:
            config: Configuration for rate limiting. If None, uses defaults
                   (min_delay=1.0, max_delay=3.0).
        """
        self.config = config or RateLimiterConfig()
        self._last_request_time: Optional[float] = None

    def wait(self) -> None:
        """Wait for a random duration between min_delay and max_delay.

        This method should be called before each request to ensure
        polite crawling behavior. The actual delay is randomly selected
        from the range [min_delay, max_delay] to add jitter and appear
        more like natural browsing.

        If called immediately after initialization, waits for the full
        random delay. If called in quick succession, ensures at least
        min_delay seconds have passed since the last request.
        """
        # Calculate random delay for this request
        delay = random.uniform(self.config.min_delay, self.config.max_delay)

        # If we've made a previous request, account for elapsed time
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            # Only sleep if we haven't already waited long enough
            if elapsed < delay:
                time.sleep(delay - elapsed)
        else:
            # First request, just wait the random delay
            time.sleep(delay)

        # Record this request time
        self._last_request_time = time.time()

    def reset(self) -> None:
        """Reset the rate limiter state.

        Clears the last request time, effectively starting fresh.
        Useful when beginning a new crawling session.
        """
        self._last_request_time = None

    @property
    def min_delay(self) -> float:
        """Get the minimum delay between requests."""
        return self.config.min_delay

    @property
    def max_delay(self) -> float:
        """Get the maximum delay between requests."""
        return self.config.max_delay
