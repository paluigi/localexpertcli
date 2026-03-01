"""Base parser abstract class and related data classes.

This module provides the abstract base class for all content parsers in the
localexpertcli project. Concrete implementations should handle different
content types (HTML, PDF, Markdown, etc.) and convert them to a standardized
markdown format.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParseResult:
    """Result of a parse operation.

    Attributes:
        markdown: The parsed content converted to markdown format.
        title: The title of the document (extracted from content or metadata).
        links: List of URLs extracted from the content for crawling purposes.
        metadata: Additional metadata extracted from the content (author, date, etc.).
    """

    markdown: str
    title: str
    links: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class BaseParser(ABC):
    """Abstract base class for content parsers.

    Parsers are responsible for converting raw content from various formats
    (HTML, PDF, Markdown, etc.) into a standardized markdown format. They also
    extract links for crawling and any relevant metadata.

    Example:
        >>> class HtmlParser(BaseParser):
        ...     def parse(self, content: str, source_url: str) -> ParseResult:
        ...         soup = BeautifulSoup(content, 'html.parser')
        ...         title = soup.title.string if soup.title else ''
        ...         links = [a['href'] for a in soup.find_all('a', href=True)]
        ...         # Convert to markdown...
        ...         return ParseResult(
        ...             markdown=markdown_content,
        ...             title=title,
        ...             links=links,
        ...             metadata={}
        ...         )
    """

    @abstractmethod
    def parse(self, content: str, source_url: str) -> ParseResult:
        """Parse content and convert to markdown.

        Args:
            content: The raw content to parse.
            source_url: The URL the content was fetched from (used for resolving
                relative links and as context for parsing).

        Returns:
            ParseResult containing the markdown content, title, extracted links,
            and any metadata.

        Raises:
            ParseError: If the content cannot be parsed.
        """
        pass
