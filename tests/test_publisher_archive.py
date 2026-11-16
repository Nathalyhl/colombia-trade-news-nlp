"""Synthetic HTTP fixtures test acquisition mechanics, not domain accuracy."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trade_news.articles import read_jsonl, write_jsonl
from trade_news.publisher_archive import collect_archive


def response(payload, headers=None):
    stream = io.BytesIO(payload)
    stream.headers = headers or {}
    return stream


class PublisherArchiveTests(unittest.TestCase):
    def test_first_run_without_manifest_and_cached_resume(self):
        robots = b"User-agent: *\nDisallow:\n"
        posts = [{"id": 123, "date": "2020-03-10T10:00:00", "date_gmt": "2020-03-10T15:00:00",
                  "link": "https://analdex.org/synthetic-fixture", "title": {"rendered": "Exportaciones colombianas de cafe"},
                  "content": {"rendered": "<p>Colombia exporta bienes textiles hacia mercados internacionales con oportunidades comerciales y dificultades.</p>"}}]
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            write_jsonl(directory/"headlines_raw.jsonl", [])
            (directory/"collection_log.json").write_text(json.dumps({"start": "2020-03-01", "end_exclusive": "2020-04-01", "requests": []}), encoding="utf8")
            with patch("trade_news.publisher_archive.urlopen", side_effect=[response(robots), response(json.dumps(posts).encode(), {"X-WP-TotalPages": "1", "X-WP-Total": "1"})]), patch("trade_news.publisher_archive.time.sleep"):
                collect_archive(directory, "2020-03-01", "2020-04-01")
            manifest = read_jsonl(directory/"article_manifest.jsonl")
            self.assertEqual(len(manifest), 1)
            self.assertEqual(manifest[0]["publication_date"], "2020-03-10")
            self.assertEqual(manifest[0]["fetch_status"], "article_extracted")
            self.assertEqual(manifest[0]["source_post_id"], 123)
            with patch("trade_news.publisher_archive.urlopen", side_effect=[response(robots)]), patch("trade_news.publisher_archive.time.sleep"):
                collect_archive(directory, "2020-03-01", "2020-04-01")
            self.assertEqual(read_jsonl(directory/"article_manifest.jsonl"), manifest)
            self.assertEqual(len(read_jsonl(directory/"headlines_raw.jsonl")), 1)
