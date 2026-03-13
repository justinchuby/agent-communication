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

## Documentation
- README section for core library: pending
- API docstrings: pending (each developer owns their file's docstrings)
