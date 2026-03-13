"""Unit tests for textanalyzer.core.statistics — compute_statistics function."""

import pytest
from textanalyzer.core.models import TextDocument, Token, StatisticsResult
from textanalyzer.core.statistics import compute_statistics


def _make_doc(text):
    return TextDocument(
        content=text,
        source="<string>",
        char_count=len(text),
        line_count=text.count("\n") + 1,
    )


def _make_tokens(words):
    return [Token(text=w, position=i, is_stopword=False) for i, w in enumerate(words)]


class TestComputeStatistics:
    def test_basic(self):
        doc = _make_doc("Hello world. Goodbye world!")
        tokens = _make_tokens(["hello", "world", "goodbye", "world"])
        result = compute_statistics(doc, tokens)
        assert isinstance(result, StatisticsResult)
        assert result.char_count == len(doc.content)
        assert result.word_count == 4
        assert result.sentence_count == 2  # . and !
        assert result.vocabulary_size == 3  # hello, world, goodbye
        assert result.lexical_diversity == pytest.approx(3 / 4)
        assert result.avg_word_length == pytest.approx((5 + 5 + 7 + 5) / 4)

    def test_empty_document(self):
        doc = _make_doc("")
        tokens = []
        result = compute_statistics(doc, tokens)
        assert result.char_count == 0
        assert result.word_count == 0
        assert result.sentence_count == 0
        assert result.avg_word_length == 0.0
        assert result.vocabulary_size == 0
        assert result.lexical_diversity == 0.0

    def test_single_word(self):
        doc = _make_doc("hello")
        tokens = _make_tokens(["hello"])
        result = compute_statistics(doc, tokens)
        assert result.word_count == 1
        assert result.vocabulary_size == 1
        assert result.lexical_diversity == pytest.approx(1.0)
        assert result.avg_word_length == pytest.approx(5.0)
        assert result.sentence_count == 0  # no sentence-ending punctuation

    def test_sentence_counting(self):
        doc = _make_doc("One. Two! Three? Four")
        tokens = _make_tokens(["one", "two", "three", "four"])
        result = compute_statistics(doc, tokens)
        assert result.sentence_count == 3  # . ! ?

    def test_all_same_words(self):
        doc = _make_doc("go go go")
        tokens = _make_tokens(["go", "go", "go"])
        result = compute_statistics(doc, tokens)
        assert result.vocabulary_size == 1
        assert result.lexical_diversity == pytest.approx(1 / 3)
