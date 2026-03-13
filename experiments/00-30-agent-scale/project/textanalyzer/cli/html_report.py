"""HTML report generator — creates self-contained HTML analysis reports.

Generates a single-file HTML report with inline CSS. No external dependencies.
Sections: header, summary stats, frequency bar chart, sentiment display, full
frequency table. Professional styling, mobile-responsive.
"""

from datetime import datetime

from textanalyzer.cli.reporter import AnalysisResults


def _escape_html(text: str) -> str:
    """Escape special characters for safe HTML embedding."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def _build_css() -> str:
    """Return the complete inline CSS stylesheet."""
    return """
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                         "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a2e;
            background: #f0f2f5;
            padding: 1rem;
        }
        .container { max-width: 900px; margin: 0 auto; }
        header {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: #fff;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }
        header h1 { font-size: 1.5rem; font-weight: 700; }
        header .timestamp { font-size: 0.85rem; opacity: 0.8; margin-top: 0.25rem; }
        .card {
            background: #fff;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        .card h2 {
            font-size: 1.15rem;
            margin-bottom: 1rem;
            color: #16213e;
            border-bottom: 2px solid #e8e8e8;
            padding-bottom: 0.5rem;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
        }
        .stat-item {
            text-align: center;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .stat-value { font-size: 1.75rem; font-weight: 700; color: #1a1a2e; }
        .stat-label { font-size: 0.8rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.05em; }
        .bar-chart { display: flex; flex-direction: column; gap: 0.4rem; }
        .bar-row { display: flex; align-items: center; gap: 0.5rem; }
        .bar-word {
            width: 100px;
            text-align: right;
            font-size: 0.85rem;
            font-weight: 500;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            flex-shrink: 0;
        }
        .bar-track { flex: 1; background: #eee; border-radius: 4px; height: 22px; position: relative; }
        .bar-fill {
            height: 100%;
            border-radius: 4px;
            background: linear-gradient(90deg, #4361ee, #3a0ca3);
            min-width: 2px;
            transition: width 0.3s;
        }
        .bar-count { width: 45px; font-size: 0.8rem; color: #6c757d; text-align: right; flex-shrink: 0; }
        .sentiment-box {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            border-radius: 8px;
        }
        .sentiment-positive { background: #d4edda; border-left: 4px solid #28a745; }
        .sentiment-negative { background: #f8d7da; border-left: 4px solid #dc3545; }
        .sentiment-neutral  { background: #e9ecef; border-left: 4px solid #6c757d; }
        .sentiment-score { font-size: 1.5rem; font-weight: 700; }
        .sentiment-label { font-size: 0.95rem; text-transform: capitalize; }
        .sentiment-counts { font-size: 0.8rem; color: #6c757d; }
        table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
        th, td { padding: 0.6rem 0.75rem; text-align: left; border-bottom: 1px solid #e8e8e8; }
        th { background: #f8f9fa; font-weight: 600; color: #16213e; position: sticky; top: 0; }
        tr:hover td { background: #f1f3f5; }
        .freq-table-wrapper { max-height: 450px; overflow-y: auto; border-radius: 8px; border: 1px solid #e8e8e8; }
        @media (max-width: 600px) {
            body { padding: 0.5rem; }
            header { padding: 1.25rem; }
            .card { padding: 1rem; }
            .bar-word { width: 70px; font-size: 0.75rem; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
    """


def _build_header(source: str, timestamp: str) -> str:
    """Build the report header section."""
    return (
        "<header>"
        f"<h1>📊 Text Analysis Report</h1>"
        f'<div class="timestamp">Source: {_escape_html(source)} · Generated: {_escape_html(timestamp)}</div>'
        "</header>"
    )


def _build_stats_card(stats) -> str:
    """Build the summary statistics card.

    Args:
        stats: A StatisticsResult instance.
    """
    items = [
        ("Words", f"{stats.word_count:,}"),
        ("Sentences", f"{stats.sentence_count:,}"),
        ("Vocabulary", f"{stats.vocabulary_size:,}"),
        ("Lexical Diversity", f"{stats.lexical_diversity:.2f}"),
    ]
    grid_items = "".join(
        f'<div class="stat-item">'
        f'<div class="stat-value">{value}</div>'
        f'<div class="stat-label">{label}</div>'
        f"</div>"
        for label, value in items
    )
    return (
        '<div class="card">'
        "<h2>Summary Statistics</h2>"
        f'<div class="stats-grid">{grid_items}</div>'
        "</div>"
    )


def _build_bar_chart(frequencies: dict[str, int], top_n: int = 20) -> str:
    """Build a CSS-only horizontal bar chart for word frequencies.

    Args:
        frequencies: Word-to-count mapping, assumed sorted descending.
        top_n: Maximum number of words to display.
    """
    top_words = list(frequencies.items())[:top_n]
    if not top_words:
        return ""
    max_count = top_words[0][1] if top_words else 1
    rows = []
    for word, count in top_words:
        pct = (count / max_count) * 100 if max_count > 0 else 0
        rows.append(
            f'<div class="bar-row">'
            f'<span class="bar-word">{_escape_html(word)}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%"></div></div>'
            f'<span class="bar-count">{count:,}</span>'
            f"</div>"
        )
    return (
        '<div class="card">'
        "<h2>Word Frequency (Top 20)</h2>"
        f'<div class="bar-chart">{"".join(rows)}</div>'
        "</div>"
    )


def _build_sentiment_section(sentiment) -> str:
    """Build the sentiment display card.

    Args:
        sentiment: A SentimentResult instance, or None to skip.
    """
    if sentiment is None:
        return ""
    css_class = f"sentiment-{sentiment.label}"
    color_map = {"positive": "#28a745", "negative": "#dc3545", "neutral": "#6c757d"}
    score_color = color_map.get(sentiment.label, "#6c757d")
    return (
        '<div class="card">'
        "<h2>Sentiment Analysis</h2>"
        f'<div class="sentiment-box {css_class}">'
        f'<div class="sentiment-score" style="color:{score_color}">{sentiment.score:+.2f}</div>'
        "<div>"
        f'<div class="sentiment-label">{_escape_html(sentiment.label)}</div>'
        f'<div class="sentiment-counts">Positive words: {sentiment.positive_count} · Negative words: {sentiment.negative_count}</div>'
        "</div>"
        "</div>"
        "</div>"
    )


def _build_frequency_table(
    frequencies: dict[str, int],
    relative_frequencies: dict[str, float],
) -> str:
    """Build the full frequency table.

    Args:
        frequencies: Word-to-count mapping, assumed sorted descending.
        relative_frequencies: Word-to-relative-frequency (count/total_tokens).
    """
    if not frequencies:
        return ""
    rows = []
    for rank, (word, count) in enumerate(frequencies.items(), start=1):
        rel_freq = relative_frequencies.get(word, 0.0) * 100
        rows.append(
            f"<tr><td>{rank}</td>"
            f"<td>{_escape_html(word)}</td>"
            f"<td>{count:,}</td>"
            f"<td>{rel_freq:.1f}%</td></tr>"
        )
    return (
        '<div class="card">'
        "<h2>Complete Word Frequencies</h2>"
        '<div class="freq-table-wrapper">'
        "<table>"
        "<thead><tr><th>#</th><th>Word</th><th>Count</th><th>Frequency</th></tr></thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        "</table></div></div>"
    )


def generate_html_report(results: AnalysisResults, output_path: str) -> None:
    """Generate a self-contained HTML analysis report.

    Writes a single HTML file with inline CSS to ``output_path``. The report
    includes summary statistics, a word frequency bar chart, optional sentiment
    display, and a full frequency table.

    Args:
        results: The bundled analysis results from ``run_analysis``.
        output_path: Destination file path for the HTML report.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sections = [
        _build_header(results.document.source, timestamp),
        _build_stats_card(results.statistics),
        _build_bar_chart(results.frequency.frequencies, top_n=20),
        _build_sentiment_section(results.sentiment),
        _build_frequency_table(
            results.frequency.frequencies,
            results.frequency.relative_frequencies,
        ),
    ]

    html = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Text Analysis Report</title>\n"
        f"{_build_css()}\n"
        "</head>\n<body>\n"
        f'<div class="container">{"".join(sections)}</div>\n'
        "</body>\n</html>"
    )

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)
