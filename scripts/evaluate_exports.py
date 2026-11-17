"""Audit supplied national export CSV or compare models after availability checks."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trade_news.articles import read_jsonl
from trade_news.contextual import verify_scores
from trade_news.economics import audit_trade, compare, load_trade, news_features

parser = argparse.ArgumentParser()
parser.add_argument("command", choices=["audit", "compare"])
parser.add_argument("--trade-csv", required=True)
parser.add_argument("--data-dir", default="data")
parser.add_argument("--output", required=True)
parser.add_argument("--exclude-reporting", action="store_true")
parser.add_argument("--fixed-domains", nargs="+")
parser.add_argument("--allow-revised-history", action="store_true")
parser.add_argument("--assumed-release-lag", type=int, choices=[1, 2, 3])
args = parser.parse_args()
trade = load_trade(args.trade_csv)
if args.command == "audit":
    report = audit_trade(trade)
else:
    directory = Path(args.data_dir)
    rows, scores = read_jsonl(directory/"headlines.jsonl"), read_jsonl(directory/"contextual_scores.jsonl")
    verify_scores(directory, scores, json.loads((directory/"contextual_manifest.json").read_text("utf8")))
    months = [r["month"] for r in json.loads((directory/"collection_log.json").read_text("utf8"))["requests"]]
    features = news_features(rows, scores, months, args.exclude_reporting, args.fixed_domains)
    coverage_path = directory/"source_coverage.json"
    if coverage_path.exists():
        window = json.loads(coverage_path.read_text("utf8"))["main_window"]
        if not window["months"]:
            parser.error("No supported primary period; inspect source coverage before fitting an economic model")
        features = features.loc[window["start"]:window["end_inclusive"]]
    report = compare(trade, features, allow_revised_history=args.allow_revised_history, assumed_release_lag=args.assumed_release_lag)
    report["reporting_candidates_excluded"] = args.exclude_reporting
    report["fixed_press_domains"] = args.fixed_domains
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf8")
print(json.dumps({k: v for k, v in report.items() if k not in {"forecasts", "skipped"}}, ensure_ascii=False, indent=2))
