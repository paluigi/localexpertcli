"""Services module for localexpertcli.

This module contains service classes that orchestrate the fetch-parse-process
pipeline and provide high-level functionality for web crawling.

Classes:
    CrawlerService: Main service for orchestrating the crawling workflow.
    CrawlerConfig: Configuration for the crawler service.
    CrawlResult: Result of a crawl operation.
    RateLimiter: Rate limiter for polite web crawling.
    RateLimiterConfig: Configuration for the rate limiter.

Functions:
    normalize_url: Normalize URL for consistent comparison.
    is_same_subdomain: Check if URL belongs to the same subdomain.
    get_url_path: Extract path component from URL.
    get_domain: Extract the registered domain from a URL.
    is_http_url: Check if URL uses HTTP or HTTPS protocol.
"""

from localexpertcli.services.crawler import CrawlerService, CrawlerConfig, CrawlResult
from localexpertcli.services.rate_limiter import RateLimiter, RateLimiterConfig
from localexpertcli.services.url_utils import (
    normalize_url,
    is_same_subdomain,
    get_url_path,
    get_domain,
    is_http_url,
)

__all__ = [
    # Crawler
    "CrawlerService",
    "CrawlerConfig",
    "CrawlResult",
    # Rate Limiter
    "RateLimiter",
    "RateLimiterConfig",
    # URL Utils
    "normalize_url",
    "is_same_subdomain",
    "get_url_path",
    "get_domain",
    "is_http_url",
]
