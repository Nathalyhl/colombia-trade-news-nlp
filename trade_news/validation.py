"""Evaluate only independently supplied human sentiment labels."""
from .corpus import apply_reviews, evaluate_sentiment, read_reviews


def validate(records, annotation_path):
    reviews = read_reviews(annotation_path)
    return evaluate_sentiment(apply_reviews(records, reviews), reviews)
