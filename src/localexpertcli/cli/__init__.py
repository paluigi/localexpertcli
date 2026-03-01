"""CLI module for localexpertcli.

This module provides command-line interface commands
built using Typer with Rich for beautiful output.

Commands:
    - crawl: Crawl a documentation website and convert to Markdown
"""

from localexpertcli.cli.commands import app

__all__ = ["app"]
