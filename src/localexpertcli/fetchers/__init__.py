"""Fetchers module for localexpertcli.

This module contains concrete implementations of BaseFetcher
for different protocols and sources (HTTP, file://, etc.).

Available implementations:
    - HttpFetcher: Fetch content via HTTP/HTTPS using httpx with retry logic
    - FileFetcher: Fetch content from local files (planned)
    - RetryFetcher: Wrapper that adds retry logic to any fetcher (planned)
"""

from localexpertcli.fetchers.http_fetcher import HttpFetcher

__all__ = ["HttpFetcher"]
