"""Create a locked blind sample or evaluate actual independent human labels."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trade_news.evaluation import prepare, evaluate

parser = argparse.ArgumentParser()
parser.add_argument("command", choices=["prepare", "evaluate"])
parser.add_argument("--data-dir", default="data")
parser.add_argument("--size", type=int, default=200)
parser.add_argument("--all-sources", action="store_true", help="Diagnostic extension beyond the primary press frame")
args = parser.parse_args()
report = prepare(args.data_dir, args.size, primary_only=not args.all_sources) if args.command == "prepare" else evaluate(args.data_dir)
if args.command == "evaluate":
    (Path(args.data_dir)/"independent_evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
print(json.dumps({k: v for k, v in report.items() if k not in {"record_ids", "strata", "excludes_diagnostic_ids"}}, ensure_ascii=False, indent=2))
