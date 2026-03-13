"""Data models and error types for the text analysis pipeline.

All dataclasses and exceptions defined here form the public API contract
shared across every module in textanalyzer.core. See blackboard-cross.md
for the authoritative specification.
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class TextDocument:
    """A parsed text document."""

    content: str
    source: str  # file path or "<string>"
    char_count: int
    line_count: int


@dataclass
class Token:
    """A single tokenized word with metadata."""

    text: str  # lowercase, stripped
    position: int  # index in original document
    is_stopword: bool


@dataclass
class FrequencyResult:
    """Word frequency analysis results."""

    total_tokens: int
    unique_tokens: int
    frequencies: dict[str, int]  # word → count, sorted desc
    relative_frequencies: dict[str, float]  # word → count/total


@dataclass
class SentimentResult:
    """Sentiment analysis results."""

    score: float  # -1.0 to 1.0
    label: str  # "positive" | "negative" | "neutral"
    positive_count: int
    negative_count: int


@dataclass
class StatisticsResult:
    """Text statistics results."""

    char_count: int
    word_count: int
    sentence_count: int
    avg_word_length: float
    vocabulary_size: int
    lexical_diversity: float  # unique/total


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------

class TextAnalyzerError(Exception):
    """Base exception for the text analyzer pipeline."""


class FileNotFoundError(TextAnalyzerError):
    """Raised when a requested file does not exist."""


class ParseError(TextAnalyzerError):
    """Raised when a file cannot be decoded or parsed."""


class EmptyDocumentError(TextAnalyzerError):
    """Raised when the input document is empty."""
