"""Parsers module for localexpertcli.

This module contains concrete implementations of BaseParser
for different content types.

Available parsers:
    - HtmlToMarkdownParser: Parse HTML content and convert to Markdown
"""

from localexpertcli.parsers.html_parser import HtmlToMarkdownParser

__all__ = ["HtmlToMarkdownParser"]
