"""URL utility functions for scope control and normalization.

This module provides functions for URL normalization and scope control
to ensure crawlers stay within their designated boundaries.
"""

from urllib.parse import urlparse, urlunparse
from typing import Optional


def normalize_url(url: str) -> str:
    """Normalize URL for consistent comparison.

    Removes trailing slashes and fragment identifiers to ensure
    URLs can be compared consistently.

    Args:
        url: The URL to normalize.

    Returns:
        Normalized URL string without trailing slash or fragment.

    Example:
        >>> normalize_url("https://example.com/page/#section")
        'https://example.com/page'
        >>> normalize_url("https://example.com/path/")
        'https://example.com/path'
    """
    parsed = urlparse(url)

    # Remove fragment (everything after #)
    # Reconstruct URL without fragment
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path.rstrip('/'),  # Remove trailing slash from path
        parsed.params,
        parsed.query,
        ''  # Remove fragment
    ))

    return normalized


def is_same_subdomain(url: str, base_url: str) -> bool:
    """Check if URL belongs to the same subdomain as base_url.

    This function compares the full netloc (hostname + port) of both URLs
    to determine if they belong to the same subdomain. This prevents
    cross-subdomain crawling (e.g., docs.example.com vs blog.example.com).

    Args:
        url: The URL to check.
        base_url: The base URL to compare against.

    Returns:
        True if the URL belongs to the same subdomain, False otherwise.

    Example:
        >>> is_same_subdomain("https://docs.example.com/page", "https://docs.example.com/")
        True
        >>> is_same_subdomain("https://blog.example.com/page", "https://docs.example.com/")
        False
        >>> is_same_subdomain("https://example.com/page", "https://www.example.com/")
        False
    """
    url_parsed = urlparse(url)
    base_parsed = urlparse(base_url)

    # Compare netloc (includes hostname and optional port)
    # This ensures docs.example.com != blog.example.com
    return url_parsed.netloc == base_parsed.netloc


def get_url_path(url: str) -> str:
    """Extract path component from URL.

    Returns the path portion of a URL, which can be used for
    generating filenames or organizing crawled content.

    Args:
        url: The URL to extract the path from.

    Returns:
        The path component of the URL, or '/' if no path exists.

    Example:
        >>> get_url_path("https://example.com/docs/guide")
        '/docs/guide'
        >>> get_url_path("https://example.com")
        '/'
    """
    parsed = urlparse(url)
    return parsed.path if parsed.path else '/'


def get_domain(url: str) -> Optional[str]:
    """Extract the registered domain from a URL.

    This extracts the main domain (e.g., "example.com" from "docs.example.com").
    Useful for logging and categorization purposes.

    Args:
        url: The URL to extract the domain from.

    Returns:
        The registered domain, or None if the URL is invalid.

    Example:
        >>> get_domain("https://docs.example.com/page")
        'example.com'
        >>> get_domain("https://blog.sub.example.co.uk/article")
        'example.co.uk'
    """
    parsed = urlparse(url)
    if not parsed.netloc:
        return None

    # Remove port if present
    hostname = parsed.netloc.split(':')[0]

    # Split hostname into parts
    parts = hostname.split('.')

    # Handle simple cases
    if len(parts) <= 2:
        return hostname

    # For more complex domains, return last two parts
    # This is a simplified approach - for production use, consider
    # using the tldextract library for accurate domain extraction
    return '.'.join(parts[-2:])


def is_http_url(url: str) -> bool:
    """Check if URL uses HTTP or HTTPS protocol.

    Args:
        url: The URL to check.

    Returns:
        True if the URL uses http or https scheme, False otherwise.

    Example:
        >>> is_http_url("https://example.com")
        True
        >>> is_http_url("ftp://files.example.com")
        False
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https')
    except Exception:
        return False
