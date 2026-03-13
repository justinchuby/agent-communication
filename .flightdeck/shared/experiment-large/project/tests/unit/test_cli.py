"""Unit tests for textanalyzer.cli modules (formatter, reporter, html_report).

Covers formatter output structure, reporter pipeline orchestration,
HTML report generation, and CLI arg parsing / exit codes.
All core API calls are mocked via unittest.mock.patch.
"""

import json
import os
import tempfile

import pytest
from unittest.mock import patch, MagicMock

from textanalyzer.core.models import (
    TextDocument,
    Token,
    FrequencyResult,
    SentimentResult,
    StatisticsResult,
    TextAnalyzerError,
    FileNotFoundError as TAFileNotFoundError,
    ParseError,
)
from textanalyzer.cli.reporter import AnalysisOptions, AnalysisResults, run_analysis
from textanalyzer.cli.formatter import format_text, format_json
from textanalyzer.cli.html_report import generate_html_report
from textanalyzer.cli.main import main


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_document():
    return TextDocument(content="hello world hello", source="test.txt", char_count=17, line_count=1)


@pytest.fixture
def sample_tokens():
    return [
        Token(text="hello", position=0, is_stopword=False),
        Token(text="world", position=1, is_stopword=False),
        Token(text="hello", position=2, is_stopword=False),
    ]


@pytest.fixture
def sample_frequency():
    return FrequencyResult(
        total_tokens=3,
        unique_tokens=2,
        frequencies={"hello": 2, "world": 1},
        relative_frequencies={"hello": 0.6667, "world": 0.3333},
    )


@pytest.fixture
def sample_sentiment():
    return SentimentResult(score=0.25, label="positive", positive_count=2, negative_count=1)


@pytest.fixture
def sample_statistics():
    return StatisticsResult(
        char_count=17, word_count=3, sentence_count=1,
        avg_word_length=5.0, vocabulary_size=2, lexical_diversity=0.67,
    )


@pytest.fixture
def sample_results(sample_document, sample_tokens, sample_frequency, sample_sentiment, sample_statistics):
    return AnalysisResults(
        document=sample_document,
        tokens=sample_tokens,
        frequency=sample_frequency,
        sentiment=sample_sentiment,
        statistics=sample_statistics,
        options=AnalysisOptions(),
    )


@pytest.fixture
def results_no_sentiment(sample_document, sample_tokens, sample_frequency, sample_statistics):
    return AnalysisResults(
        document=sample_document,
        tokens=sample_tokens,
        frequency=sample_frequency,
        sentiment=None,
        statistics=sample_statistics,
        options=AnalysisOptions(include_sentiment=False),
    )


# ---------------------------------------------------------------------------
# Formatter tests
# ---------------------------------------------------------------------------

class TestFormatText:
    def test_output_contains_header_and_stats(self, sample_results):
        output = format_text(sample_results)
        assert "=== Text Analysis Report ===" in output
        assert "Source: test.txt" in output
        assert "Words: 3" in output
        assert "Vocabulary: 2" in output

    def test_output_contains_frequency_table(self, sample_results):
        output = format_text(sample_results)
        assert "Top Words:" in output
        assert "hello" in output
        assert "world" in output
        assert "WORD" in output
        assert "COUNT" in output

    def test_none_sentiment_omits_section(self, results_no_sentiment):
        output = format_text(results_no_sentiment)
        assert "Sentiment:" not in output

    def test_sentiment_section_present_when_included(self, sample_results):
        output = format_text(sample_results)
        assert "Sentiment:" in output
        assert "positive" in output
        assert "0.25" in output


class TestFormatJson:
    def test_valid_json_output(self, sample_results):
        output = format_json(sample_results)
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_tokens_excluded_token_count_present(self, sample_results):
        output = format_json(sample_results)
        data = json.loads(output)
        assert "tokens" not in data
        assert data["token_count"] == 3

    def test_json_contains_frequency_data(self, sample_results):
        output = format_json(sample_results)
        data = json.loads(output)
        assert data["frequency"]["frequencies"]["hello"] == 2

    def test_json_none_sentiment(self, results_no_sentiment):
        output = format_json(results_no_sentiment)
        data = json.loads(output)
        assert data["sentiment"] is None


# ---------------------------------------------------------------------------
# Reporter tests
# ---------------------------------------------------------------------------

class TestAnalysisOptionsDefaults:
    def test_default_values(self):
        opts = AnalysisOptions()
        assert opts.top_n == 10
        assert opts.include_sentiment is True
        assert opts.remove_stopwords is False

    def test_custom_values(self):
        opts = AnalysisOptions(top_n=5, include_sentiment=False, remove_stopwords=True)
        assert opts.top_n == 5
        assert opts.include_sentiment is False
        assert opts.remove_stopwords is True


class TestRunAnalysis:
    @patch("textanalyzer.cli.reporter.compute_statistics")
    @patch("textanalyzer.cli.reporter.analyze_sentiment")
    @patch("textanalyzer.cli.reporter.word_frequency")
    @patch("textanalyzer.cli.reporter.tokenize")
    @patch("textanalyzer.cli.reporter.parse_file")
    def test_pipeline_calls_all_core_modules(
        self, mock_parse, mock_tokenize, mock_freq, mock_sentiment, mock_stats,
        sample_document, sample_tokens, sample_frequency, sample_sentiment, sample_statistics,
    ):
        mock_parse.return_value = sample_document
        mock_tokenize.return_value = sample_tokens
        mock_freq.return_value = sample_frequency
        mock_sentiment.return_value = sample_sentiment
        mock_stats.return_value = sample_statistics

        result = run_analysis("test.txt")

        mock_parse.assert_called_once_with("test.txt")
        mock_tokenize.assert_called_once_with(sample_document, remove_stopwords=False)
        mock_freq.assert_called_once_with(sample_tokens, top_n=10)
        mock_sentiment.assert_called_once_with(sample_tokens)
        mock_stats.assert_called_once_with(sample_document, sample_tokens)
        assert result.document is sample_document

    @patch("textanalyzer.cli.reporter.compute_statistics")
    @patch("textanalyzer.cli.reporter.analyze_sentiment")
    @patch("textanalyzer.cli.reporter.word_frequency")
    @patch("textanalyzer.cli.reporter.tokenize")
    @patch("textanalyzer.cli.reporter.parse_file")
    def test_sentiment_skipped_when_disabled(
        self, mock_parse, mock_tokenize, mock_freq, mock_sentiment, mock_stats,
        sample_document, sample_tokens, sample_frequency, sample_statistics,
    ):
        mock_parse.return_value = sample_document
        mock_tokenize.return_value = sample_tokens
        mock_freq.return_value = sample_frequency
        mock_stats.return_value = sample_statistics

        opts = AnalysisOptions(include_sentiment=False)
        result = run_analysis("test.txt", opts)

        mock_sentiment.assert_not_called()
        assert result.sentiment is None

    @patch("textanalyzer.cli.reporter.parse_file")
    def test_error_propagation(self, mock_parse):
        mock_parse.side_effect = TAFileNotFoundError("not found")
        with pytest.raises(TAFileNotFoundError):
            run_analysis("missing.txt")

    @patch("textanalyzer.cli.reporter.compute_statistics")
    @patch("textanalyzer.cli.reporter.analyze_sentiment")
    @patch("textanalyzer.cli.reporter.word_frequency")
    @patch("textanalyzer.cli.reporter.tokenize")
    @patch("textanalyzer.cli.reporter.parse_file")
    def test_default_options_when_none(
        self, mock_parse, mock_tokenize, mock_freq, mock_sentiment, mock_stats,
        sample_document, sample_tokens, sample_frequency, sample_sentiment, sample_statistics,
    ):
        mock_parse.return_value = sample_document
        mock_tokenize.return_value = sample_tokens
        mock_freq.return_value = sample_frequency
        mock_sentiment.return_value = sample_sentiment
        mock_stats.return_value = sample_statistics

        result = run_analysis("test.txt", None)
        assert result.options.top_n == 10
        assert result.options.include_sentiment is True


# ---------------------------------------------------------------------------
# HTML report tests
# ---------------------------------------------------------------------------

class TestGenerateHtmlReport:
    def test_file_creation(self, sample_results):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            path = tmp.name
        try:
            generate_html_report(sample_results, path)
            assert os.path.exists(path)
            content = open(path, encoding="utf-8").read()
            assert content.startswith("<!DOCTYPE html>")
        finally:
            os.unlink(path)

    def test_html_sections_present(self, sample_results):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            path = tmp.name
        try:
            generate_html_report(sample_results, path)
            content = open(path, encoding="utf-8").read()
            assert "Summary Statistics" in content
            assert "Sentiment Analysis" in content
            assert "Complete Word Frequencies" in content
            assert "test.txt" in content
        finally:
            os.unlink(path)

    def test_none_sentiment_skipped(self, results_no_sentiment):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            path = tmp.name
        try:
            generate_html_report(results_no_sentiment, path)
            content = open(path, encoding="utf-8").read()
            assert "Sentiment Analysis" not in content
        finally:
            os.unlink(path)

    def test_relative_frequencies_used_in_table(self, sample_results):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            path = tmp.name
        try:
            generate_html_report(sample_results, path)
            content = open(path, encoding="utf-8").read()
            # relative_frequencies: hello=0.6667 → 66.7%, world=0.3333 → 33.3%
            assert "66.7%" in content
            assert "33.3%" in content
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# CLI main tests (supplementary — test_main.py has full coverage)
# ---------------------------------------------------------------------------

class TestCliMain:
    def test_no_command_returns_exit_2(self):
        assert main([]) == 2

    @patch("textanalyzer.cli.main.run_analysis")
    def test_success_exit_0(self, mock_run, sample_results):
        mock_run.return_value = sample_results
        assert main(["analyze", "test.txt"]) == 0

    @patch("textanalyzer.cli.main.run_analysis")
    def test_file_not_found_exit_1(self, mock_run):
        mock_run.side_effect = TAFileNotFoundError("no such file")
        assert main(["analyze", "missing.txt"]) == 1

    @patch("textanalyzer.cli.main.run_analysis")
    def test_parse_error_exit_2(self, mock_run):
        mock_run.side_effect = ParseError("bad encoding")
        assert main(["analyze", "bad.txt"]) == 2
