"""HTML to Markdown parser implementation.

This module provides a parser that converts HTML content to Markdown format
using the markitdown library and extracts links using BeautifulSoup.
"""

from io import BytesIO
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from markitdown import MarkItDown
from markitdown._stream_info import StreamInfo

from localexpertcli.core.parser import BaseParser, ParseResult


class HtmlToMarkdownParser(BaseParser):
    """Parser that converts HTML content to Markdown.

    This parser uses markitdown for HTML to Markdown conversion and BeautifulSoup
    for extracting page metadata like title and links.

    Attributes:
        _converter: MarkItDown instance for HTML to Markdown conversion.
    """

    def __init__(self) -> None:
        """Initialize the HTML to Markdown parser."""
        self._converter = MarkItDown()

    def parse(self, content: str, source_url: str) -> ParseResult:
        """Parse HTML content and convert to Markdown.

        Args:
            content: Raw HTML content.
            source_url: The URL the content was fetched from (for resolving relative links).

        Returns:
            ParseResult with markdown, title, extracted links, and metadata.
        """
        # Create BeautifulSoup object for metadata extraction
        soup = BeautifulSoup(content, "html.parser")

        # Extract title
        title = self._extract_title(soup)

        # Extract links
        links = self._extract_links(soup, source_url)

        # Convert HTML to Markdown using markitdown
        # markitdown expects a file-like object, so wrap content in BytesIO
        # Provide StreamInfo with mimetype to ensure proper HTML handling
        content_stream = BytesIO(content.encode("utf-8"))
        stream_info = StreamInfo(mimetype="text/html")
        conversion_result = self._converter.convert(content_stream, stream_info=stream_info)
        markdown = conversion_result.text_content

        # Build metadata
        metadata = {
            "source_url": source_url,
            "original_content_length": len(content),
            "markdown_length": len(markdown),
            "links_count": len(links),
            "conversion_status": "success",
        }

        return ParseResult(
            markdown=markdown,
            title=title,
            links=links,
            metadata=metadata,
        )

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """Extract all links from HTML, resolving relative URLs.

        Finds all anchor tags with href attributes, resolves relative URLs,
        filters out invalid protocols, and returns a unique list of absolute URLs.

        Args:
            soup: BeautifulSoup object of the HTML content.
            base_url: The base URL for resolving relative links.

        Returns:
            List of unique absolute URLs extracted from the HTML.
        """
        links: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()

            # Skip empty hrefs
            if not href:
                continue

            # Skip anchor links (same page navigation)
            if href.startswith("#"):
                continue

            # Skip javascript: and mailto: links
            if href.startswith(("javascript:", "mailto:", "tel:", "data:")):
                continue

            # Resolve relative URLs to absolute URLs
            absolute_url = urljoin(base_url, href)

            # Only include valid HTTP/HTTPS URLs
            if self._is_valid_url(absolute_url):
                links.add(absolute_url)

        return list(links)

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title from HTML.

        Attempts to extract title from <title> tag first, falls back to <h1>
        if title tag is not present or empty.

        Args:
            soup: BeautifulSoup object of the HTML content.

        Returns:
            Extracted title string, or empty string if no title found.
        """
        # Try to get title from <title> tag
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        # Fallback to first <h1> tag
        h1_tag = soup.find("h1")
        if h1_tag:
            # Get text content, handling nested elements
            h1_text = h1_tag.get_text(strip=True)
            if h1_text:
                return h1_text

        return ""

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid for crawling (http/https only).

        Validates that the URL has a proper scheme (http or https) and
        a network location (hostname).

        Args:
            url: The URL to validate.

        Returns:
            True if the URL is a valid HTTP/HTTPS URL, False otherwise.
        """
        try:
            parsed = urlparse(url)
            # Only allow http and https schemes
            if parsed.scheme not in ("http", "https"):
                return False
            # Must have a hostname
            if not parsed.netloc:
                return False
            return True
        except Exception:
            return False
