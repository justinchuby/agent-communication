"""Unit tests for textanalyzer.core.models — dataclasses and error types."""

import pytest
from textanalyzer.core.models import (
    TextDocument,
    Token,
    FrequencyResult,
    SentimentResult,
    StatisticsResult,
    TextAnalyzerError,
    FileNotFoundError as TAFileNotFoundError,
    ParseError,
    EmptyDocumentError,
)


class TestTextDocument:
    def test_instantiation(self):
        doc = TextDocument(content="hello world", source="test.txt", char_count=11, line_count=1)
        assert doc.content == "hello world"
        assert doc.source == "test.txt"
        assert doc.char_count == 11
        assert doc.line_count == 1

    def test_field_types(self):
        doc = TextDocument(content="abc", source="<string>", char_count=3, line_count=1)
        assert isinstance(doc.content, str)
        assert isinstance(doc.source, str)
        assert isinstance(doc.char_count, int)
        assert isinstance(doc.line_count, int)

    def test_multiline_content(self):
        text = "line1\nline2\nline3"
        doc = TextDocument(content=text, source="multi.txt", char_count=len(text), line_count=3)
        assert doc.line_count == 3
        assert "\n" in doc.content


class TestToken:
    def test_instantiation(self):
        token = Token(text="hello", position=0, is_stopword=False)
        assert token.text == "hello"
        assert token.position == 0
        assert token.is_stopword is False

    def test_stopword_flag(self):
        token = Token(text="the", position=5, is_stopword=True)
        assert token.is_stopword is True

    def test_position_tracking(self):
        tokens = [Token(text=f"w{i}", position=i, is_stopword=False) for i in range(5)]
        assert [t.position for t in tokens] == [0, 1, 2, 3, 4]


class TestFrequencyResult:
    def test_instantiation(self):
        result = FrequencyResult(
            total_tokens=10,
            unique_tokens=5,
            frequencies={"hello": 3, "world": 2},
            relative_frequencies={"hello": 0.3, "world": 0.2},
        )
        assert result.total_tokens == 10
        assert result.unique_tokens == 5
        assert result.frequencies["hello"] == 3
        assert result.relative_frequencies["hello"] == pytest.approx(0.3)

    def test_empty_frequencies(self):
        result = FrequencyResult(
            total_tokens=0,
            unique_tokens=0,
            frequencies={},
            relative_frequencies={},
        )
        assert result.total_tokens == 0
        assert len(result.frequencies) == 0


class TestSentimentResult:
    def test_instantiation(self):
        result = SentimentResult(score=0.5, label="positive", positive_count=5, negative_count=0)
        assert result.score == 0.5
        assert result.label == "positive"
        assert result.positive_count == 5
        assert result.negative_count == 0

    def test_negative_score(self):
        result = SentimentResult(score=-0.8, label="negative", positive_count=1, negative_count=9)
        assert result.score < 0
        assert result.label == "negative"


class TestStatisticsResult:
    def test_instantiation(self):
        result = StatisticsResult(
            char_count=100,
            word_count=20,
            sentence_count=3,
            avg_word_length=4.5,
            vocabulary_size=15,
            lexical_diversity=0.75,
        )
        assert result.char_count == 100
        assert result.word_count == 20
        assert result.sentence_count == 3
        assert result.avg_word_length == pytest.approx(4.5)
        assert result.vocabulary_size == 15
        assert result.lexical_diversity == pytest.approx(0.75)


class TestErrorTypes:
    def test_base_error_inherits_exception(self):
        assert issubclass(TextAnalyzerError, Exception)

    def test_file_not_found_inherits_base(self):
        assert issubclass(TAFileNotFoundError, TextAnalyzerError)
        with pytest.raises(TAFileNotFoundError):
            raise TAFileNotFoundError("missing.txt")

    def test_parse_error_inherits_base(self):
        assert issubclass(ParseError, TextAnalyzerError)
        with pytest.raises(ParseError):
            raise ParseError("bad encoding")

    def test_empty_document_error_inherits_base(self):
        assert issubclass(EmptyDocumentError, TextAnalyzerError)
        with pytest.raises(EmptyDocumentError):
            raise EmptyDocumentError("empty input")
