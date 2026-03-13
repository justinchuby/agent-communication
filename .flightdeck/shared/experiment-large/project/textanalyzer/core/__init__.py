"""textanalyzer.core — Public API for the text analysis library.

Re-export the public API so users can do::

    from textanalyzer.core import parse_file, tokenize, word_frequency, ...

Exports:
    Models: TextDocument, Token, FrequencyResult, SentimentResult, StatisticsResult
    Errors: TextAnalyzerError, FileNotFoundError, ParseError, EmptyDocumentError
    Functions: parse_file, parse_string, tokenize, word_frequency,
              analyze_sentiment, compute_statistics
"""

from textanalyzer.core.models import (
    TextDocument,
    Token,
    FrequencyResult,
    SentimentResult,
    StatisticsResult,
    TextAnalyzerError,
    FileNotFoundError,
    ParseError,
    EmptyDocumentError,
)
from textanalyzer.core.parser import parse_file, parse_string
from textanalyzer.core.tokenizer import tokenize
from textanalyzer.core.frequency import word_frequency
from textanalyzer.core.sentiment import analyze_sentiment
from textanalyzer.core.statistics import compute_statistics

__all__ = [
    # Models
    "TextDocument",
    "Token",
    "FrequencyResult",
    "SentimentResult",
    "StatisticsResult",
    # Errors
    "TextAnalyzerError",
    "FileNotFoundError",
    "ParseError",
    "EmptyDocumentError",
    # Functions
    "parse_file",
    "parse_string",
    "tokenize",
    "word_frequency",
    "analyze_sentiment",
    "compute_statistics",
]
