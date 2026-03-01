"""Main crawler service for orchestrating the crawling process.

This module provides the CrawlerService class that orchestrates the entire
crawling workflow, including URL discovery, content fetching, parsing, and
saving to files.
"""

import logging
import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from localexpertcli.core.fetcher import BaseFetcher, FetchResult
from localexpertcli.core.parser import BaseParser, ParseResult
from localexpertcli.core.processor import BaseProcessor, ProcessorPipeline, ProcessorContext
from localexpertcli.services.url_utils import normalize_url, is_same_subdomain, get_url_path
from localexpertcli.services.rate_limiter import RateLimiter, RateLimiterConfig

logger = logging.getLogger(__name__)


@dataclass
class CrawlerConfig:
    """Configuration for the crawler service.

    Attributes:
        start_url: The starting URL for crawling.
        output_dir: Directory where crawled content will be saved.
        max_retries: Maximum number of retry attempts for failed requests.
        dry_run: If True, only discover URLs without downloading content.
        rate_limiter_config: Configuration for rate limiting. If None, uses defaults.
    """

    start_url: str
    output_dir: Path
    max_retries: int = 5
    dry_run: bool = False
    rate_limiter_config: Optional[RateLimiterConfig] = None


@dataclass
class CrawlResult:
    """Result of a crawl operation.

    Attributes:
        pages_discovered: Total number of unique URLs discovered.
        pages_downloaded: Number of pages successfully downloaded and converted.
        pages_failed: Number of pages that failed to download.
        output_files: List of paths to saved markdown files.
    """

    pages_discovered: int
    pages_downloaded: int
    pages_failed: int
    output_files: list[Path] = field(default_factory=list)


class CrawlerService:
    """Service for orchestrating the web crawling process.

    This service implements a two-phase crawling strategy:
    1. Phase 1 (Mapping): Discover all unique URLs within scope using BFS traversal.
    2. Phase 2 (Download): Download and convert each page to Markdown.

    The crawler respects scope boundaries (same subdomain) and implements
    politeness through rate limiting.

    Example:
        >>> from pathlib import Path
        >>> from localexpertcli.fetchers.http_fetcher import HttpFetcher
        >>> from localexpertcli.parsers.html_parser import HtmlToMarkdownParser
        >>>
        >>> config = CrawlerConfig(
        ...     start_url="https://docs.example.com/",
        ...     output_dir=Path("./output"),
        ...     dry_run=False
        ... )
        >>> fetcher = HttpFetcher()
        >>> parser = HtmlToMarkdownParser()
        >>> crawler = CrawlerService(config, fetcher, parser)
        >>> result = crawler.crawl()
        >>> print(f"Downloaded {result.pages_downloaded} pages")
    """

    def __init__(
        self,
        config: CrawlerConfig,
        fetcher: BaseFetcher,
        parser: BaseParser,
        processors: Optional[list[BaseProcessor]] = None,
    ) -> None:
        """Initialize the crawler service.

        Args:
            config: Configuration for the crawler.
            fetcher: Fetcher instance for retrieving web content.
            parser: Parser instance for converting content to markdown.
            processors: Optional list of processors for content transformation.
        """
        self.config = config
        self.fetcher = fetcher
        self.parser = parser
        self.pipeline = ProcessorPipeline(processors or [])
        self.rate_limiter = RateLimiter(config.rate_limiter_config)
        self._visited: set[str] = set()
        self._to_visit: set[str] = set()

    def crawl(self) -> CrawlResult:
        """Execute the crawl process.

        Performs a two-phase crawl:
        1. Phase 1: Map all unique URLs within scope (BFS traversal).
        2. If dry_run, return early with count of discovered pages.
        3. Phase 2: Download and convert each page to Markdown.

        Returns:
            CrawlResult containing statistics and output file paths.
        """
        logger.info(f"Starting crawl from: {self.config.start_url}")
        logger.info(f"Output directory: {self.config.output_dir}")
        logger.info(f"Dry run mode: {self.config.dry_run}")

        # Phase 1: Map all URLs within scope
        discovered_urls = self._map_urls()
        pages_discovered = len(discovered_urls)

        logger.info(f"Discovered {pages_discovered} unique URLs within scope")

        # If dry run, return early
        if self.config.dry_run:
            logger.info("Dry run complete. No files downloaded.")
            return CrawlResult(
                pages_discovered=pages_discovered,
                pages_downloaded=0,
                pages_failed=0,
                output_files=[],
            )

        # Phase 2: Download and convert each page
        output_files, pages_failed = self._download_and_convert(discovered_urls)
        pages_downloaded = pages_discovered - pages_failed

        logger.info(f"Crawl complete: {pages_downloaded} pages downloaded, {pages_failed} failed")

        return CrawlResult(
            pages_discovered=pages_discovered,
            pages_downloaded=pages_downloaded,
            pages_failed=pages_failed,
            output_files=output_files,
        )

    def _map_urls(self) -> set[str]:
        """Phase 1: Build a set of unique URLs within scope.

        Uses BFS traversal starting from start_url to discover all pages
        within the same subdomain. URLs are normalized before being added
        to the visited set to avoid duplicates.

        Returns:
            Set of normalized URLs within scope.
        """
        # Initialize with the start URL
        start_url_normalized = normalize_url(self.config.start_url)
        queue: deque[str] = deque([start_url_normalized])
        self._visited = set()

        logger.info("Phase 1: Mapping URLs within scope...")

        while queue:
            current_url = queue.popleft()

            # Skip if already visited
            if current_url in self._visited:
                continue

            # Mark as visited
            self._visited.add(current_url)
            logger.debug(f"Mapping: {current_url}")

            try:
                # Wait for rate limiting
                self.rate_limiter.wait()

                # Fetch the page
                fetch_result = self.fetcher.fetch(current_url)

                # Skip non-successful responses
                if fetch_result.status_code != 200:
                    logger.warning(
                        f"Skipping {current_url}: HTTP {fetch_result.status_code}"
                    )
                    continue

                # Parse to extract links
                parse_result = self.parser.parse(fetch_result.content, current_url)

                # Process discovered links
                for link in parse_result.links:
                    # Normalize the link
                    normalized_link = normalize_url(link)

                    # Check if within scope (same subdomain)
                    if not is_same_subdomain(normalized_link, self.config.start_url):
                        logger.debug(f"Out of scope: {normalized_link}")
                        continue

                    # Add to queue if not visited
                    if normalized_link not in self._visited:
                        queue.append(normalized_link)

                logger.debug(f"Found {len(parse_result.links)} links on {current_url}")

            except Exception as e:
                logger.error(f"Error mapping {current_url}: {e}")
                # Continue with other URLs even if one fails
                continue

        logger.info(f"URL mapping complete: {len(self._visited)} unique URLs found")
        return self._visited

    def _download_and_convert(self, urls: set[str]) -> tuple[list[Path], int]:
        """Phase 2: Download content and convert to Markdown.

        Downloads each URL, parses the content, processes it through
        the pipeline, and saves as a Markdown file.

        Args:
            urls: Set of URLs to download and convert.

        Returns:
            Tuple of (list of output file paths, count of failed downloads).
        """
        logger.info("Phase 2: Downloading and converting pages...")

        # Create output directory if it doesn't exist
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        output_files: list[Path] = []
        failed_count = 0
        total = len(urls)

        for index, url in enumerate(urls, 1):
            logger.info(f"Processing [{index}/{total}]: {url}")

            try:
                # Wait for rate limiting
                self.rate_limiter.wait()

                # Fetch the page
                fetch_result = self.fetcher.fetch(url)

                # Skip non-successful responses
                if fetch_result.status_code != 200:
                    logger.warning(
                        f"Failed to download {url}: HTTP {fetch_result.status_code}"
                    )
                    failed_count += 1
                    continue

                # Parse to markdown
                parse_result = self.parser.parse(fetch_result.content, url)

                # Create processor context
                context = ProcessorContext(
                    markdown=parse_result.markdown,
                    source_url=url,
                    title=parse_result.title,
                    metadata=parse_result.metadata,
                )

                # Process through pipeline
                processed_context = self.pipeline.process(context)

                # Save to file
                output_path = self._save_markdown(
                    url, processed_context.markdown, processed_context.title
                )
                output_files.append(output_path)

                logger.debug(f"Saved: {output_path}")

            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                failed_count += 1
                continue

        logger.info(f"Download complete: {len(output_files)} files saved")
        return output_files, failed_count

    def _save_markdown(self, url: str, markdown: str, title: str) -> Path:
        """Save markdown content to a file.

        Generates a safe filename from the URL and title, then saves
        the markdown content to the output directory.

        Args:
            url: The source URL (used for filename generation).
            markdown: The markdown content to save.
            title: The page title (used for filename generation).

        Returns:
            Path to the saved file.
        """
        filename = self._generate_filename(url, title)
        output_path = self.config.output_dir / filename

        # Handle filename collisions by appending a number
        counter = 1
        while output_path.exists():
            stem = output_path.stem
            suffix = output_path.suffix
            output_path = self.config.output_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        # Write the markdown content
        output_path.write_text(markdown, encoding="utf-8")

        return output_path

    def _generate_filename(self, url: str, title: str) -> str:
        """Generate a safe filename from URL and title.

        Creates a filesystem-safe filename based on the URL path or title.
        Falls back to a hash of the URL if neither is available.

        Args:
            url: The source URL.
            title: The page title.

        Returns:
            A safe filename ending with .md extension.
        """
        # Try to use title first if available
        if title:
            # Clean the title for use as filename
            safe_title = self._sanitize_filename(title)
            if safe_title:
                return f"{safe_title}.md"

        # Fall back to URL path
        path = get_url_path(url)
        if path and path != "/":
            # Remove leading slash and clean
            path = path.lstrip("/")
            safe_path = self._sanitize_filename(path)
            if safe_path:
                return f"{safe_path}.md"

        # Last resort: use hash of URL
        url_hash = abs(hash(url))
        return f"page_{url_hash}.md"

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename.

        Removes or replaces characters that are not safe for filesystem use.

        Args:
            name: The string to sanitize.

        Returns:
            A filesystem-safe string, or empty string if result is invalid.
        """
        if not name:
            return ""

        # Replace common separators with underscores
        name = name.replace("/", "_").replace("\\", "_")

        # Remove or replace unsafe characters
        # Keep alphanumeric, underscores, hyphens, and spaces
        name = re.sub(r'[^\w\s\-]', '', name)

        # Replace spaces with underscores
        name = name.replace(" ", "_")

        # Remove consecutive underscores
        name = re.sub(r'_+', '_', name)

        # Remove leading/trailing underscores
        name = name.strip("_")

        # Limit length
        if len(name) > 100:
            name = name[:100]

        return name.lower() if name else ""
