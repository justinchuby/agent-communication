"""Unit tests for textanalyzer.cli.main — CLI entry point."""

import os
import pytest
from unittest.mock import patch, MagicMock

from textanalyzer.cli.main import main
from textanalyzer.core.models import (
    FileNotFoundError as TAFileNotFoundError,
    ParseError,
    EmptyDocumentError,
    TextAnalyzerError,
)


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")
SAMPLE_FILE = os.path.join(FIXTURES_DIR, "sample.txt")


class TestMainNoCommand:
    """Tests for when no subcommand is given."""

    def test_no_args_returns_2(self):
        assert main([]) == 2

    def test_help_flag_exits(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0


class TestMainAnalyzeTextFormat:
    """Tests for the 'analyze' subcommand with text output."""

    def test_analyze_text_default(self, capsys):
        code = main(["analyze", SAMPLE_FILE])
        assert code == 0
        captured = capsys.readouterr()
        assert "=== Text Analysis Report ===" in captured.out

    def test_analyze_text_explicit(self, capsys):
        code = main(["analyze", SAMPLE_FILE, "--format", "text"])
        assert code == 0
        assert "Text Analysis Report" in capsys.readouterr().out

    def test_analyze_no_sentiment(self, capsys):
        code = main(["analyze", SAMPLE_FILE, "--no-sentiment"])
        assert code == 0
        output = capsys.readouterr().out
        assert "Sentiment:" not in output

    def test_analyze_top_n(self, capsys):
        code = main(["analyze", SAMPLE_FILE, "--top-n", "3"])
        assert code == 0


class TestMainAnalyzeJsonFormat:
    """Tests for JSON output format."""

    def test_json_output(self, capsys):
        code = main(["analyze", SAMPLE_FILE, "--format", "json"])
        assert code == 0
        output = capsys.readouterr().out
        assert '"document"' in output
        assert '"frequency"' in output

    def test_json_parseable(self, capsys):
        import json
        main(["analyze", SAMPLE_FILE, "--format", "json"])
        data = json.loads(capsys.readouterr().out)
        assert "document" in data
        assert "statistics" in data


class TestMainAnalyzeHtmlFormat:
    """Tests for HTML output format."""

    def test_html_creates_file(self, tmp_path):
        output_file = str(tmp_path / "report.html")
        code = main(["analyze", SAMPLE_FILE, "--format", "html", "--output", output_file])
        assert code == 0
        assert os.path.exists(output_file)
        with open(output_file, encoding="utf-8") as fh:
            content = fh.read()
        assert "<!DOCTYPE html>" in content

    def test_html_default_output_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        code = main(["analyze", SAMPLE_FILE, "--format", "html"])
        assert code == 0
        assert os.path.exists(tmp_path / "report.html")


class TestMainErrorHandling:
    """Tests for error handling and exit codes."""

    def test_file_not_found_returns_1(self, capsys):
        code = main(["analyze", "/nonexistent/path/no_such_file.txt"])
        assert code == 1
        assert "Error:" in capsys.readouterr().err

    def test_empty_file_returns_2(self, capsys):
        empty_file = os.path.join(FIXTURES_DIR, "empty.txt")
        code = main(["analyze", empty_file])
        assert code == 2
        assert "Error:" in capsys.readouterr().err

    @patch("textanalyzer.cli.main.run_analysis")
    def test_parse_error_returns_2(self, mock_run, capsys):
        mock_run.side_effect = ParseError("bad encoding")
        code = main(["analyze", "dummy.txt"])
        assert code == 2
        assert "bad encoding" in capsys.readouterr().err

    @patch("textanalyzer.cli.main.run_analysis")
    def test_generic_analyzer_error_returns_2(self, mock_run, capsys):
        mock_run.side_effect = TextAnalyzerError("unknown error")
        code = main(["analyze", "dummy.txt"])
        assert code == 2
        assert "unknown error" in capsys.readouterr().err

    @patch("textanalyzer.cli.main.generate_html_report")
    @patch("textanalyzer.cli.main.run_analysis")
    def test_io_error_returns_3(self, mock_run, mock_html, capsys):
        mock_run.return_value = MagicMock()
        mock_html.side_effect = OSError("Permission denied")
        code = main(["analyze", "dummy.txt", "--format", "html"])
        assert code == 3
        assert "Permission denied" in capsys.readouterr().err

    @patch("textanalyzer.cli.main.format_text")
    @patch("textanalyzer.cli.main.run_analysis")
    def test_format_error_inside_try(self, mock_run, mock_fmt, capsys):
        """Formatting errors (e.g. broken results) are caught, not raw tracebacks."""
        mock_run.return_value = MagicMock()
        mock_fmt.side_effect = OSError("Broken pipe")
        code = main(["analyze", "dummy.txt", "--format", "text"])
        assert code == 3
        assert "Broken pipe" in capsys.readouterr().err
