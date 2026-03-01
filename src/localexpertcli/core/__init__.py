"""Core module containing abstract base classes for localexpertcli.

This module exports all core abstract base classes and data classes used
throughout the localexpertcli project for fetching, parsing, and processing
content.

Classes:
    FetchResult: Data class for fetch operation results.
    BaseFetcher: Abstract base class for URL fetchers.
    ParseResult: Data class for parse operation results.
    BaseParser: Abstract base class for content parsers.
    ProcessorContext: Data class for processor pipeline context.
    BaseProcessor: Abstract base class for content processors.
    ProcessorPipeline: Pipeline for chaining processors.
"""

from localexpertcli.core.fetcher import BaseFetcher, FetchResult
from localexpertcli.core.parser import BaseParser, ParseResult
from localexpertcli.core.processor import (
    BaseProcessor,
    ProcessorContext,
    ProcessorPipeline,
)

__all__ = [
    # Fetcher
    "FetchResult",
    "BaseFetcher",
    # Parser
    "ParseResult",
    "BaseParser",
    # Processor
    "ProcessorContext",
    "BaseProcessor",
    "ProcessorPipeline",
]
