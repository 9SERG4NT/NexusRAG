"""
CLI query interface.

Usage:
    python query.py --user alice --query "What are the top incidents this week?"
    python query.py --user bob   --query "What is the maternity leave policy?"
    python query.py --demo                  # runs all 6 showcase queries
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rag.pipeline import EnterprisePipeline


DEMO_QUERIES = [
    ("alice", "What are the top incidents this week?"),
    ("bob",   "What is the maternity leave policy?"),
    ("bob",   "What is the Q4 revenue?"),          # should be blocked
    ("carol", "Show me employee salaries in Engineering"),
    ("dave",  "Any critical errors in the last 24 hours?"),
    ("eve",   "What is the remote work policy?"),
]


def print_result(result: dict, verbose: bool = False):
    sep = "=" * 65
    print(f"\n{sep}")
    user = result.get("user", "?")
    role = result.get("role", "?")
    conf = result.get("confidence", 0)
    conf_label = result.get("confidence_label", "")
    print(f"  USER: {user:<12} ROLE: {role:<14} CONFIDENCE: {conf:.0%} ({conf_label})")

    if result.get("access_denied"):
        print(f"\n  BLOCKED: {result.get('answer')}")
        print(sep)
        return

    print(f"\n  ANSWER:\n")
    for line in result["answer"].split("\n"):
        print(f"    {line}")

    citations = result.get("citations") or result.get("all_retrieved_sources", [])
    if citations:
        print(f"\n  CITATIONS:")
        for c in citations:
            score_str = f"  score={c.get('score', 0):.3f}" if verbose else ""
            print(f"    [{c['id']}] {c['source']} ({c['type'].upper()}, dept={c['department']}){score_str}")

    if verbose and result.get("retrieval_info"):
        info = result["retrieval_info"]
        print(f"\n  RETRIEVAL TRACE:")
        print(f"    allowed_departments : {info.get('allowed_departments')}")
        print(f"    preferred_dept      : {info.get('preferred_department')}")
        print(f"    candidates_found    : {info.get('candidates_after_threshold')}")
        print(f"    chunks_used         : {info.get('final_chunks')}")
        print(f"    top_hybrid_scores   : {info.get('top_scores')}")

    print(sep)


def main():
    parser = argparse.ArgumentParser(description="Enterprise RAG CLI")
    parser.add_argument("--user", default=None, help="Username (alice/bob/carol/dave/eve)")
    parser.add_argument("--query", default=None, help="Natural language question")
    parser.add_argument("--demo", action="store_true", help="Run all 6 demo queries")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show retrieval trace")
    args = parser.parse_args()

    if not args.demo and (not args.user or not args.query):
        parser.print_help()
        sys.exit(1)

    print("\nInitialising Enterprise RAG pipeline …")
    pipeline = EnterprisePipeline()

    queries = DEMO_QUERIES if args.demo else [(args.user, args.query)]

    for user, query in queries:
        print(f"\nQuerying as '{user}': {query}")
        result = pipeline.query(user=user, query=query)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_result(result, verbose=args.verbose)


if __name__ == "__main__":
    main()
