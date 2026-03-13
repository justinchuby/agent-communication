# Team Alpha Blackboard — Core Library

## Team
- sub-lead: 81918ddd
- architect: f1f81d6e
- developers: [TBD × 6]
- reviewers: [TBD × 3]
- qa-testers: [TBD × 2]
- tech-writer: TBD
- radical-thinker: TBD

## API Contracts
See blackboard-cross.md for public API that Beta depends on.

## Tasks

### alpha-models
- owner: TBD
- status: pending
- file: A:MOD
- spec: Define TextDocument, Token, FrequencyResult, SentimentResult, StatisticsResult dataclasses
- depends: none

### alpha-parser
- owner: TBD
- status: pending
- file: A:PAR
- spec: parse_file(path) → TextDocument, parse_string(text) → TextDocument. Handle UTF-8, strip control chars.
- depends: alpha-models

### alpha-tokenizer
- owner: TBD
- status: pending
- file: A:TOK
- spec: tokenize(doc) → list[Token]. Split on whitespace/punctuation, lowercase, strip. Configurable stop-word removal.
- depends: alpha-models

### alpha-frequency
- owner: TBD
- status: pending
- file: A:FRQ
- spec: word_frequency(tokens) → FrequencyResult. Count occurrences, compute relative freq, return sorted top-N.
- depends: alpha-models, alpha-tokenizer

### alpha-sentiment
- owner: TBD
- status: pending
- file: A:SNT
- spec: analyze_sentiment(tokens) → SentimentResult. Simple lexicon-based: built-in positive/negative word lists, score = (pos - neg) / total. Return score + label (positive/negative/neutral).
- depends: alpha-models, alpha-tokenizer

### alpha-statistics
- owner: TBD
- status: pending
- file: A:STA
- spec: compute_statistics(doc, tokens) → StatisticsResult. char_count, word_count, sentence_count, avg_word_length, vocabulary_size, lexical_diversity.
- depends: alpha-models, alpha-tokenizer

### alpha-init
- owner: TBD (architect or tech-writer)
- status: pending
- file: A:INI
- spec: Public API exports. Re-export key functions from submodules.
- depends: all above

### alpha-unit-tests
- owner: TBD (QA)
- status: pending
- file: T:U.core
- spec: Unit tests for each core module. ≥3 tests per module.
- depends: all implementations

## Reviews
Format: `file: REF — reviewer: agent-id — verdict: approved|changes_needed — notes: string`

## Test Results
Format: `suite: name — tester: agent-id — result: pass(N)/fail(N) — details: string`

## Design Challenges
Format: `challenger: agent-id — target: REF/decision — challenge: string — resolution: string`

challenger: 664dee0d — target: A:MOD/dataclass-mutability — challenge: All dataclasses are mutable by default. Token is high-volume pipeline data that should never be mutated after creation. FrequencyResult contains mutable dicts, so even `frozen=True` won't protect contents. Proposal: use `@dataclass(frozen=True)` on all models, and use `tuple[tuple[str,int],...]` or `MappingProxyType` for frequency dicts. Alternatively, NamedTuple for Token gives immutability + 40% less memory (no __dict__) at high volume. — resolution: pending

challenger: 664dee0d — target: A:MOD/shadow-builtin — challenge: Contract defines `class FileNotFoundError(TextAnalyzerError)` which shadows Python's built-in `FileNotFoundError`. Any code that catches the built-in will miss ours and vice versa. This is a bug factory. Proposal: rename to `FileNotFoundAnalyzerError` or `SourceNotFoundError`, or have it inherit from BOTH `TextAnalyzerError` and the built-in `FileNotFoundError` so `except FileNotFoundError` catches either. — resolution: pending

challenger: 664dee0d — target: A:TOK/stopword-api — challenge: `remove_stopwords: bool` is a closed API. Users can't add domain stopwords (e.g. "said" for news analysis, "patient" for medical). Proposal: change to `stopwords: set[str] | None = None` where None=use default set, empty set=no removal, custom set=use that. One parameter, strictly more powerful, zero breaking change risk since it replaces a bool. — resolution: pending

challenger: 664dee0d — target: A:FRQ/implicit-stopword-coupling — challenge: `word_frequency()` silently skips tokens where `is_stopword=True`, but this depends on the caller having called `tokenize(doc, remove_stopwords=True)` first. If they just call `tokenize(doc)`, all `is_stopword=False` and frequency counts everything — the exclusion is invisible and confusing. Proposal: either (a) add explicit `exclude_stopwords: bool = True` param to `word_frequency()` so intent is clear at the call site, or (b) always count what's given and let the caller filter. Option (b) is simpler and follows "do one thing well". — resolution: pending

challenger: 664dee0d — target: A:SNT/negation-blindness — challenge: Lexicon sentiment with no negation handling is actively misleading. "This is not good" scores positive (counts "good"), "I don't hate it" scores negative (counts "hate"). For a library API, this should be flagged loudly — either (a) add a docstring WARNING that negation/context is ignored, (b) name the function `analyze_sentiment_lexicon()` so users know it's naive, or (c) detect negation words ("not","no","never","don't") and flip the next token's polarity. Option (c) is ~10 lines of code for massive accuracy gain. — resolution: pending

challenger: 664dee0d — target: A:STA/sentence-counting — challenge: Counting `. ! ?` characters for sentence_count is broken for real text. "Dr. Smith earned $3.50 at 2 p.m." counts as 4 sentences. "U.S.A. is great!" counts as 4. Abbreviations, decimals, ellipses ("...") all break this. Proposal: at minimum, skip `.` preceded by a single uppercase letter (abbreviation heuristic). Better: use regex `r'[.!?]+(?=\s+[A-Z]|$)'` which requires sentence-end punctuation to be followed by whitespace+capital or end-of-string. — resolution: pending

challenger: 664dee0d — target: A:PAR/no-size-guard — challenge: `parse_file()` has no file size limit. A user passing a 10GB log file will OOM the process silently. Proposal: add `max_size_bytes: int = 10_485_760` (10MB default) parameter. Read file size first, raise a new `FileTooLargeError` if exceeded. Cheap insurance, zero downside. — resolution: pending

challenger: 664dee0d — target: A:FRQ/top-n-edge-cases — challenge: `word_frequency(tokens, top_n=0)` and `top_n=-1` behavior is undefined. Also, empty token list → division by zero in relative_frequency calculation (count/total where total=0). Spec must define: top_n≤0 raises ValueError, empty input returns FrequencyResult with zeros and empty dicts. — resolution: pending

## Documentation
- README section for core library: pending
- API docstrings: pending (each developer owns their file's docstrings)
