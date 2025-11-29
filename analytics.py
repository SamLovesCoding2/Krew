#!/usr/bin/env python3
"""
Quick analytics script for scraped data.
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
    """Load docs from file"""
    documents = []

    with open(input_path, "r", encoding="utf-8") as f:
        first_line = f.readline()
        f.seek(0)

        try:
            json.loads(first_line)
            for line in f:
                line = line.strip()
                if line:
                    documents.append(json.loads(line))
        except json.JSONDecodeError:
            f.seek(0)
            data = json.load(f)
            if isinstance(data, list):
                documents = data
            else:
                documents = [data]

    return documents


def print_section(title: str):
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def analyze_collection(documents: List[Dict]):
    """Print stats about the collection"""
    if not documents:
        print("No docs found", file=sys.stderr)
        return

    print_section("OVERVIEW")
    print(f"Total docs: {len(documents):,}")

    # Get metrics
    word_counts = [doc.get("word_count", 0) for doc in documents]
    languages = [doc.get("language", "unknown") for doc in documents]
    content_types = [doc.get("content_type", "unknown") for doc in documents]
    link_densities = [doc.get("link_density", 0) for doc in documents]
    has_code = [doc.get("has_code_blocks", False) for doc in documents]

    print_section("CONTENT STATS")
    print(f"Total words: {sum(word_counts):,}")
    print(f"Word count range: {min(word_counts):,} - {max(word_counts):,}")
    print(f"Average: {statistics.mean(word_counts):,.0f}")
    print(f"Median: {statistics.median(word_counts):,.0f}")

    print_section("LANGUAGES")
    lang_counter = Counter(languages)
    for lang, count in lang_counter.most_common():
        pct = (count / len(documents)) * 100
        print(f"  {lang}: {count} ({pct:.0f}%)")

    print_section("CONTENT TYPES")
    type_counter = Counter(content_types)
    for ct, count in type_counter.most_common():
        pct = (count / len(documents)) * 100
        print(f"  {ct}: {count} ({pct:.0f}%)")

    print_section("QUALITY CHECK")

    high_link = sum(1 for d in link_densities if d > 0.3)
    print(
        f"High link density (>0.3): {high_link} ({high_link / len(documents) * 100:.0f}%)"
    )
    print("  → These are probably navigation/index pages")

    thin = sum(1 for w in word_counts if w < 100)
    print(f"Thin content (<100 words): {thin} ({thin / len(documents) * 100:.0f}%)")

    code_count = sum(has_code)
    print(f"Has code blocks: {code_count} ({code_count / len(documents) * 100:.0f}%)")

    print("\nFor AI training, consider filtering:")
    print(f"  - Remove {thin} thin docs (<100 words)")
    print(f"  - Remove {high_link} navigation pages (link_density > 0.3)")
    print(f"  - Keep only {lang_counter.most_common(1)[0][0]} language")

    clean_count = len(
        [
            d
            for d in documents
            if d.get("word_count", 0) >= 100 and d.get("link_density", 1) <= 0.3
        ]
    )
    print(f"\nAfter filtering: {clean_count} / {len(documents)} docs")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze scraped AI collections and provide insights"
    )

    parser.add_argument(
        "--input", required=True, help="Input JSONL or JSON file to analyze"
    )

    parser.add_argument(
        "--export-filtered",
        help="Export filtered documents (applying quality filters) to a new file",
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
        most_common_lang = Counter(
            d.get("language", "unknown") for d in documents
        ).most_common(1)[0][0]
        filtered = [
            d
            for d in documents
            if d.get("word_count", 0) >= 100
            and d.get("link_density", 1) <= 0.3
            and d.get("language", "") == most_common_lang
        ]

        with open(args.export_filtered, "w", encoding="utf-8") as f:
            for doc in filtered:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")

        print(f"✓ Exported {len(filtered)} filtered documents")


if __name__ == "__main__":
    main()
