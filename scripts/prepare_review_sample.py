"""Create an unlabeled diagnostic review sheet; preserve existing human work."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trade_news.review_sample import prepare

if __name__ == "__main__":
    report = prepare(Path(__file__).resolve().parents[1]/"data")
    print(f"Prepared {report['selected_size']} real source records; generated human labels: 0.")
