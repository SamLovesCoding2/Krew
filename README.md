
```bash
# Install
pip install -r requirements.txt

# Run it
python cli.py --start-url https://books.toscrape.com --max-pages 50 --output data.jsonl

# Check what you got
head -n 1 data.jsonl | python -m json.tool
```

## outPut

```json
{
  "url": "https://...",
  "title": "Page Title",
  "body_text": "Clean text content...",
  "word_count": 234,
  "language": "en",
  "content_type": "article",
  "link_density": 0.15,
  "has_code_blocks": false,
  "fetched_at": "2024-11-28T10:30:00+00:00"
}
```

more details in `schema.json`


## How it works

1. **Crawling** - Starts from seed URL, follows internal links, avoids duplicates
2. **Extraction** - Finds main content (skips nav/footer), cleans HTML
3. **Enrichment** - Adds metadata: word count, language, content type, etc
4. **Output** - Saves as JSONL (one JSON object per line)

### Content detection

Tries to find `<main>` or `<article>` tags first, falls back to body. Removes obvious boilerplate (nav, footer, etc).

### Metadata fields

- **word_count/char_count** - Filter by length (skip thin pages)
- **language** - Route to correct model
- **content_type** - article/doc/product/list (heuristic based on URL + link density)
- **link_density** - High ratio = navigation page, skip for training
- **has_code_blocks** - Separate technical docs from regular text


## Command line options

```bash
python cli.py \
  --start-url <URL>        # where to start
  --max-pages <N>          # how many pages (default: 100)
  --max-depth <N>          # how deep to crawl (default: 3)
  --delay <seconds>        # wait between requests (default: 1.0)
  --output <file>          # output file (.jsonl or .json)
  --format jsonl|json      # output format
  --verbose                # debug mode
```

## Using the data

`ai_examples.py` for real usage examples:

```bash
python ai_examples.py data.jsonl
```

- Filter for RAG (removes navigation pages, thin content)
- Validate quality (catches common issues)
- Chunk for embeddings (handles token limits)
- Export to vector DBs


## Architecture Workflow

```
cli.py → WebCrawler → ContentExtractor → ContentEnricher → JSON output
```


## Tests

```bash
python -m pytest tests/test_scraper.py -v
```

**Analytics tool:**

```bash
python analytics.py --input data.jsonl
```

**Docker:**

```bash
docker build -t scraper .
docker run -v $(pwd)/data:/output scraper --start-url <URL> --output /output/data.jsonl
```

## Production ideas

- **Distributed**: Message queue for URLs, multiple workers, Redis for dedup
- **Incremental**: Check Last-Modified headers, only refetch changed pages
- **Monitoring**: Track error rates, queue depth, pages/sec
- **Better content detection**: Train a small classifier instead of heuristics
- **Parallel**: asyncio for concurrent requests