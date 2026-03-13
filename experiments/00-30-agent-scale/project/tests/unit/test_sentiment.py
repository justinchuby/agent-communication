"""Unit tests for textanalyzer.core.sentiment — analyze_sentiment function."""

import pytest
from textanalyzer.core.models import Token, SentimentResult
from textanalyzer.core.sentiment import analyze_sentiment, POSITIVE_WORDS, NEGATIVE_WORDS


def _make_tokens(words, stopwords=None):
    """Helper to create Token list from word strings."""
    stopwords = stopwords or set()
    return [
        Token(text=w, position=i, is_stopword=(w in stopwords))
        for i, w in enumerate(words)
    ]


class TestAnalyzeSentiment:
    def test_positive_text(self):
        tokens = _make_tokens(["great", "excellent", "wonderful", "day"])
        result = analyze_sentiment(tokens)
        assert isinstance(result, SentimentResult)
        assert result.score > 0.05
        assert result.label == "positive"
        assert result.positive_count >= 3

    def test_negative_text(self):
        tokens = _make_tokens(["terrible", "awful", "horrible", "day"])
        result = analyze_sentiment(tokens)
        assert result.score < -0.05
        assert result.label == "negative"
        assert result.negative_count >= 3

    def test_neutral_text(self):
        tokens = _make_tokens(["table", "chair", "window", "door"])
        result = analyze_sentiment(tokens)
        assert -0.05 <= result.score <= 0.05
        assert result.label == "neutral"

    def test_empty_tokens(self):
        result = analyze_sentiment([])
        assert result.score == 0.0
        assert result.label == "neutral"
        assert result.positive_count == 0
        assert result.negative_count == 0

    def test_mixed_sentiment(self):
        tokens = _make_tokens(["good", "bad", "great", "terrible"])
        result = analyze_sentiment(tokens)
        # Equal positive and negative — should be near neutral
        assert -0.1 <= result.score <= 0.1

    def test_score_clamped(self):
        # All positive words — score should not exceed 1.0
        pos_words = list(POSITIVE_WORDS)[:10]
        tokens = _make_tokens(pos_words)
        result = analyze_sentiment(tokens)
        assert -1.0 <= result.score <= 1.0

    def test_lexicon_sizes(self):
        assert len(POSITIVE_WORDS) >= 30
        assert len(NEGATIVE_WORDS) >= 30

    def test_stopwords_excluded_from_count(self):
        tokens = _make_tokens(
            ["the", "good", "is", "great"],
            stopwords={"the", "is"},
        )
        result = analyze_sentiment(tokens)
        # Only non-stopword tokens count
        assert result.positive_count == 2
        assert result.score > 0
