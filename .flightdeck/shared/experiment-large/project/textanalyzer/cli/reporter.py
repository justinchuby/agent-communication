"""Analysis orchestrator — runs the full pipeline and bundles results.

Owner: Team Beta developer (see blackboard-beta.md → beta-reporter)

Implement:
    @dataclass
    class AnalysisOptions:
        top_n: int = 10
        include_sentiment: bool = True
        remove_stopwords: bool = False

    @dataclass
    class AnalysisResults:
        document: TextDocument
        tokens: list[Token]
        frequency: FrequencyResult
        sentiment: SentimentResult | None  # None if sentiment disabled
        statistics: StatisticsResult
        options: AnalysisOptions

    run_analysis(file_path: str, options: AnalysisOptions | None = None) -> AnalysisResults
        - Call parse_file(file_path) → document
        - Call tokenize(document, remove_stopwords=options.remove_stopwords) → tokens
        - Call word_frequency(tokens, top_n=options.top_n) → frequency
        - If options.include_sentiment: call analyze_sentiment(tokens) → sentiment
        - Call compute_statistics(document, tokens) → statistics
        - Bundle into AnalysisResults and return
        - Let TextAnalyzerError subtypes propagate (CLI catches them)

Dependencies: All core modules (parser, tokenizer, frequency, sentiment, statistics)
"""

from dataclasses import dataclass

from textanalyzer.core.models import (
    TextDocument,
    Token,
    FrequencyResult,
    SentimentResult,
    StatisticsResult,
)
from textanalyzer.core.parser import parse_file
from textanalyzer.core.tokenizer import tokenize
from textanalyzer.core.frequency import word_frequency
from textanalyzer.core.sentiment import analyze_sentiment
from textanalyzer.core.statistics import compute_statistics


@dataclass
class AnalysisOptions:
    """Options controlling which analyses to run and how."""

    top_n: int = 10
    include_sentiment: bool = True
    remove_stopwords: bool = False


@dataclass
class AnalysisResults:
    """Bundled results from a complete analysis pipeline run."""

    document: TextDocument
    tokens: list[Token]
    frequency: FrequencyResult
    sentiment: SentimentResult | None
    statistics: StatisticsResult
    options: AnalysisOptions


def run_analysis(
    file_path: str, options: AnalysisOptions | None = None
) -> AnalysisResults:
    """Run the full analysis pipeline on a file.

    Parses the file, tokenizes, computes frequency/sentiment/statistics,
    and returns all results bundled together.

    Raises:
        TextAnalyzerError subtypes: propagated from core modules.
    """
    if options is None:
        options = AnalysisOptions()

    document = parse_file(file_path)
    tokens = tokenize(document, remove_stopwords=options.remove_stopwords)
    frequency = word_frequency(tokens, top_n=options.top_n)
    sentiment = (
        analyze_sentiment(tokens) if options.include_sentiment else None
    )
    statistics = compute_statistics(document, tokens)

    return AnalysisResults(
        document=document,
        tokens=tokens,
        frequency=frequency,
        sentiment=sentiment,
        statistics=statistics,
        options=options,
    )
