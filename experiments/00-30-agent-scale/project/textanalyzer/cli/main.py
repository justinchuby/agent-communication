"""CLI entry point — argparse-based command-line interface.

Provides the ``textanalyzer analyze`` command which runs the full text
analysis pipeline and outputs results in text, JSON, or HTML format.

Exit codes: 0 = success, 1 = file not found, 2 = parse/analysis error, 3 = output error.
"""

import argparse
import sys

from textanalyzer.cli.reporter import run_analysis, AnalysisOptions
from textanalyzer.cli.formatter import format_text, format_json
from textanalyzer.cli.html_report import generate_html_report
from textanalyzer.core.models import (
    TextAnalyzerError,
    FileNotFoundError as TAFileNotFoundError,
    ParseError,
    EmptyDocumentError,
)


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments, run analysis, and output formatted results.

    Args:
        argv: Command-line arguments. Uses ``sys.argv[1:]`` when *None*.

    Returns:
        Exit code: 0 on success, 1 for file-not-found, 2 for parse/analysis
        errors, 3 for output I/O errors.
    """
    parser = argparse.ArgumentParser(
        prog="textanalyzer",
        description="Analyze text files for word frequency, sentiment, and statistics.",
    )
    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze a text file."
    )
    analyze_parser.add_argument("file", help="Path to the text file to analyze.")
    analyze_parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        dest="format",
        help="Output format (default: text).",
    )
    analyze_parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of top words to include (default: 10).",
    )
    analyze_parser.add_argument(
        "--no-sentiment",
        action="store_true",
        help="Skip sentiment analysis.",
    )
    analyze_parser.add_argument(
        "--output",
        default=None,
        help="Output file path (used with --format html, default: report.html).",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 2

    options = AnalysisOptions(
        top_n=args.top_n,
        include_sentiment=not args.no_sentiment,
    )

    try:
        results = run_analysis(args.file, options)

        if args.format == "text":
            print(format_text(results))
        elif args.format == "json":
            print(format_json(results))
        elif args.format == "html":
            output_path = args.output or "report.html"
            generate_html_report(results, output_path)
    except TAFileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (ParseError, EmptyDocumentError, TextAnalyzerError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except (IOError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
