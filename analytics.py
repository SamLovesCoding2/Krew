#!/usr/bin/env python3
"""
Analytics for scraped collections - provides stats and quality insights.
Usage: python analytics.py --input output.jsonl
"""

import json
import argparse
import sys
from pathlib import Path
from collections import Counter
from typing import List, Dict
import statistics


def load_documents(input_path: str) -> List[Dict]:
    """Load from JSONL or JSON file"""
    documents = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        f.seek(0)
        
        try:
            json.loads(first_line)
            # JSONL format
            for line in f:
                line = line.strip()
                if line:
                    documents.append(json.loads(line))
        except json.JSONDecodeError:
            # JSON array format
            f.seek(0)
            data = json.load(f)
            if isinstance(data, list):
                documents = data
            else:
                documents = [data]
    
    return documents


def print_section(title: str):
    """Print a section header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def analyze_collection(documents: List[Dict]):
    """Analyze collection and print stats"""
    if not documents:
        print("Error: No documents to analyze.", file=sys.stderr)
        return
    
    print_section("COLLECTION OVERVIEW")
    print(f"Total documents: {len(documents):,}")
    
    # Extract metrics
    word_counts = [doc.get('word_count', 0) for doc in documents]
    char_counts = [doc.get('char_count', 0) for doc in documents]
    read_times = [doc.get('estimated_read_time_minutes', 0) for doc in documents]
    languages = [doc.get('language', 'unknown') for doc in documents]
    content_types = [doc.get('content_type', 'unknown') for doc in documents]
    crawl_depths = [doc.get('crawl_depth', 0) for doc in documents]
    link_densities = [doc.get('link_density', 0) for doc in documents]
    has_code = [doc.get('has_code_blocks', False) for doc in documents]
    
    # Word count statistics
    print_section("CONTENT LENGTH STATISTICS")
    print(f"Total words across all documents: {sum(word_counts):,}")
    print(f"Total characters: {sum(char_counts):,}")
    print()
    print(f"Word count:")
    print(f"  Minimum: {min(word_counts):,}")
    print(f"  Maximum: {max(word_counts):,}")
    print(f"  Mean: {statistics.mean(word_counts):,.1f}")
    print(f"  Median: {statistics.median(word_counts):,.0f}")
    if len(word_counts) > 1:
        print(f"  Std Dev: {statistics.stdev(word_counts):,.1f}")
    
    # Reading time
    print()
    print(f"Estimated reading time:")
    print(f"  Total: {sum(read_times):,.1f} minutes ({sum(read_times)/60:.1f} hours)")
    print(f"  Average per document: {statistics.mean(read_times):.2f} minutes")
    
    # Language distribution
    print_section("LANGUAGE DISTRIBUTION")
    lang_counter = Counter(languages)
    for lang, count in lang_counter.most_common():
        percentage = (count / len(documents)) * 100
        print(f"  {lang}: {count:,} documents ({percentage:.1f}%)")
    
    # Content type distribution
    print_section("CONTENT TYPE DISTRIBUTION")
    type_counter = Counter(content_types)
    for content_type, count in type_counter.most_common():
        percentage = (count / len(documents)) * 100
        print(f"  {content_type}: {count:,} documents ({percentage:.1f}%)")
    
    # Crawl depth distribution
    print_section("CRAWL DEPTH DISTRIBUTION")
    depth_counter = Counter(crawl_depths)
    for depth, count in sorted(depth_counter.items()):
        percentage = (count / len(documents)) * 100
        bar = '█' * int(percentage / 2)
        print(f"  Depth {depth}: {count:,} documents ({percentage:.1f}%) {bar}")
    
    # Link density analysis
    print_section("LINK DENSITY ANALYSIS")
    print(f"Average link density: {statistics.mean(link_densities):.3f}")
    print(f"Median link density: {statistics.median(link_densities):.3f}")
    
    high_link_density = sum(1 for d in link_densities if d > 0.3)
    print(f"Documents with high link density (>0.3): {high_link_density} ({high_link_density/len(documents)*100:.1f}%)")
    print("  → Likely index/navigation pages")
    
    # Code blocks
    print_section("TECHNICAL CONTENT ANALYSIS")
    code_count = sum(has_code)
    print(f"Documents with code blocks: {code_count} ({code_count/len(documents)*100:.1f}%)")
    
    # Quality signals
    print_section("QUALITY SIGNALS")
    
    # Substantial content (>500 words)
    substantial = sum(1 for w in word_counts if w > 500)
    print(f"Substantial documents (>500 words): {substantial} ({substantial/len(documents)*100:.1f}%)")
    
    # Short content (< 100 words) - potential thin content
    thin = sum(1 for w in word_counts if w < 100)
    print(f"Thin content (<100 words): {thin} ({thin/len(documents)*100:.1f}%)")
    
    # Good balance (100-500 words)
    medium = len(documents) - substantial - thin
    print(f"Medium length (100-500 words): {medium} ({medium/len(documents)*100:.1f}%)")
    
    # URL analysis
    print_section("URL ANALYSIS")
    domains = set()
    for doc in documents:
        url = doc.get('url', '')
        if url:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            domains.add(domain)
    
    print(f"Unique domains: {len(domains)}")
    for domain in sorted(domains):
        domain_docs = sum(1 for doc in documents if domain in doc.get('url', ''))
        print(f"  {domain}: {domain_docs} documents")
    
    # HTTP status codes
    print_section("HTTP STATUS CODES")
    status_codes = [doc.get('http_status', 0) for doc in documents]
    status_counter = Counter(status_codes)
    for status, count in sorted(status_counter.items()):
        percentage = (count / len(documents)) * 100
        print(f"  {status}: {count} documents ({percentage:.1f}%)")
    
    # Recommendations
    print_section("RECOMMENDATIONS FOR AI WORKFLOWS")
    
    print("\n📊 Dataset Quality:")
    if substantial / len(documents) > 0.5:
        print("  ✓ Good: Majority of documents have substantial content (>500 words)")
    else:
        print("  ⚠ Consider filtering: Many documents have thin content")
    
    if len(set(languages)) == 1:
        print("  ✓ Good: Consistent language across collection")
    else:
        print("  ⚠ Consider: Separate documents by language for better embeddings")
    
    if high_link_density / len(documents) < 0.2:
        print("  ✓ Good: Low proportion of navigation/index pages")
    else:
        print("  ⚠ Consider: Filter out high link-density pages (index/navigation)")
    
    print("\n🤖 Suggested Filters for RAG/Fine-tuning:")
    print(f"  - Min word count: 100 (removes {thin} documents)")
    print(f"  - Max link density: 0.3 (removes {high_link_density} documents)")
    print(f"  - Language: {lang_counter.most_common(1)[0][0]} (keeps {lang_counter.most_common(1)[0][1]} documents)")
    
    filtered_count = len([
        d for d in documents 
        if d.get('word_count', 0) >= 100 
        and d.get('link_density', 1) <= 0.3
        and d.get('language', '') == lang_counter.most_common(1)[0][0]
    ])
    print(f"\n  → After applying all filters: {filtered_count} documents ({filtered_count/len(documents)*100:.1f}%)")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Analyze scraped AI collections and provide insights'
    )
    
    parser.add_argument(
        '--input',
        required=True,
        help='Input JSONL or JSON file to analyze'
    )
    
    parser.add_argument(
        '--export-filtered',
        help='Export filtered documents (applying quality filters) to a new file'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Load documents
    print(f"Loading documents from {args.input}...")
    try:
        documents = load_documents(args.input)
    except Exception as e:
        print(f"Error loading documents: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Analyze
    analyze_collection(documents)
    
    # Export filtered if requested
    if args.export_filtered and documents:
        print(f"\nExporting filtered documents to {args.export_filtered}...")
        
        # Apply quality filters
        most_common_lang = Counter(d.get('language', 'unknown') for d in documents).most_common(1)[0][0]
        filtered = [
            d for d in documents
            if d.get('word_count', 0) >= 100
            and d.get('link_density', 1) <= 0.3
            and d.get('language', '') == most_common_lang
        ]
        
        with open(args.export_filtered, 'w', encoding='utf-8') as f:
            for doc in filtered:
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')
        
        print(f"✓ Exported {len(filtered)} filtered documents")


if __name__ == '__main__':
    main()

