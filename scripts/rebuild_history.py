"""Discover or retrieve a NEW historical corpus without changing the active data."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trade_news.history import discover, fetch

parser = argparse.ArgumentParser()
parser.add_argument("command", choices=["discover", "fetch"])
parser.add_argument("--data-dir", required=True)
parser.add_argument("--start", default="2020-03-01")
parser.add_argument("--end", default="2026-11-01")
parser.add_argument("--sources", nargs="+")
args = parser.parse_args()
if Path(args.data_dir).resolve() == (Path(__file__).resolve().parents[1]/"data").resolve():
    parser.error("Use a new staging directory; preserve the active snapshot and human work")
operation = discover if args.command == "discover" else fetch
operation(args.data_dir, args.start, args.end, args.sources)
