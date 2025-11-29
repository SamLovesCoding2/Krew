#!/usr/bin/env python3
"""
CLI for web scraper.
Usage: python cli.py --start-url <URL> --output <FILE> [options]
"""

import argparse
import sys
import logging
from pathlib import Path

from scraper import WebCrawler


def main():
    parser = argparse.ArgumentParser(
        description='Web scraper for AI collections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --start-url https://books.toscrape.com --max-pages 100 --output books.jsonl
  python cli.py --start-url https://quotes.toscrape.com --max-pages 50 --delay 2.0 --output quotes.jsonl
        """
    )
    
    # Required
    parser.add_argument(
        '--start-url',
        required=True,
        help='Starting URL for the crawl (must be a valid HTTP/HTTPS URL)'
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help='Output file path (e.g., output.jsonl or output.json)'
    )
    
    # Optional
    parser.add_argument('--max-pages', type=int, default=100, help='Max pages (default: 100)')
    parser.add_argument('--max-depth', type=int, default=3, help='Max depth (default: 3)')
    parser.add_argument('--delay', type=float, default=1.0, help='Request delay in sec (default: 1.0)')
    parser.add_argument('--timeout', type=int, default=10, help='HTTP timeout (default: 10)')
    parser.add_argument('--format', choices=['jsonl', 'json'], default='jsonl', help='Output format (default: jsonl)')
    parser.add_argument('--verbose', action='store_true', help='Debug logging')
    parser.add_argument('--user-agent', default='AI-Collections-Scraper/1.0', help='Custom User-Agent')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.start_url.startswith(('http://', 'https://')):
        print("Error: start-url must begin with http:// or https://", file=sys.stderr)
        sys.exit(1)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Initializing crawler for {args.start_url}")
    print(f"Configuration:")
    print(f"  Max pages: {args.max_pages}")
    print(f"  Max depth: {args.max_depth}")
    print(f"  Delay: {args.delay}s")
    print(f"  Output: {args.output} (format: {args.format})")
    print()
    
    crawler = WebCrawler(
        start_url=args.start_url,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        delay_seconds=args.delay,
        timeout=args.timeout,
        user_agent=args.user_agent
    )
    
    # Run crawler
    try:
        documents = crawler.crawl()
        
        if not documents:
            print("Warning: No documents were collected.", file=sys.stderr)
            sys.exit(1)
        
        # Save results
        if args.format == 'jsonl':
            crawler.save_to_jsonl(args.output)
        else:
            crawler.save_to_json(args.output)
        
        print()
        print(f"✓ Successfully scraped {len(documents)} pages")
        print(f"✓ Output saved to {args.output}")
        
        total_words = sum(doc.word_count for doc in documents)
        languages = set(doc.language for doc in documents)
        content_types = {}
        for doc in documents:
            content_types[doc.content_type] = content_types.get(doc.content_type, 0) + 1
        
        print()
        print("Collection Statistics:")
        print(f"  Total words: {total_words:,}")
        print(f"  Average words per page: {total_words // len(documents):,}")
        print(f"  Languages detected: {', '.join(languages)}")
        print(f"  Content types: {dict(content_types)}")
        
    except KeyboardInterrupt:
        print("\n\nCrawl interrupted by user.", file=sys.stderr)
        # Save partial results if any
        if crawler.documents:
            partial_output = args.output.replace('.json', '_partial.json')
            if args.format == 'jsonl':
                crawler.save_to_jsonl(partial_output)
            else:
                crawler.save_to_json(partial_output)
            print(f"Partial results saved to {partial_output}")
        sys.exit(130)
    
    except Exception as e:
        print(f"\nError during crawl: {e}", file=sys.stderr)
        import traceback
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

