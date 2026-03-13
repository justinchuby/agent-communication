# Cross-Team Blackboard — API Contracts

## Contract Status
- version: 1
- alpha-architect-approved: true
- beta-architect-approved: false
- status: draft

## Public API (textanalyzer.core)

### Data Models (core/models.py)

```python
@dataclass
class TextDocument:
    content: str
    source: str  # file path or "<string>"
    char_count: int
    line_count: int

@dataclass
class Token:
    text: str          # lowercase, stripped
    position: int      # index in original document
    is_stopword: bool

@dataclass
class FrequencyResult:
    total_tokens: int
    unique_tokens: int
    frequencies: dict[str, int]          # word → count, sorted desc
    relative_frequencies: dict[str, float]  # word → count/total

@dataclass
class SentimentResult:
    score: float       # -1.0 to 1.0
    label: str         # "positive" | "negative" | "neutral"
    positive_count: int
    negative_count: int

@dataclass
class StatisticsResult:
    char_count: int
    word_count: int
    sentence_count: int
    avg_word_length: float
    vocabulary_size: int
    lexical_diversity: float  # unique/total
```

### Functions (core API)

```python
# core/parser.py
def parse_file(path: str) -> TextDocument: ...
def parse_string(text: str, source: str = "<string>") -> TextDocument: ...

# core/tokenizer.py
def tokenize(document: TextDocument, remove_stopwords: bool = False) -> list[Token]: ...

# core/frequency.py
def word_frequency(tokens: list[Token], top_n: int | None = None) -> FrequencyResult: ...

# core/sentiment.py
def analyze_sentiment(tokens: list[Token]) -> SentimentResult: ...

# core/statistics.py
def compute_statistics(document: TextDocument, tokens: list[Token]) -> StatisticsResult: ...
```

### Error Types

```python
class TextAnalyzerError(Exception): ...
class FileNotFoundError(TextAnalyzerError): ...   # file doesn't exist
class ParseError(TextAnalyzerError): ...           # can't decode/parse file
class EmptyDocumentError(TextAnalyzerError): ...   # empty input
```

## Contract Change Log
- v1: Initial contract (pending approval)

## Cross-Team Decisions
Format: `decision: string — proposed-by: team — approved-by: [alpha-arch, beta-arch] — status: pending|approved`

## Cross-Team Blockers
Format: `blocker: string — raised-by: team — assigned-to: team — status: open|resolved`
