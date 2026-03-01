# LocalExpertCLI

A modular CLI tool for crawling documentation websites and converting them to Markdown.

## Features

- **Plugin-based Architecture** - Extensible system with three main extension points:
  - **Fetchers**: Retrieve content from various sources (HTTP, browser emulation, local files)
  - **Parsers**: Convert raw content to Markdown (HTML, PDF, Word documents)
  - **Processors**: Post-process Markdown output through a pipeline (LLM enhancements, noise removal)
- **Subdomain-scoped Crawling** - Automatically discovers and crawls pages within the same subdomain
- **Polite Crawling** - Random delays between requests to be respectful to target servers
- **Tenacity-based Retry Logic** - Robust retry mechanism with exponential backoff for failed requests
- **Dry-run Mode** - Map URLs only without downloading content, perfect for planning crawls
- **HTML to Markdown Conversion** - Clean conversion of HTML pages to well-formatted Markdown

## Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Install with uv

```bash
# Clone the repository
git clone <repository-url>
cd localexpertcli

# Install dependencies
uv sync
```

## Usage

### Basic Usage

```bash
uv run localexpertcli crawl <URL> <OUTPUT_DIR>
```

### CLI Arguments Reference

| Argument | Description | Default |
|----------|-------------|---------|
| `URL` | Target URL to crawl | (required) |
| `OUTPUT_DIR` | Output directory for Markdown files | (required) |
| `--retries`, `-r` | Maximum retry attempts | `5` |
| `--dry-run`, `-n` | Map URLs only without downloading | `False` |
| `--min-delay` | Minimum delay between requests (seconds) | `1.0` |
| `--max-delay` | Maximum delay between requests (seconds) | `3.0` |
| `--verbose`, `-v` | Enable verbose output | `False` |

## Examples

### Dry-run to Discover Pages

Map all discoverable URLs without downloading any content:

```bash
uv run localexpertcli crawl https://docs.example.com ./output --dry-run
```

### Full Crawl with Default Settings

Crawl a documentation site and save Markdown files to the output directory:

```bash
uv run localexpertcli crawl https://docs.python.org ./python-docs
```

### Custom Retry and Delay Settings

Configure more aggressive retries and shorter delays for faster crawling:

```bash
uv run localexpertcli crawl https://docs.example.com ./output --retries 10 --min-delay 0.5 --max-delay 1.5
```

### Verbose Mode

Enable detailed output for debugging or monitoring:

```bash
uv run localexpertcli crawl https://docs.example.com ./output --verbose
```

## Architecture

LocalExpertCLI follows a **plugin-based architecture** designed for extensibility and maintainability:

- **Separation of Concerns**: Each component has a single responsibility
- **Open/Closed Principle**: Easy to extend without modifying core logic
- **Dependency Injection**: Components are injected into the crawler service
- **Strategy Pattern**: Swappable implementations for fetchers and parsers
- **Chain of Responsibility**: Processor pipeline for post-processing

For detailed architecture documentation, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

### Extending the Tool

The plugin system allows you to add new capabilities:

1. **Custom Fetchers**: Implement [`BaseFetcher`](src/localexpertcli/core/fetcher.py) to support new content sources (e.g., Playwright for JavaScript-heavy sites)
2. **Custom Parsers**: Implement [`BaseParser`](src/localexpertcli/core/parser.py) to handle new content types (e.g., PDF, DOCX)
3. **Custom Processors**: Implement [`BaseProcessor`](src/localexpertcli/core/processor.py) to add post-processing steps (e.g., LLM-based summarization)

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.
