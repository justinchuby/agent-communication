"""Integration tests — end-to-end pipeline verification.

Runs the full CLI pipeline via ``textanalyzer.cli.main.main()`` and verifies
text, JSON, and HTML output formats, error handling, and flag behaviour.
"""

import json
import os
import tempfile

import pytest

from textanalyzer.cli.main import main

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def _fixture(name: str) -> str:
    return os.path.join(FIXTURES_DIR, name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(args: list[str], capsys) -> tuple[int, str, str]:
    """Call main() with *args* and return (exit_code, stdout, stderr)."""
    code = main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# ---------------------------------------------------------------------------
# 1. Text output — default format
# ---------------------------------------------------------------------------

class TestTextOutput:
    def test_text_report_header(self, capsys):
        code, out, _ = _run(["analyze", _fixture("sample.txt")], capsys)
        assert code == 0
        assert "=== Text Analysis Report ===" in out

    def test_text_report_has_statistics(self, capsys):
        code, out, _ = _run(["analyze", _fixture("sample.txt")], capsys)
        assert code == 0
        assert "Words:" in out
        assert "Sentences:" in out
        assert "Vocabulary:" in out
        assert "Lexical Diversity:" in out

    def test_text_report_has_top_words(self, capsys):
        code, out, _ = _run(["analyze", _fixture("sample.txt")], capsys)
        assert code == 0
        assert "Top Words:" in out
        assert "WORD" in out
        assert "COUNT" in out

    def test_text_report_has_sentiment(self, capsys):
        code, out, _ = _run(["analyze", _fixture("sample.txt")], capsys)
        assert code == 0
        assert "Sentiment:" in out
        assert "Score:" in out
        assert "Label:" in out


# ---------------------------------------------------------------------------
# 2. JSON output
# ---------------------------------------------------------------------------

class TestJsonOutput:
    def test_json_valid(self, capsys):
        code, out, _ = _run(
            ["analyze", _fixture("sample.txt"), "--format", "json"], capsys
        )
        assert code == 0
        data = json.loads(out)
        assert isinstance(data, dict)

    def test_json_has_frequency_fields(self, capsys):
        code, out, _ = _run(
            ["analyze", _fixture("sample.txt"), "--format", "json"], capsys
        )
        assert code == 0
        data = json.loads(out)
        assert "frequency" in data
        freq = data["frequency"]
        assert "frequencies" in freq
        assert "relative_frequencies" in freq
        assert "total_tokens" in freq
        assert "unique_tokens" in freq

    def test_json_has_statistics_fields(self, capsys):
        code, out, _ = _run(
            ["analyze", _fixture("sample.txt"), "--format", "json"], capsys
        )
        assert code == 0
        data = json.loads(out)
        assert "statistics" in data
        stats = data["statistics"]
        for field in (
            "char_count", "word_count", "sentence_count",
            "avg_word_length", "vocabulary_size", "lexical_diversity",
        ):
            assert field in stats

    def test_json_excludes_tokens(self, capsys):
        code, out, _ = _run(
            ["analyze", _fixture("sample.txt"), "--format", "json"], capsys
        )
        assert code == 0
        data = json.loads(out)
        assert "tokens" not in data
        assert "token_count" in data
        assert isinstance(data["token_count"], int)


# ---------------------------------------------------------------------------
# 3. HTML output
# ---------------------------------------------------------------------------

class TestHtmlOutput:
    def test_html_creates_file(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "report.html")
            code, _, _ = _run(
                ["analyze", _fixture("sample.txt"),
                 "--format", "html", "--output", out_path],
                capsys,
            )
            assert code == 0
            assert os.path.isfile(out_path)

    def test_html_has_expected_sections(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "report.html")
            _run(
                ["analyze", _fixture("sample.txt"),
                 "--format", "html", "--output", out_path],
                capsys,
            )
            content = open(out_path, encoding="utf-8").read()
            assert "Text Analysis Report" in content
            assert "Summary Statistics" in content
            assert "Word Frequency" in content
            assert "Sentiment Analysis" in content

    def test_html_is_valid_structure(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "report.html")
            _run(
                ["analyze", _fixture("sample.txt"),
                 "--format", "html", "--output", out_path],
                capsys,
            )
            content = open(out_path, encoding="utf-8").read()
            assert content.startswith("<!DOCTYPE html>")
            assert "</html>" in content


# ---------------------------------------------------------------------------
# 4. Error handling — nonexistent file → exit 1
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_nonexistent_file_exit_code_1(self, capsys):
        code, _, err = _run(["analyze", "/no/such/file.txt"], capsys)
        assert code == 1
        assert "Error" in err

    def test_empty_file_exit_code_2(self, capsys):
        code, _, err = _run(["analyze", _fixture("empty.txt")], capsys)
        assert code == 2
        assert "Error" in err


# ---------------------------------------------------------------------------
# 5. --no-sentiment flag
# ---------------------------------------------------------------------------

class TestNoSentimentFlag:
    def test_no_sentiment_text(self, capsys):
        code, out, _ = _run(
            ["analyze", _fixture("sample.txt"), "--no-sentiment"], capsys
        )
        assert code == 0
        assert "Sentiment:" not in out

    def test_no_sentiment_json(self, capsys):
        code, out, _ = _run(
            ["analyze", _fixture("sample.txt"),
             "--format", "json", "--no-sentiment"],
            capsys,
        )
        assert code == 0
        data = json.loads(out)
        assert data.get("sentiment") is None

    def test_no_sentiment_html(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "report.html")
            _run(
                ["analyze", _fixture("sample.txt"),
                 "--format", "html", "--output", out_path,
                 "--no-sentiment"],
                capsys,
            )
            content = open(out_path, encoding="utf-8").read()
            assert "Sentiment Analysis" not in content


# ---------------------------------------------------------------------------
# 6. --top-n flag
# ---------------------------------------------------------------------------

class TestTopNFlag:
    def test_top_n_limits_text_output(self, capsys):
        code, out, _ = _run(
            ["analyze", _fixture("sample.txt"), "--top-n", "5"], capsys
        )
        assert code == 0
        # Count data rows in Top Words table (lines between separators)
        in_table = False
        data_rows = 0
        for line in out.splitlines():
            if "Top Words:" in line:
                in_table = True
                continue
            if in_table and line.startswith("-"):
                continue
            if in_table and "WORD" in line and "COUNT" in line:
                continue
            if in_table and "|" in line:
                data_rows += 1
            elif in_table and line.strip() == "":
                break
        assert data_rows <= 5

    def test_top_n_limits_json_output(self, capsys):
        code, out, _ = _run(
            ["analyze", _fixture("sample.txt"),
             "--format", "json", "--top-n", "3"],
            capsys,
        )
        assert code == 0
        data = json.loads(out)
        assert len(data["frequency"]["frequencies"]) <= 3


# ---------------------------------------------------------------------------
# 7. Edge cases — different fixture files
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_short_file(self, capsys):
        code, out, _ = _run(["analyze", _fixture("short.txt")], capsys)
        assert code == 0
        assert "=== Text Analysis Report ===" in out

    def test_unicode_file(self, capsys):
        code, out, _ = _run(["analyze", _fixture("unicode.txt")], capsys)
        assert code == 0
        assert "=== Text Analysis Report ===" in out

    def test_single_word_file(self, capsys):
        code, out, _ = _run(["analyze", _fixture("single_word.txt")], capsys)
        assert code == 0
        assert "=== Text Analysis Report ===" in out

    def test_no_command_shows_help(self, capsys):
        code, out, _ = _run([], capsys)
        assert code == 2
