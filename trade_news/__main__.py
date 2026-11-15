"""Explicit collection, public-text retrieval, analysis and human-label evaluation."""
import argparse
from pathlib import Path
from .articles import acquire, read_jsonl
from .collect import collect
from .corpus import build, write_json
from .validation import validate


def main():
    parser = argparse.ArgumentParser(description="Colombian goods export news: BE1340 measurement adaptation")
    parser.add_argument("command", choices=["collect", "fetch", "analyze", "validate", "all"])
    parser.add_argument("--start", default="2026-01-01")
    parser.add_argument("--end", default="2026-11-01", help="Exclusive month boundary; frozen Jan–Oct 2026 snapshot")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--verify-local-text", action="store_true")
    args = parser.parse_args()
    directory = Path(args.data_dir)
    if args.command in {"collect", "all"}:
        if (directory/"article_manifest.jsonl").exists():
            parser.error("Use a new data directory for a new collection; preserve existing articles and reviews.")
        print(f"Collected {len(collect(args.start, args.end, directory))} real candidate metadata records")
    if args.command in {"fetch", "all"}:
        print(f"Recorded {len(acquire(directory))} retrieval outcomes")
    if args.command in {"analyze", "all"}:
        rows, _ = build(directory, verify_local_text=args.verify_local_text)
        print(f"Prepared {len(rows)} retrieval records; {sum(r['eligible_for_index'] for r in rows)} eligible articles")
    if args.command in {"validate", "all"}:
        report = validate(read_jsonl(directory/"headlines.jsonl"), directory/"annotations.csv")
        write_json(directory/"validation_report.json", report)
        print(report["status"])


if __name__ == "__main__":
    main()
