"""Reproducible collection, analysis and reference-label evaluation commands."""
import argparse
from pathlib import Path
from .collect import collect
from .pipeline import build, read_jsonl, write_json
from .validation import validate

parser = argparse.ArgumentParser(description="Colombian trade news NLP research prototype")
parser.add_argument("command", choices=["collect", "analyze", "validate", "all"])
parser.add_argument("--start", default="2026-05-01")
parser.add_argument("--end", default="2026-11-01", help="Exclusive month boundary")
parser.add_argument("--data-dir", default="data")
args = parser.parse_args()
directory = Path(args.data_dir)
if args.command in {"collect", "all"}:
    rows = collect(args.start, args.end, directory)
    print(f"Collected {len(rows)} real search records")
if args.command in {"analyze", "all"}:
    rows, indices = build(directory)
    print(f"Prepared {len(rows)} unique records and {len(indices)} index groups")
if args.command in {"validate", "all"}:
    report = validate(read_jsonl(directory / "headlines.jsonl"), directory / "annotations.csv")
    write_json(directory / "validation_report.json", report)
    print(report["status"])
