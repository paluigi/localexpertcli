"""Base fetcher abstract class and related data classes.

This module provides the abstract base class for all URL fetchers in the
localexpertcli project. Concrete implementations should handle different
protocols (HTTP, HTTPS, file://, etc.) and provide retry/error handling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class FetchResult:
    """Result of a fetch operation.

    Attributes:
        url: The URL that was fetched (may differ from requested URL due to redirects).
        content: The raw content retrieved from the URL.
        status_code: HTTP status code (200 for success, 4xx/5xx for errors).
        headers: Response headers as a dictionary.
        elapsed_seconds: Time taken to complete the fetch operation.
    """

    url: str
    content: str
    status_code: int
    headers: dict
    elapsed_seconds: float


class BaseFetcher(ABC):
    """Abstract base class for URL fetchers.

    Fetchers are responsible for retrieving content from various sources
    (HTTP URLs, local files, etc.). Concrete implementations should handle
    protocol-specific details, error handling, and resource cleanup.

    Example:
        >>> class HttpFetcher(BaseFetcher):
        ...     def __init__(self):
        ...         self._client = httpx.Client()
        ...
        ...     def fetch(self, url: str) -> FetchResult:
        ...         response = self._client.get(url)
        ...         return FetchResult(
        ...             url=str(response.url),
        ...             content=response.text,
        ...             status_code=response.status_code,
        ...             headers=dict(response.headers),
        ...             elapsed_seconds=response.elapsed.total_seconds()
        ...         )
        ...
        ...     def close(self) -> None:
        ...         self._client.close()
    """

    @abstractmethod
    def fetch(self, url: str) -> FetchResult:
        """Fetch content from a URL.

        Args:
            url: The URL to fetch content from.

        Returns:
            FetchResult containing the fetched content and metadata.

        Raises:
            FetchError: If the fetch operation fails.
            TimeoutError: If the request times out.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up resources used by the fetcher.

        This method should be called when the fetcher is no longer needed
        to release any resources (connections, file handles, etc.).
        """
        pass
