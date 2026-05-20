"""
One-shot ingestion pipeline.
Run ONCE after generate_dataset.py:
    python ingest_all.py [--reset]

--reset  drops the existing ChromaDB collection before re-ingesting
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, CHROMA_DIR
from rag.ingestor import ingest_all
from rag.embedder import Embedder
from rag.vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(description="Ingest all enterprise data into ChromaDB")
    parser.add_argument("--reset", action="store_true", help="Drop existing collection first")
    args = parser.parse_args()

    print("=" * 60)
    print("Enterprise RAG — Ingestion Pipeline")
    print("=" * 60)

    store = VectorStore(persist_dir=CHROMA_DIR)

    if args.reset:
        print("\nResetting ChromaDB collection …")
        store.reset()

    existing = store.count()
    if existing > 0 and not args.reset:
        print(f"\nCollection already contains {existing} chunks.")
        print("Use --reset to re-ingest from scratch.")
        return

    # ── Load & chunk ──────────────────────────────────────────────────────────
    print(f"\nLoading data from: {DATA_DIR}")
    chunks = ingest_all(DATA_DIR)

    # ── Embed ─────────────────────────────────────────────────────────────────
    print(f"\nEmbedding {len(chunks)} chunks …")
    embedder = Embedder()
    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed_documents(texts)

    # ── Store ─────────────────────────────────────────────────────────────────
    print("\nStoring in ChromaDB …")
    store.add_chunks(chunks, embeddings)

    print(f"\nIngestion complete. Total chunks indexed: {store.count()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
