# AI Collections Web Scraper

A production-minded web scraping pipeline designed to collect, clean, and enrich web content for AI workflows (RAG, fine-tuning, analytics).

## Overview

This scraper transforms unstructured web pages into clean, structured AI-ready documents with rich metadata and quality signals. It's built with production reliability in mind, featuring throttling, error handling, deduplication, and idempotency.

## Target Site

**Chosen Site:** [Books to Scrape](https://books.toscrape.com)

**Why this site:**

- Explicitly designed for scraping practice (ethically safe)
- Well-structured HTML with clear content hierarchy
- Diverse content types (product pages, category pages, pagination)
- Realistic e-commerce structure useful for testing content classification
- No rate limiting concerns, allowing demonstration of throttling features

## Features

### 🔍 Intelligent Crawling

- **Domain-restricted**: Only follows internal links
- **Deduplication**: URL normalization prevents duplicate fetches
- **Depth control**: Configurable crawl depth to avoid getting lost
- **Smart filtering**: Skips non-content pages (login, cart, search results)
- **Throttling**: Configurable delay between requests (default: 1s)

### 🧹 Content Extraction & Cleaning

- **Boilerplate removal**: Strips nav, footer, header, and sidebar content
- **Main content detection**: Heuristics to identify primary content (`<main>`, `<article>`, etc.)
- **Text cleaning**: Whitespace normalization, HTML tag removal
- **Title extraction**: Multi-strategy fallback (title tag → h1 → og:title)

### 🤖 AI-Ready Enrichment

Each document includes metadata optimized for AI workflows:

| Field                         | Description              | AI Use Case                            |
| ----------------------------- | ------------------------ | -------------------------------------- |
| `url`                         | Canonical URL            | Citation, deduplication                |
| `title`                       | Page title               | Semantic search, context               |
| `body_text`                   | Cleaned main content     | RAG input, fine-tuning corpus          |
| `word_count`                  | Word count               | Dataset filtering (min/max length)     |
| `char_count`                  | Character count          | Token estimation                       |
| `language`                    | ISO 639-1 code           | Language-specific models               |
| `content_type`                | Heuristic classification | Content filtering for training         |
| `fetched_at`                  | ISO 8601 timestamp       | Freshness tracking                     |
| `estimated_read_time_minutes` | Reading time             | User experience metrics                |
| `has_code_blocks`             | Boolean                  | Filter technical vs. narrative content |
| `link_density`                | Link text ratio          | Identify index/navigation pages        |
| `paragraph_count`             | Number of paragraphs     | Document structure signal              |
| `http_status`                 | HTTP status code         | Quality/reliability check              |
| `crawl_depth`                 | Distance from seed URL   | Relevance proxy                        |

### 🛡️ Production Robustness

- **Error handling**: Graceful handling of timeouts, 4xx/5xx errors
- **Partial save**: Interrupted crawls save progress automatically
- **Idempotent**: URL deduplication prevents duplicate processing
- **Logging**: Comprehensive logging with summary statistics
- **Resilient parsing**: Continues on individual page failures

## Installation

### Prerequisites

- Python 3.8 or higher
- pip

### Setup

```bash
# Clone or download the repository
cd ai-collections-scraper

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python cli.py --start-url https://books.toscrape.com --max-pages 50 --output books.jsonl
```

### Full Command-Line Options

```bash
python cli.py \
  --start-url <URL>              # Required: Starting URL
  --output <FILE>                # Required: Output file path
  --max-pages <INT>              # Optional: Max pages to scrape (default: 100)
  --max-depth <INT>              # Optional: Max crawl depth (default: 3)
  --delay <FLOAT>                # Optional: Delay between requests in seconds (default: 1.0)
  --timeout <INT>                # Optional: HTTP timeout in seconds (default: 10)
  --format <jsonl|json>          # Optional: Output format (default: jsonl)
  --user-agent <STRING>          # Optional: Custom User-Agent
  --verbose                      # Optional: Enable debug logging
```

### Examples

**Scrape books.toscrape.com (default example):**

```bash
python cli.py --start-url https://books.toscrape.com --max-pages 100 --output books.jsonl
```

**Scrape quotes.toscrape.com with custom settings:**

```bash
python cli.py \
  --start-url https://quotes.toscrape.com \
  --max-pages 50 \
  --max-depth 2 \
  --delay 2.0 \
  --output quotes.jsonl \
  --verbose
```

**Output as JSON array instead of JSONL:**

```bash
python cli.py --start-url https://books.toscrape.com --max-pages 20 --output books.json --format json
```

## Output Format

### JSONL (Newline-Delimited JSON)

Default format. Each line is a complete JSON object:

```jsonl
{"url": "https://example.com/page1", "title": "Example", ...}
{"url": "https://example.com/page2", "title": "Another", ...}
```

**Benefits:**

- Streamable (process line-by-line)
- Easy to append to
- Standard for large-scale data pipelines

### JSON Array

Single JSON array containing all documents:

```json
[
  {"url": "https://example.com/page1", "title": "Example", ...},
  {"url": "https://example.com/page2", "title": "Another", ...}
]
```

## Data Schema

See [`schema.json`](schema.json) for the formal JSON Schema definition.

### Example Document

```json
{
  "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "title": "A Light in the Attic",
  "body_text": "A Light in the Attic\n£51.77\nIn stock (22 available)\n\nIt's hard to imagine a world without A Light in the Attic...",
  "fetched_at": "2024-11-28T10:30:45.123456+00:00",
  "content_type": "product_page",
  "word_count": 89,
  "char_count": 567,
  "language": "en",
  "estimated_read_time_minutes": 0.45,
  "has_code_blocks": false,
  "link_density": 0.234,
  "paragraph_count": 3,
  "http_status": 200,
  "crawl_depth": 2
}
```

## Design Decisions

### 1. Content Type Classification

Heuristic-based classification using URL patterns and content signals:

- **doc_page**: `/docs/` in URL → technical documentation
- **article**: `/blog/`, `/article/` in URL → blog posts
- **product_page**: `/product/`, `/catalogue/` in URL → e-commerce
- **list_page**: High link density (>30%) → index/navigation
- **tutorial**: Long-form content with "guide"/"tutorial" in title

**AI Rationale:** Enables filtering during training (e.g., "only use articles and tutorials") and improves retrieval (e.g., "find product pages about X").

### 2. Boilerplate Removal Strategy

Multi-layered approach:

1. **Tag-based removal**: Strip `<nav>`, `<footer>`, `<header>`, `<aside>`
2. **Class/ID patterns**: Remove elements with common boilerplate patterns (`nav`, `sidebar`, `menu`)
3. **Main content detection**: Prefer `<main>` or `<article>` containers

**AI Rationale:** Reduces noise in embeddings and training data. Navigation text pollutes semantic similarity and wastes tokens.

### 3. URL Normalization & Deduplication

Normalize URLs by:

- Removing fragments (`#section`)
- Removing trailing slashes (conditionally)
- Preserving query parameters (they may indicate different content)

**Production Rationale:** Prevents re-fetching the same page. Critical for idempotency and cost control.

### 4. Quality Signals

Fields like `link_density`, `paragraph_count`, `word_count` enable:

- **Pre-filtering**: Skip low-quality pages before embedding
- **Dataset balancing**: Ensure diverse document lengths
- **Ranking**: Prefer substantial content over thin pages

### 5. Language Detection

Uses `langdetect` library for automatic language identification.

**AI Rationale:**

- Filter to specific languages for fine-tuning
- Route to language-specific models
- Ensure multilingual embeddings are properly labeled

## Architecture

```
cli.py                  # Command-line interface
  └─> WebCrawler        # Manages crawl state, queue, visited URLs
        ├─> fetch_page()              # HTTP requests + error handling
        ├─> extract_links()           # Link discovery
        └─> ContentExtractor          # HTML → structured data
              └─> ContentEnricher     # Structured data → AIDocument
```

**Separation of Concerns:**

- `WebCrawler`: Crawling logic, state management
- `ContentExtractor`: HTML parsing, text cleaning
- `ContentEnricher`: Metadata calculation, classification
- `AIDocument`: Data model (dataclass)

## Testing

Run the test suite:

```bash
python -m pytest tests/test_scraper.py -v
```

Tests cover:

- URL normalization and validation
- Content extraction and cleaning
- Metadata enrichment
- Error handling

## Analytics

Analyze your scraped collection:

```bash
python analytics.py --input books.jsonl
```

Outputs:

- Document count by content type
- Language distribution
- Word count statistics (min, max, mean, median)
- Average reading time
- Top domains (if multi-domain)

## Docker Support

Build and run in a container:

```bash
# Build image
docker build -t ai-scraper .

# Run scraper
docker run -v $(pwd)/data:/output ai-scraper \
  --start-url https://books.toscrape.com \
  --max-pages 50 \
  --output /output/books.jsonl
```

Output will be saved to `./data/books.jsonl` on your host machine.

## Future Work

### Short-term Improvements

1. **Configurable URL filters**: Allow regex patterns to include/exclude URLs (e.g., `--url-pattern=/docs/.*`)
2. **Resume capability**: Save crawl state to disk, resume from checkpoint
3. **Parallel fetching**: Use `asyncio` + `aiohttp` for concurrent requests
4. **Better content detection**: Train a small classifier to distinguish content from boilerplate
5. **Sitemap support**: Parse `sitemap.xml` for efficient large-site crawling

### Production-Scale Features

1. **Distributed crawling**:

   - Use message queue (RabbitMQ, Kafka) for URL frontier
   - Multiple worker processes/machines
   - Centralized deduplication (Redis bloom filter)

2. **Monitoring & Observability**:

   - Prometheus metrics (pages/sec, error rate, queue depth)
   - Structured logging (JSON logs → Elasticsearch)
   - Alerting on failure spikes

3. **Incremental updates**:

   - Track `Last-Modified` headers and ETags
   - Only re-fetch changed pages
   - Versioning of documents

4. **Quality scoring**:

   - ML-based quality classifier trained on human labels
   - Content diversity metrics (entity extraction, topic modeling)
   - Automatic filtering of low-quality pages

5. **Multi-source orchestration**:

   - Unified pipeline for multiple websites
   - Cross-site deduplication (fuzzy matching on content)
   - Priority queue (crawl high-value sites more frequently)

6. **Storage optimization**:

   - Stream to cloud storage (S3) instead of local files
   - Compression (gzip JSONL)
   - Partitioning by date/domain for efficient querying

7. **Legal & Ethical**:
   - robots.txt compliance (already in `requests` via `robotparser`)
   - Rate limiting per domain (token bucket algorithm)
   - User consent tracking for GDPR compliance

## Project Structure

```
.
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── schema.json           # JSON Schema for output format
├── scraper.py            # Core scraping logic
├── cli.py                # Command-line interface
├── tests/
│   └── test_scraper.py   # Unit tests
├── analytics.py          # Collection analysis tool
└── Dockerfile            # Container definition
```

## License

This is a demonstration project for a technical assessment. Use responsibly and respect website terms of service.

## Notes

- Always check a website's `robots.txt` and terms of service before scraping
- This scraper includes reasonable throttling, but adjust `--delay` for sensitive sites
- Some websites may block scrapers; this is expected and the scraper will log errors gracefully
