# Krew Take-Home Study Notes

This document is a quick-learning guide tailored to the Crew Research scraping + AI enrichment take-home. After reading it, you should be able to describe the assignment clearly and outline a credible solution plan.

## Challenge at a Glance
- **Goal:** Build a small, production-minded scraper + processor that collects high-quality documents from a scrape-friendly public site and outputs AI-ready JSONL.
- **End Product:** Clean text with structured metadata and quality signals (length, language, content type, timestamps, etc.) suitable for RAG/search/fine-tuning.
- **Interface Expectation:** Runnable CLI/function (e.g., `scrape_site --start-url=<URL> --max-pages=100 --output=output.jsonl`) with sane limits and logging.

## What the Company Is Testing
1. **Product/Data judgment:** Can you choose a scrape-safe site, define what “good” content looks like, and keep only valuable sections?
2. **Systems thinking (small-scale):** Do you structure the pipeline (crawl → fetch → parse/clean → enrich → output) with error handling, throttling, and deduplication?
3. **Information extraction judgment:** Can you separate main content from boilerplate and capture titles/body text cleanly?
4. **AI readiness:** Do you design a consistent schema with metadata/signals that downstream AI tasks actually need?
5. **Practical engineering:** Is there a usable CLI, sensible defaults/limits, and basic observability (logs/stats)?
6. **Communication:** Do you document choices (site, heuristics, schema) concisely so others can run/consume the scraper?

## Knowledge Map (Mental Graph)
- **Inputs & Scope**
  - Start URL + on-domain crawl; respect robots.txt and politeness (delay, limits).
  - Filters: include/exclude patterns to avoid login/search/cart pages; cap depth/pages.
- **Fetcher**
  - HTTP client with timeouts, small retry policy, and custom User-Agent.
  - Skip non-HTML content types.
- **Crawler Frontier**
  - Queue of `(url, depth)`; visited set for idempotency; URL normalization (urljoin, strip fragments/queries when safe).
- **Parser & Cleaner**
  - Strip `script/style/nav/footer` where possible; target `main/article/[role=main]/.content` heuristics.
  - Fallback to largest text block; normalize whitespace; prefer `<title>` then `<h1>`.
- **Enrichment (AI Signals)**
  - Required: `url`, `title`, `body_text`, `word_count/char_count`, `language`, `content_type`, `fetched_at`.
  - Helpful extras: `reading_time_minutes`, `has_code_blocks`, `section_headings`, `out_links`, `text_hash` for dedup/versioning.
- **Schema & Output**
  - Define JSON schema (fields + types) in README or JSON Schema file.
  - Emit newline-delimited JSON; validate and skip malformed/too-short docs.
- **Quality/Resilience**
  - Idempotent: avoid duplicates via normalized URLs + content hash.
  - Robust: handle 4xx/5xx/timeouts gracefully; log skips/failures without crashing.
- **Ergonomics & Validation**
  - CLI flags: `start-url`, `max-pages`, `max-depth`, `delay`, `output`, `allow-pattern`, `exclude-pattern`.
  - Optional quick stats (doc count, avg length, language distribution) to sanity-check output.
- **Documentation**
  - Chosen site and why (scrape-friendly, predictable HTML).
  - Main-content heuristic and filters.
  - Schema definition and how metadata supports AI workflows.
  - Future work: scheduling, monitoring, richer parsing, cross-source dedup.

## How to Explain the Challenge Confidently
- **“What’s being built?”** A polite, on-domain crawler that fetches HTML pages, extracts main text and title, enriches with metadata/signals, and writes JSONL.
- **“What matters most?”** Data quality (clean main text), schema consistency, AI-usable signals, resilience (errors/throttling), and documentation of choices.
- **“How to prove readiness?”** Show a clear schema, a CLI that respects limits/robots, heuristics for main content, dedup/idempotency, and logs/stats that demonstrate control over the crawl.

## Typical Solution Outline (Storyboard)
1. **Choose site** that allows scraping (e.g., docs or sandbox domain); verify robots.txt.
2. **Crawl loop** with queue, depth/page caps, include/exclude patterns, small delay.
3. **Fetch** with timeouts/retries; ensure HTML content-type.
4. **Parse & clean** using BeautifulSoup/selectolax: remove boilerplate, extract title/body, normalize whitespace.
5. **Enrich** with counts, language heuristic, content type inference, fetched timestamp, hashes, optional signals (reading time, code ratio).
6. **Validate & write** JSONL according to your schema; log successes/failures; skip short/invalid docs.
7. **Document** site choice, heuristics, schema, and future improvements.

## Checklist Before You Deliver
- [ ] CLI runs end-to-end with configurable limits.
- [ ] On-domain, robots-respecting crawl with delays and duplicate prevention.
- [ ] Main-content extraction heuristic implemented; boilerplate stripped.
- [ ] JSON schema documented; JSONL output validated; idempotent across runs.
- [ ] Basic logging and (optional) summary stats.
- [ ] README covers site choice, how to run, schema, design decisions, future work.

