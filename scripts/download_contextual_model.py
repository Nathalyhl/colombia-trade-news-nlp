"""Fetch the public pinned model files and verify their published run hashes."""
import argparse
import json
from pathlib import Path
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from trade_news.contextual import MODEL_ID, REVISION, MODEL_FILES, checksum

parser = argparse.ArgumentParser()
parser.add_argument("--output", default="data/raw/contextual_model")
args = parser.parse_args()
target = Path(args.output)
target.mkdir(parents=True, exist_ok=True)
reference = json.loads((ROOT/"reference/contextual_model.json").read_text("utf8"))
for name in MODEL_FILES:
    path = target/name
    if path.exists():
        if checksum(path) != reference["model_files_sha256"][name]:
            raise ValueError("Cached model differs from its pinned hash; preserve it before replacing")
        print("Verified cached", name, flush=True)
        continue
    url = f"https://huggingface.co/{MODEL_ID}/resolve/{REVISION}/{name}"
    temporary = path.with_suffix(path.suffix+".part")
    with urlopen(url, timeout=60) as response, temporary.open("wb") as stream:
        while chunk := response.read(1024*1024):
            stream.write(chunk)
    if checksum(temporary) != reference["model_files_sha256"][name]:
        raise ValueError("Downloaded model differs from its pinned hash")
    temporary.replace(path)
    print("Downloaded and verified", name, flush=True)
