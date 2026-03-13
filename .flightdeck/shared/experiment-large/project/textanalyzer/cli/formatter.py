"""Output formatter — converts analysis results to text and JSON.

Provides two output formats:
    format_text: human-readable aligned report
    format_json: machine-readable JSON with all fields
"""

import json
from dataclasses import asdict

from textanalyzer.cli.reporter import AnalysisResults


def format_text(results: AnalysisResults) -> str:
    """Format analysis results as a human-readable text report.

    Includes summary statistics, top words table, and optional sentiment.
    """
    lines: list[str] = []

    # Header
    lines.append("=== Text Analysis Report ===")
    lines.append(f"Source: {results.document.source}")
    lines.append("")

    # Summary statistics
    stats = results.statistics
    lines.append(
        f"Words: {stats.word_count} | "
        f"Sentences: {stats.sentence_count} | "
        f"Vocabulary: {stats.vocabulary_size}"
    )
    lines.append(f"Lexical Diversity: {stats.lexical_diversity:.2f}")
    lines.append("")

    # Top words table
    frequencies = results.frequency.frequencies
    if frequencies:
        # Compute column widths for alignment
        words = list(frequencies.keys())
        counts = [frequencies[w] for w in words]
        relative = results.frequency.relative_frequencies

        word_width = max(len("WORD"), max(len(w) for w in words))
        count_width = max(len("COUNT"), max(len(str(c)) for c in counts))

        header = (
            f"{'WORD':<{word_width}} | "
            f"{'COUNT':>{count_width}} | "
            f"FREQUENCY"
        )
        separator = "-" * len(header)

        lines.append("Top Words:")
        lines.append(separator)
        lines.append(header)
        lines.append(separator)
        for word in words:
            count = frequencies[word]
            freq = relative.get(word, 0.0)
            lines.append(
                f"{word:<{word_width}} | "
                f"{count:>{count_width}} | "
                f"{freq:.4f}"
            )
        lines.append(separator)
        lines.append("")

    # Sentiment (optional)
    if results.sentiment is not None:
        lines.append("Sentiment:")
        lines.append(f"  Score: {results.sentiment.score:.2f}")
        lines.append(f"  Label: {results.sentiment.label}")
        lines.append("")

    return "\n".join(lines)


def format_json(results: AnalysisResults) -> str:
    """Format analysis results as pretty-printed JSON.

    Excludes the raw tokens list to avoid memory issues on large files.
    Includes token_count as a summary instead.
    """
    data = asdict(results)
    data["token_count"] = len(results.tokens)
    del data["tokens"]
    return json.dumps(data, indent=2)
