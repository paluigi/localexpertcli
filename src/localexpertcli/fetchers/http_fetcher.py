"""HTTP fetcher implementation using httpx with tenacity retry logic.

This module provides the HttpFetcher class for fetching content from HTTP/HTTPS
URLs with automatic retry logic using the tenacity library.
"""

import logging
import time
from typing import Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryCallState,
)

from localexpertcli.core.fetcher import BaseFetcher, FetchResult

logger = logging.getLogger(__name__)


def _make_retry_decorator(max_retries: int):
    """Create a retry decorator with dynamic max_retries configuration.
    
    Args:
        max_retries: Maximum number of retry attempts.
    
    Returns:
        A retry decorator configured with the specified max_retries.
    """
    return retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_random_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.HTTPStatusError,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


class HttpFetcher(BaseFetcher):
    """HTTP fetcher using httpx with tenacity retry logic.
    
    This fetcher handles HTTP/HTTPS URLs with automatic retry logic for
    transient failures (timeouts, network errors, 5xx server errors).
    
    Attributes:
        max_retries: Maximum number of retry attempts for failed requests.
        timeout: Request timeout in seconds.
        user_agent: User-Agent header sent with requests.
    
    Example:
        >>> fetcher = HttpFetcher(max_retries=3, timeout=30.0)
        >>> result = fetcher.fetch("https://example.com")
        >>> print(result.status_code)
        200
        >>> fetcher.close()
    """
    
    def __init__(
        self,
        max_retries: int = 5,
        timeout: float = 30.0,
        user_agent: str = "LocalExpertCLI/0.1.0",
    ):
        """Initialize the HTTP fetcher.
        
        Args:
            max_retries: Maximum number of retry attempts (default: 5).
            timeout: Request timeout in seconds (default: 30.0).
            user_agent: User-Agent header value (default: "LocalExpertCLI/0.1.0").
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self.user_agent = user_agent
        self._client: Optional[httpx.Client] = None
        
        # Create the retry decorator with instance-level configuration
        self._retry_decorator = _make_retry_decorator(max_retries)
    
    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client with lazy initialization.
        
        Returns:
            The httpx.Client instance.
        """
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            )
        return self._client
    
    def fetch(self, url: str) -> FetchResult:
        """Fetch content from a URL with retry logic.
        
        This method fetches content from the specified URL with automatic
        retry logic for transient failures. 4xx client errors are returned
        without retrying, while 5xx server errors trigger retries.
        
        Args:
            url: The URL to fetch content from.
        
        Returns:
            FetchResult containing the fetched content and metadata.
        
        Raises:
            httpx.TimeoutException: If the request times out after all retries.
            httpx.NetworkError: If a network error occurs after all retries.
            httpx.HTTPStatusError: If a 5xx error occurs after all retries.
        """
        # Apply retry decorator dynamically
        @self._retry_decorator
        def _fetch_with_retry() -> httpx.Response:
            client = self._get_client()
            response = client.get(url)
            
            # For 5xx errors, raise HTTPStatusError to trigger retry
            if response.is_server_error:
                response.raise_for_status()
            
            return response
        
        start_time = time.time()
        
        try:
            response = _fetch_with_retry()
            elapsed = time.time() - start_time
            
            return FetchResult(
                url=str(response.url),
                content=response.text,
                status_code=response.status_code,
                headers=dict(response.headers),
                elapsed_seconds=elapsed,
            )
        except httpx.HTTPStatusError as e:
            # 4xx errors should be returned, not raised
            # This handles cases where raise_for_status() was called on 4xx
            if e.response and 400 <= e.response.status_code < 500:
                elapsed = time.time() - start_time
                return FetchResult(
                    url=str(e.response.url),
                    content=e.response.text,
                    status_code=e.response.status_code,
                    headers=dict(e.response.headers),
                    elapsed_seconds=elapsed,
                )
            # Re-raise 5xx errors (should not reach here after retries exhausted)
            raise
    
    def close(self) -> None:
        """Close the HTTP client and release resources.
        
        This method should be called when the fetcher is no longer needed
        to properly close the HTTP connection pool.
        """
        if self._client is not None:
            self._client.close()
            self._client = None
