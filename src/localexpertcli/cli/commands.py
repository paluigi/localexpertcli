"""CLI commands for localexpertcli.

This module provides the command-line interface commands built using Typer
with Rich for beautiful output formatting.
"""

import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from localexpertcli.services.crawler import CrawlerService, CrawlerConfig, CrawlResult
from localexpertcli.services.rate_limiter import RateLimiterConfig
from localexpertcli.fetchers.http_fetcher import HttpFetcher
from localexpertcli.parsers.html_parser import HtmlToMarkdownParser

app = typer.Typer(
    name="localexpertcli",
    help="Crawl documentation websites and convert them to Markdown."
)
console = Console()


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Target URL to start crawling from"),
    output_dir: Path = typer.Argument(..., help="Output directory for Markdown files"),
    max_retries: int = typer.Option(5, "--retries", "-r", help="Maximum retry attempts for failed requests"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Map URLs only without downloading"),
    min_delay: float = typer.Option(1.0, "--min-delay", help="Minimum delay between requests (seconds)"),
    max_delay: float = typer.Option(3.0, "--max-delay", help="Maximum delay between requests (seconds)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """
    Crawl a documentation website and convert pages to Markdown.

    Examples:
        localexpertcli crawl https://docs.example.com ./output
        localexpertcli crawl https://docs.python.org ./python-docs --dry-run
    """
    # Validate URL
    if not _validate_url(url):
        console.print(f"[red]Error:[/red] Invalid URL: {url}")
        console.print("[yellow]URL must be a valid HTTP or HTTPS URL.[/yellow]")
        raise typer.Exit(code=1)

    # Validate delay configuration
    if max_delay < min_delay:
        console.print("[red]Error:[/red] max-delay must be greater than or equal to min-delay")
        raise typer.Exit(code=1)

    # Create output directory if it doesn't exist
    if not dry_run:
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            console.print(f"[red]Error:[/red] Failed to create output directory: {e}")
            raise typer.Exit(code=1)

    # Display configuration
    _print_config(url, output_dir, max_retries, dry_run, min_delay, max_delay, verbose)

    # Show dry-run banner if applicable
    if dry_run:
        console.print()
        console.print(Panel.fit(
            "[yellow]DRY RUN MODE[/yellow]\n[dim]Mapping URLs only, no files will be downloaded.[/dim]",
            border_style="yellow"
        ))

    try:
        # Create configuration
        rate_limiter_config = RateLimiterConfig(
            min_delay=min_delay,
            max_delay=max_delay,
        )
        
        config = CrawlerConfig(
            start_url=url,
            output_dir=output_dir,
            max_retries=max_retries,
            dry_run=dry_run,
            rate_limiter_config=rate_limiter_config,
        )

        # Create fetcher and parser
        fetcher = HttpFetcher(max_retries=max_retries)
        parser = HtmlToMarkdownParser()

        # Create crawler service
        crawler = CrawlerService(config, fetcher, parser)

        # Execute crawl with progress indication
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            disable=verbose,  # Disable progress bar in verbose mode
        ) as progress:
            task = progress.add_task(
                "[cyan]Crawling...[/cyan]",
                total=None if dry_run else 100
            )
            
            result = crawler.crawl()
            
            progress.update(task, completed=100)

        # Print summary
        _print_summary(result, dry_run)

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Crawl interrupted by user (Ctrl+C)[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print()
        console.print(f"[red]Error during crawl:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)
    finally:
        # Clean up fetcher resources
        if 'fetcher' in locals():
            fetcher.close()


def _print_config(
    url: str,
    output_dir: Path,
    max_retries: int,
    dry_run: bool,
    min_delay: float,
    max_delay: float,
    verbose: bool,
) -> None:
    """Print the crawl configuration."""
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]LocalExpertCLI[/bold cyan]\n[dim]Documentation Crawler[/dim]",
        border_style="cyan"
    ))
    console.print()
    
    config_table = Table(show_header=False, box=None, padding=(0, 2))
    config_table.add_column("Key", style="bold")
    config_table.add_column("Value")
    
    config_table.add_row("Target URL:", f"[link={url}]{url}[/link]")
    config_table.add_row("Output Directory:", str(output_dir))
    config_table.add_row("Max Retries:", str(max_retries))
    config_table.add_row("Request Delay:", f"{min_delay}s - {max_delay}s")
    config_table.add_row("Dry Run:", "[yellow]Yes[/yellow]" if dry_run else "[green]No[/green]")
    config_table.add_row("Verbose:", "[green]Yes[/green]" if verbose else "[dim]No[/dim]")
    
    console.print(config_table)
    console.print()


def _print_summary(result: CrawlResult, dry_run: bool) -> None:
    """Print a summary table of the crawl results."""
    console.print()
    
    # Create summary table
    summary_table = Table(title="Crawl Summary", show_header=True, header_style="bold cyan")
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Value", justify="right")
    
    if dry_run:
        summary_table.add_row("Pages Discovered", f"[green]{result.pages_discovered}[/green]")
        summary_table.add_row("Mode", "[yellow]Dry Run (no files downloaded)[/yellow]")
    else:
        summary_table.add_row("Pages Discovered", str(result.pages_discovered))
        summary_table.add_row("Pages Downloaded", f"[green]{result.pages_downloaded}[/green]")
        if result.pages_failed > 0:
            summary_table.add_row("Pages Failed", f"[red]{result.pages_failed}[/red]")
        else:
            summary_table.add_row("Pages Failed", "[green]0[/green]")
        summary_table.add_row("Output Files", str(len(result.output_files)))
    
    console.print(summary_table)
    
    # Show output file locations if not dry run
    if not dry_run and result.output_files:
        console.print()
        console.print("[dim]Output files saved to:[/dim]")
        for file_path in result.output_files[:5]:  # Show first 5 files
            console.print(f"  [dim]•[/dim] {file_path}")
        if len(result.output_files) > 5:
            console.print(f"  [dim]• ... and {len(result.output_files) - 5} more files[/dim]")
    
    console.print()
    
    # Print completion message
    if dry_run:
        console.print("[green]✓[/green] Dry run complete. Use without --dry-run to download files.")
    elif result.pages_failed > 0:
        console.print(f"[yellow]⚠[/yellow] Crawl completed with {result.pages_failed} failed pages.")
    else:
        console.print("[green]✓[/green] Crawl completed successfully!")


def _validate_url(url: str) -> bool:
    """Validate that URL is a valid HTTP/HTTPS URL.
    
    Args:
        url: The URL string to validate.
        
    Returns:
        True if the URL is valid, False otherwise.
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


if __name__ == "__main__":
    app()
