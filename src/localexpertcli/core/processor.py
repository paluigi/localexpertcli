"""Base processor abstract class and processor pipeline.

This module provides the abstract base class for all content processors in the
localexpertcli project, as well as a ProcessorPipeline for chaining multiple
processors together. Processors are responsible for transforming, filtering,
or enhancing parsed markdown content.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProcessorContext:
    """Context object passed through the processor pipeline.

    This dataclass carries all the information that processors might need
    to perform their transformations. Processors can modify any of these
    fields as the content flows through the pipeline.

    Attributes:
        markdown: The markdown content to process.
        source_url: The original URL where the content was fetched from.
        title: The title of the document.
        metadata: Additional metadata about the content.
    """

    markdown: str
    source_url: str
    title: str
    metadata: dict = field(default_factory=dict)


class BaseProcessor(ABC):
    """Abstract base class for content processors.

    Processors are responsible for transforming, filtering, or enhancing
    markdown content. They can be chained together using the ProcessorPipeline
    to create complex processing workflows.

    Each processor receives a ProcessorContext and returns a (potentially
    modified) ProcessorContext. This allows processors to:
    - Modify the markdown content (e.g., clean up, reformat)
    - Update metadata (e.g., add processing timestamps)
    - Filter content (e.g., remove unwanted sections)
    - Enrich content (e.g., add summaries, extract entities)

    Example:
        >>> class CodeBlockProcessor(BaseProcessor):
        ...     @property
        ...     def name(self) -> str:
        ...         return "code_block_cleaner"
        ...
        ...     def process(self, context: ProcessorContext) -> ProcessorContext:
        ...         # Remove empty code blocks
        ...         import re
        ...         context.markdown = re.sub(
        ...             r'```\\n```\\n', '', context.markdown
        ...         )
        ...         return context
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Processor name for logging and identification.

        Returns:
            A unique string identifier for this processor.
        """
        pass

    @abstractmethod
    def process(self, context: ProcessorContext) -> ProcessorContext:
        """Process and optionally modify the context.

        Args:
            context: The processor context containing markdown and metadata.

        Returns:
            The (potentially modified) processor context.

        Raises:
            ProcessingError: If the processing fails critically.
        """
        pass


class ProcessorPipeline:
    """Pipeline for chaining multiple processors together.

    The ProcessorPipeline executes a sequence of processors in order,
    passing the output of each processor as input to the next. This allows
    for building complex processing workflows from simple, reusable components.

    Example:
        >>> pipeline = ProcessorPipeline([
        ...     CodeBlockProcessor(),
        ...     LinkProcessor(),
        ...     MetadataEnricher(),
        ... ])
        >>> result = pipeline.process(context)

    Attributes:
        processors: List of processors to execute in sequence.
    """

    def __init__(self, processors: list[BaseProcessor]):
        """Initialize the pipeline with a list of processors.

        Args:
            processors: List of BaseProcessor instances to execute in order.
        """
        self.processors = processors

    def process(self, context: ProcessorContext) -> ProcessorContext:
        """Execute all processors in sequence.

        Args:
            context: The initial processor context.

        Returns:
            The final processor context after all processors have been applied.
        """
        for processor in self.processors:
            context = processor.process(context)
        return context

    def add_processor(self, processor: BaseProcessor) -> "ProcessorPipeline":
        """Add a processor to the end of the pipeline.

        Args:
            processor: The processor to add.

        Returns:
            Self for method chaining.
        """
        self.processors.append(processor)
        return self
