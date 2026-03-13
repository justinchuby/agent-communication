# textanalyzer

A Python text analysis library and CLI tool.

## Features

- **File parsing**: Read .txt, .md, .csv files with encoding detection
- **Tokenization**: Split text into tokens with optional stopword filtering
- **Word frequency**: Count word occurrences, compute relative frequencies
- **Sentiment analysis**: Keyword-based positive/negative/neutral scoring
- **Statistics**: Word count, sentence count, lexical diversity, averages
- **CLI**: Command-line interface with text, JSON, and HTML output formats

## Installation

```bash
pip install -e .
```

## Usage

### CLI

```bash
# Analyze a text file
textanalyzer analyze myfile.txt

# JSON output
textanalyzer analyze myfile.txt --format json

# HTML report
textanalyzer analyze myfile.txt --format html --output report.html

# Top 20 words, no sentiment
textanalyzer analyze myfile.txt --top-n 20 --no-sentiment
```

### Library

```python
from textanalyzer.core import parse_file, tokenize, word_frequency, compute_statistics

doc = parse_file("myfile.txt")
tokens = tokenize(doc)
freq = word_frequency(tokens, top_n=10)
stats = compute_statistics(doc, tokens)
```

## Core Library API

The `textanalyzer.core` package provides all analysis functionality. Import directly from the package:

```python
from textanalyzer.core import parse_file, tokenize, word_frequency, analyze_sentiment, compute_statistics
```

### Parsing

Create `TextDocument` objects from files or strings:

```python
from textanalyzer.core import parse_file, parse_string

doc = parse_file("myfile.txt")           # reads UTF-8, strips control chars
doc = parse_string("Hello world.")       # from an in-memory string
# doc.content, doc.source, doc.char_count, doc.line_count
```

Raises `FileNotFoundError`, `ParseError`, or `EmptyDocumentError` on failure.

### Tokenization

Split a document into `Token` objects:

```python
from textanalyzer.core import tokenize

tokens = tokenize(doc)                            # all tokens
tokens = tokenize(doc, remove_stopwords=True)     # marks stopwords (still included)
# Each token: token.text, token.position, token.is_stopword
```

### Word Frequency

Count occurrences, excluding stopwords:

```python
from textanalyzer.core import word_frequency

freq = word_frequency(tokens)              # all words
freq = word_frequency(tokens, top_n=10)    # top 10 only
# freq.total_tokens, freq.unique_tokens
# freq.frequencies      → {"word": count, ...}   sorted by count desc
# freq.relative_frequencies → {"word": 0.15, ...}
```

### Sentiment Analysis

Lexicon-based scoring with built-in positive/negative word lists (30+ words each):

```python
from textanalyzer.core import analyze_sentiment

result = analyze_sentiment(tokens)
# result.score  → float in [-1.0, 1.0]
# result.label  → "positive" | "negative" | "neutral"
# result.positive_count, result.negative_count
```

Score thresholds: `> 0.05` → positive, `< -0.05` → negative, else neutral.

### Text Statistics

Aggregate metrics for a document:

```python
from textanalyzer.core import compute_statistics

stats = compute_statistics(doc, tokens)
# stats.char_count, stats.word_count, stats.sentence_count
# stats.avg_word_length, stats.vocabulary_size, stats.lexical_diversity
```

### Error Handling

All errors inherit from `TextAnalyzerError`:

```python
from textanalyzer.core import TextAnalyzerError, FileNotFoundError, ParseError, EmptyDocumentError

try:
    doc = parse_file("missing.txt")
except FileNotFoundError:
    print("File not found")
except ParseError:
    print("Could not decode file")
except EmptyDocumentError:
    print("File is empty")
```

### Data Models

| Class | Fields |
|-------|--------|
| `TextDocument` | `content`, `source`, `char_count`, `line_count` |
| `Token` | `text`, `position`, `is_stopword` |
| `FrequencyResult` | `total_tokens`, `unique_tokens`, `frequencies`, `relative_frequencies` |
| `SentimentResult` | `score`, `label`, `positive_count`, `negative_count` |
| `StatisticsResult` | `char_count`, `word_count`, `sentence_count`, `avg_word_length`, `vocabulary_size`, `lexical_diversity` |

## Project Structure

```
textanalyzer/
├── core/              # Team Alpha — analysis library
│   ├── models.py      # Data models and error types
│   ├── parser.py      # File parsing
│   ├── tokenizer.py   # Tokenization
│   ├── frequency.py   # Word frequency analysis
│   ├── sentiment.py   # Sentiment analysis
│   └── statistics.py  # Aggregate statistics
├── cli/               # Team Beta — CLI and reporting
│   ├── main.py        # CLI entry point (argparse)
│   ├── reporter.py    # Analysis orchestrator
│   ├── formatter.py   # Text/JSON output formatting
│   └── html_report.py # HTML report generation
tests/
├── unit/              # Unit tests per module
└── integration/       # End-to-end pipeline tests
```

## License

MIT
