"""Run optional local model inference or rebuild its saved aggregates offline."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trade_news.contextual import rebuild, run

parser = argparse.ArgumentParser()
parser.add_argument("--data-dir", default="data")
parser.add_argument("--model-dir")
parser.add_argument("--offline", action="store_true")
args = parser.parse_args()
if args.offline:
    rebuild(args.data_dir)
elif args.model_dir:
    run(args.data_dir, args.model_dir)
else:
    parser.error("Provide a local pinned model directory or use --offline for saved feature arithmetic")
