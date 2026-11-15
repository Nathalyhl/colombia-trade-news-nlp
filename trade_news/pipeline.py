"""Compatibility imports for the article-text pipeline."""
from .articles import read_jsonl
from .bank_method import aggregate
from .corpus import build, write_json

__all__ = ["read_jsonl", "aggregate", "build", "write_json"]
