"""Unit tests for textanalyzer.core.frequency — word_frequency function."""

import pytest
from textanalyzer.core.models import Token, FrequencyResult
from textanalyzer.core.frequency import word_frequency


def _make_tokens(words, stopwords=None):
    """Helper to create Token list from word strings."""
    stopwords = stopwords or set()
    return [
        Token(text=w, position=i, is_stopword=(w in stopwords))
        for i, w in enumerate(words)
    ]


class TestWordFrequency:
    def test_basic_count(self):
        tokens = _make_tokens(["hello", "world", "hello"])
        result = word_frequency(tokens)
        assert isinstance(result, FrequencyResult)
        assert result.frequencies["hello"] == 2
        assert result.frequencies["world"] == 1
        assert result.total_tokens == 3
        assert result.unique_tokens == 2

    def test_relative_frequencies(self):
        tokens = _make_tokens(["a", "b", "a", "a"])
        result = word_frequency(tokens)
        assert result.relative_frequencies["a"] == pytest.approx(0.75)
        assert result.relative_frequencies["b"] == pytest.approx(0.25)

    def test_top_n(self):
        tokens = _make_tokens(["x", "x", "x", "y", "y", "z"])
        result = word_frequency(tokens, top_n=2)
        assert len(result.frequencies) == 2
        assert "x" in result.frequencies
        assert "y" in result.frequencies
        assert "z" not in result.frequencies

    def test_empty_tokens(self):
        result = word_frequency([])
        assert result.total_tokens == 0
        assert result.unique_tokens == 0
        assert result.frequencies == {}
        assert result.relative_frequencies == {}

    def test_stopword_exclusion(self):
        tokens = _make_tokens(
            ["the", "cat", "is", "happy"],
            stopwords={"the", "is"},
        )
        result = word_frequency(tokens)
        assert "the" not in result.frequencies
        assert "is" not in result.frequencies
        assert "cat" in result.frequencies
        assert "happy" in result.frequencies
        assert result.total_tokens == 2

    def test_sorted_descending(self):
        tokens = _make_tokens(["a", "b", "b", "c", "c", "c"])
        result = word_frequency(tokens)
        counts = list(result.frequencies.values())
        assert counts == sorted(counts, reverse=True)
