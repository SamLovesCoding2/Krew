#!/usr/bin/env python3
"""
Quick examples showing how to use the scraped data for different AI tasks.
I wrote these to demonstrate why the metadata fields are actually useful.
"""

import json
from typing import List, Dict


def load_collection(jsonl_path: str) -> List[Dict]:
    """Load docs from JSONL file"""
    docs = []
    with open(jsonl_path, "r") as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))
    return docs


def prepare_for_rag(
    docs: List[Dict], min_words: int = 100, max_words: int = 2000
) -> List[Dict]:
    """Filter docs for RAG - need decent content, not navigation pages"""
    rag_ready = []

    for doc in docs:
        # Too short or too long
        if doc["word_count"] < min_words or doc["word_count"] > max_words:
            continue

        # High link density = navigation page, skip it
        if doc["link_density"] > 0.4:
            continue

        if doc["language"] == "unknown":
            continue

        rag_ready.append(
            {
                "text": doc["body_text"],
                "metadata": {
                    "source": doc["url"],
                    "title": doc["title"],
                    "type": doc["content_type"],
                    "language": doc["language"],
                    "fetched_at": doc["fetched_at"],
                },
            }
        )

    return rag_ready


def validate_training_data(docs: List[Dict]) -> Dict:
    """Check dataset quality - catches common issues before training"""
    report = {"total_docs": len(docs), "quality_issues": [], "recommendations": []}

    content_types = {}
    for doc in docs:
        ct = doc["content_type"]
        content_types[ct] = content_types.get(ct, 0) + 1

    if len(content_types) == 1:
        report["quality_issues"].append("All same content type")
        report["recommendations"].append("Mix different page types for better results")

    thin_docs = sum(1 for d in docs if d["word_count"] < 50)
    if thin_docs / len(docs) > 0.2:
        report["quality_issues"].append(
            f"{thin_docs} docs are really short (<50 words)"
        )
        report["recommendations"].append("Filter these out, they dont add much")

    nav_heavy = sum(1 for d in docs if d["link_density"] > 0.5)
    if nav_heavy / len(docs) > 0.3:
        report["quality_issues"].append(f"{nav_heavy} look like navigation/index pages")
        report["recommendations"].append("Remove high link-density pages")

    languages = set(d["language"] for d in docs)
    if len(languages) > 1:
        lang_dist = {
            lang: sum(1 for d in docs if d["language"] == lang) for lang in languages
        }
        report["quality_issues"].append(f"Mixed languages: {lang_dist}")
        report["recommendations"].append("Split by language for better training")

    return report


def chunk_for_embeddings(
    docs: List[Dict], chunk_size: int = 512, overlap: int = 50
) -> List[Dict]:
    """Split long docs into chunks - most embedding models cap at 512-1024 tokens"""
    chunks = []

    for doc in docs:
        text = doc["body_text"]
        words = text.split()

        if len(words) <= chunk_size:
            chunks.append(
                {
                    "text": text,
                    "source_url": doc["url"],
                    "chunk_id": 0,
                    "total_chunks": 1,
                }
            )
            continue

        num_chunks = 0
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i : i + chunk_size]
            chunks.append(
                {
                    "text": " ".join(chunk_words),
                    "source_url": doc["url"],
                    "chunk_id": num_chunks,
                    "total_chunks": -1,
                }
            )
            num_chunks += 1

        for chunk in chunks[-num_chunks:]:
            chunk["total_chunks"] = num_chunks

    return chunks


def filter_by_use_case(docs: List[Dict], use_case: str) -> List[Dict]:
    """Filter by use case - different tasks need different content"""
    filters = {
        "code_qa": {"has_code_blocks": True, "content_types": ["doc_page", "tutorial"]},
        "general_qa": {
            "min_words": 100,
            "content_types": ["article", "doc_page"],
            "max_link_density": 0.3,
        },
        "product_info": {"content_types": ["product_page"], "min_words": 50},
    }

    if use_case not in filters:
        return docs

    config = filters[use_case]
    filtered = []

    for doc in docs:
        if (
            "content_types" in config
            and doc["content_type"] not in config["content_types"]
        ):
            continue

        if (
            "has_code_blocks" in config
            and doc["has_code_blocks"] != config["has_code_blocks"]
        ):
            continue

        if "min_words" in config and doc["word_count"] < config["min_words"]:
            continue

        if (
            "max_link_density" in config
            and doc["link_density"] > config["max_link_density"]
        ):
            continue

        filtered.append(doc)

    return filtered


def export_for_vector_db(docs: List[Dict], output_path: str):
    """Export in format for vector DBs like Pinecone/Weaviate"""
    import hashlib

    vector_docs = []
    for doc in docs:
        doc_id = hashlib.md5(doc["url"].encode()).hexdigest()

        vector_docs.append(
            {
                "id": doc_id,
                "text": doc["body_text"],
                "metadata": {
                    "url": doc["url"],
                    "title": doc["title"],
                    "content_type": doc["content_type"],
                    "language": doc["language"],
                    "word_count": doc["word_count"],
                    "fetched_at": doc["fetched_at"],
                },
            }
        )

    with open(output_path, "w") as f:
        json.dump(vector_docs, f, indent=2)

    print(f"Exported {len(vector_docs)} docs to {output_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ai_examples.py <input.jsonl>")
        sys.exit(1)

    input_file = sys.argv[1]

    print("Loading docs...")
    docs = load_collection(input_file)
    print(f"Loaded {len(docs)} documents\n")

    print("=" * 60)
    print("1. RAG Preparation")
    print("=" * 60)
    rag_docs = prepare_for_rag(docs)
    print(f"RAG-ready: {len(rag_docs)} / {len(docs)}")
    print(f"Filtered out: {len(docs) - len(rag_docs)} (navigation/thin content)")

    print("\n" + "=" * 60)
    print("2. Quality Check")
    print("=" * 60)
    report = validate_training_data(docs)
    if report["quality_issues"]:
        print(f"Found {len(report['quality_issues'])} issues:")
        for issue in report["quality_issues"]:
            print(f"  - {issue}")
        if report["recommendations"]:
            print("\nFixes:")
            for rec in report["recommendations"]:
                print(f"  - {rec}")
    else:
        print("No major issues found")

    print("\n" + "=" * 60)
    print("3. Chunking (first 5 docs)")
    print("=" * 60)
    chunks = chunk_for_embeddings(docs[:5], chunk_size=200)
    print(f"Created {len(chunks)} chunks from 5 docs")

    print("\n" + "=" * 60)
    print("4. Filter by Use Case")
    print("=" * 60)
    for use_case in ["code_qa", "general_qa", "product_info"]:
        filtered = filter_by_use_case(docs, use_case)
        print(f"  {use_case}: {len(filtered)} docs")

    print("\n" + "=" * 60)
    print("5. Vector DB Export")
    print("=" * 60)
    output_file = input_file.replace(".jsonl", "_vector_db.json")
    export_for_vector_db(docs, output_file)

    print("\nDone. This shows how the metadata fields enable real filtering/routing.")
