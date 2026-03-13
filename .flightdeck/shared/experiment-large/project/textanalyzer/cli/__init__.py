"""textanalyzer.cli — Public API for the CLI and reporting layer."""

from textanalyzer.cli.main import main
from textanalyzer.cli.reporter import run_analysis, AnalysisResults, AnalysisOptions
from textanalyzer.cli.formatter import format_text, format_json
from textanalyzer.cli.html_report import generate_html_report

__all__ = [
    "main",
    "run_analysis",
    "AnalysisResults",
    "AnalysisOptions",
    "format_text",
    "format_json",
    "generate_html_report",
]
