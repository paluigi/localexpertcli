"""Main entry point for localexpertcli.

This module provides the main entry point for the CLI application.
"""

from localexpertcli.cli.commands import app


def main() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    main()
