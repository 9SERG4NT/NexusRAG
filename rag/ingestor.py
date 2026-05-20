"""
Loads and chunks all data sources into a uniform chunk schema:
  { "text": str, "metadata": { source, source_type, department, chunk_id } }
"""

import json
import csv
import re
import hashlib
from pathlib import Path
from typing import Iterator

try:
    from fpdf import FPDF  # only needed at generate time
except ImportError:
    pass


# ── Chunking utilities ────────────────────────────────────────────────────────

def split_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """Naive word-count sliding window chunker."""
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return [c for c in chunks if c.strip()]


def make_chunk_id(source: str, index: int) -> str:
    slug = re.sub(r"[^a-z0-9]", "_", source.lower())
    return f"{slug}_{index}"


# ── PDF loader ────────────────────────────────────────────────────────────────

def _extract_pdf_text(path: Path) -> str:
    """Extract text from a PDF using pypdf if available, else raw read."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        pass
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    except ImportError:
        pass
    # Last resort: read raw bytes and decode printable chars
    raw = path.read_bytes()
    return raw.decode("latin-1", errors="ignore")


def load_pdf(path: Path, department: str) -> list[dict]:
    text = _extract_pdf_text(path)
    chunks = []
    for i, chunk_text in enumerate(split_text(text, chunk_size=300, overlap=50)):
        chunks.append({
            "text": chunk_text,
            "metadata": {
                "source": path.name,
                "source_type": "pdf",
                "department": department,
                "chunk_id": make_chunk_id(path.name, i),
            },
        })
    return chunks


# ── CSV loader ────────────────────────────────────────────────────────────────

def load_csv(path: Path, department: str, rows_per_chunk: int = 5) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    chunks = []
    for batch_start in range(0, len(rows), rows_per_chunk):
        batch = rows[batch_start : batch_start + rows_per_chunk]
        lines = [", ".join(f"{k}: {v}" for k, v in row.items()) for row in batch]
        text = f"[{path.name}]\n" + "\n".join(lines)
        idx = batch_start // rows_per_chunk
        chunks.append({
            "text": text,
            "metadata": {
                "source": path.name,
                "source_type": "csv",
                "department": department,
                "chunk_id": make_chunk_id(path.name, idx),
                "row_start": batch_start,
                "row_end": batch_start + len(batch) - 1,
            },
        })
    return chunks


# ── JSON logs loader ──────────────────────────────────────────────────────────

def load_json_logs(path: Path, department: str, entries_per_chunk: int = 5) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)

    chunks = []
    for batch_start in range(0, len(entries), entries_per_chunk):
        batch = entries[batch_start : batch_start + entries_per_chunk]
        lines = []
        levels_in_batch: set[str] = set()
        for e in batch:
            ts  = e.get("timestamp", "")
            lvl = e.get("level", "INFO")
            svc = e.get("service", "")
            msg = e.get("message", "")
            levels_in_batch.add(lvl.upper())
            lines.append(f"[{ts}] [{lvl}] {svc}: {msg}")
        # Descriptive header improves semantic matching for log queries
        level_str = ", ".join(sorted(levels_in_batch))
        text = f"System log entries (levels: {level_str}):\n" + "\n".join(lines)
        idx = batch_start // entries_per_chunk
        chunks.append({
            "text": text,
            "metadata": {
                "source": path.name,
                "source_type": "json",
                "department": department,
                "chunk_id": make_chunk_id(path.name, idx),
                "log_levels": list({e.get("level") for e in batch}),
            },
        })
    return chunks


# ── Master ingestor ───────────────────────────────────────────────────────────

def ingest_all(data_dir: Path) -> list[dict]:
    """
    Loads every data source, tags each chunk, and returns the unified list.
    Chunk IDs are globally unique (file + index).
    """
    chunks: list[dict] = []

    # PDFs
    pdf_dept_map = {
        "hr_policy.pdf": "hr",
        "finance_report.pdf": "finance",
        "it_security.pdf": "it",
    }
    for fname, dept in pdf_dept_map.items():
        path = data_dir / "documents" / fname
        if path.exists():
            loaded = load_pdf(path, dept)
            chunks.extend(loaded)
            print(f"  Loaded {path.name}: {len(loaded)} chunks")

    # CSVs
    csv_dept_map = {
        "employees.csv": "employees",
        "incidents.csv": "incidents",
    }
    for fname, dept in csv_dept_map.items():
        path = data_dir / "structured" / fname
        if path.exists():
            loaded = load_csv(path, dept)
            chunks.extend(loaded)
            print(f"  Loaded {path.name}: {len(loaded)} chunks")

    # JSON logs
    logs_path = data_dir / "logs" / "system_logs.json"
    if logs_path.exists():
        loaded = load_json_logs(logs_path, "logs")
        chunks.extend(loaded)
        print(f"  Loaded {logs_path.name}: {len(loaded)} chunks")

    # De-duplicate by chunk_id (safety)
    seen, deduped = set(), []
    for c in chunks:
        cid = c["metadata"]["chunk_id"]
        if cid not in seen:
            seen.add(cid)
            deduped.append(c)

    print(f"\nTotal chunks after dedup: {len(deduped)}")
    return deduped
