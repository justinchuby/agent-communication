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
- owner: f2dc8aa6
- status: done
- file: A:MOD
- spec: Define TextDocument, Token, FrequencyResult, SentimentResult, StatisticsResult dataclasses
- depends: none

### alpha-parser
- owner: 9ff61817
- status: done
- file: A:PAR
- spec: parse_file(path) → TextDocument, parse_string(text) → TextDocument. Handle UTF-8, strip control chars.
- depends: alpha-models

### alpha-tokenizer
- owner: 5d691eb9
- status: done
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
- owner: d6ee7d38
- status: done
- file: A:SNT
- spec: analyze_sentiment(tokens) → SentimentResult. Simple lexicon-based: built-in positive/negative word lists, score = (pos - neg) / total. Return score + label (positive/negative/neutral).
- depends: alpha-models, alpha-tokenizer

### alpha-statistics
- owner: b748aeb6
- status: done
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
- owner: 9174b332
- status: done
- file: T:U.core
- spec: Unit tests for each core module. ≥3 tests per module.
- depends: all implementations

## Reviews
Format: `file: REF — reviewer: agent-id — verdict: approved|changes_needed — notes: string`

### Critical Review — reviewer: 500e90cb — verdict: changes_needed

**Scope**: architecture coherence, security, performance, error propagation, type safety across all 6 core files.

**CRITICAL — parser.py: No path traversal protection (security)**
`parse_file(path)` accepts arbitrary paths with zero validation. No `os.path.realpath()`, no directory sandboxing, no symlink check. If exposed to user input (CLI, web API), attacker reads `/etc/shadow`, `../../secrets.env`, etc. Fix: document the risk prominently OR add optional `allowed_dir` param with `os.path.commonpath` check.

**CRITICAL — parser.py: Unbounded file read (performance/DoS)**
Line 78: `fh.read()` loads entire file into memory. A 2GB file OOMs the process. `_strip_control_characters` then iterates char-by-char creating a second copy. Fix: add `MAX_FILE_SIZE` constant (e.g., 50MB), check `os.path.getsize()` before read, raise `ParseError` if exceeded.

**HIGH — parser.py: PermissionError not caught (error contract)**
`open()` can raise `PermissionError`/`IsADirectoryError` — neither is caught or wrapped in `TextAnalyzerError`. Breaks the error hierarchy contract. Beta team code catching `TextAnalyzerError` will miss these. Fix: add `except OSError as exc: raise ParseError(...)` catch.

**HIGH — parser.py: TOCTOU race condition**
Lines 73-77: `os.path.exists()` then `open()` — file can be deleted between check and open, raising builtin `FileNotFoundError` (not the custom one). Fix: remove `os.path.exists()` check, use try/except on `open()` catching `builtins.FileNotFoundError` and re-raising as custom `FileNotFoundError`.

**MEDIUM — models.py: FileNotFoundError shadows builtin**
Line 74: Custom `FileNotFoundError(TextAnalyzerError)` shadows `builtins.FileNotFoundError`. Any downstream `except FileNotFoundError` becomes ambiguous. Contract specifies this, so accepted with caveat: parser.py must handle the builtin carefully (currently broken due to TOCTOU above).

**LOW — frequency.py: Stub docstring not updated**
Lines 1-14 still contain original "Owner: Team Alpha developer" stub text with TODO instructions. Implementation is complete but docstring is stale.

**LOW — statistics.py: Stub docstring not updated**
Same issue — lines 1-16 still contain original stub text.

**GOOD DECISIONS (acknowledged)**
- ✓ Architecture coherence: clean unidirectional pipeline (parse→tokenize→analyze). Single responsibility per module. All modules depend only on models.py — no circular deps.
- ✓ Contract compliance: all 6 function signatures match blackboard-cross.md exactly.
- ✓ frequency.py: stable sort with alphabetical tiebreak prevents nondeterministic output.
- ✓ sentiment.py: clean edge-case handling for empty token lists, correct score clamping.
- ✓ statistics.py: `SENTENCE_ENDINGS` as frozenset — immutable, O(1) lookup.
- ✓ parser.py: delegation from `parse_file` to `parse_string` avoids duplication.
- ✓ tokenizer.py: module-level compiled regex for performance.

**Summary**: 2 CRITICAL (path traversal, unbounded read), 2 HIGH (PermissionError gap, TOCTOU race) — all in parser.py. The remaining 4 modules are architecturally sound. Parser needs a security/resilience pass before this library is safe for production use.

### Readability Review — reviewer: ce5b457b — verdict: approved — scope: all 6 core files

**Overall: CLEAN.** Code is readable, well-structured, and a new developer could understand it quickly. Naming is clear throughout, organization is logical, PEP 8 is followed. API contract match is exact. Approving with suggestions below.

**Praise:**
- models.py: Exemplary — inline field comments (`# -1.0 to 1.0`, `# word → count, sorted desc`) explain constraints concisely. Section separators between models and errors aid scanning.
- parser.py: Best docstrings in the project — NumPy-style with Parameters/Raises. Private `_strip_control_characters` helper is well-named and correctly prefixed.
- sentiment.py: Early return for empty-token edge case is clean. `raw_score` → clamp → label flow reads naturally.
- statistics.py: `SENTENCE_ENDINGS = frozenset(...)` is good — communicates immutability intent.
- tokenizer.py: Public API summary in module docstring is helpful for discoverability.

**Findings (non-blocking):**

1. **STALE MODULE DOCSTRINGS — frequency.py, statistics.py**: Still contain stub text (`Owner: Team Alpha developer`, `Implement:` spec instructions). The other 4 files updated theirs. These read as unfinished work. Replace with descriptive docstrings matching the pattern in sentiment.py/tokenizer.py.

2. **DOCSTRING STYLE INCONSISTENCY**: parser.py uses NumPy-style (Parameters/Raises with `------` underlines). All other files use Google-style (Args/Returns). Pick one — Google-style is the majority, so parser.py is the outlier. Suggest standardizing to Google-style.

3. **VARIABLE NAMING INCONSISTENCY across modules**: `non_stopword` (frequency.py:33) vs `non_stopword_tokens` (sentiment.py:44). The longer name is clearer. Suggest standardizing to `non_stopword_tokens` in both.

4. **SHADOW BUILTIN — no explanatory comment**: models.py defines `FileNotFoundError` shadowing Python's built-in. The original stub noted this was intentional but the comment was dropped. Add `# Intentionally shadows built-in; caught via TextAnalyzerError hierarchy` or similar. (Agrees with @664dee0d's design challenge on this — readability angle: at minimum, document the intent.)

5. **SENTIMENT NEGATION — docstring gap**: `analyze_sentiment()` doesn't warn users that negation is ignored ("not good" → positive). Add a one-line Note/Warning in the docstring: `Note: Lexicon-only; negation and context are not handled.` (Agrees with @664dee0d's challenge — readability angle: set expectations.)

**Summary:** 5 non-blocking suggestions, 0 blocking issues. Code is approved for readability.

### Code Review — reviewer: 11a34f74 — verdict: changes_needed — scope: all 6 core files

**Overall: SOLID.** 5 of 6 files approved. 1 blocking bug in frequency.py (now fixed by @27a458e8). All files match the API contract. Error handling is consistent. Import patterns are uniform (absolute imports throughout).

**Per-file verdicts:**

file: A:MOD — reviewer: 11a34f74 — verdict: approved — notes: All 5 dataclasses and 4 error types match contract exactly. Fields, types, hierarchy correct. Token.is_stopword has no default — forces explicit construction. FileNotFoundError shadows built-in (design decision per contract).

file: A:PAR — reviewer: 11a34f74 — verdict: approved — notes: parse_file and parse_string correct per spec. Good DRY: parse_file delegates to parse_string. _strip_control_characters correctly uses unicodedata Cc check preserving newlines. Minor: TOCTOU race — os.path.exists() then open() means vanishing file raises built-in FileNotFoundError instead of custom one.

file: A:TOK — reviewer: 11a34f74 — verdict: approved — notes: Correct splitting, lowercasing, punctuation stripping, empty filtering, sequential positioning. STOP_WORDS meets minimum (33 words). Compiled regex good for performance. is_stopword marking only when remove_stopwords=True — controls all downstream behavior.

file: A:FRQ — reviewer: 11a34f74 — verdict: changes_needed (fixed) — notes: BUG: negative top_n produced silently wrong results via Python slice semantics (top_n=-1 dropped last entry). Fix committed by @27a458e8: ValueError on negative top_n. Secondary alphabetical sort for determinism is a nice touch. Division-by-zero on empty input correctly handled.

file: A:SNT — reviewer: 11a34f74 — verdict: approved — notes: Clean and correct. Early return for zero-total case. Both lexicons have exactly 30 words matching spec. Clamping with max/min is idiomatic. Threshold logic correct (strict inequalities, boundary → neutral).

file: A:STA — reviewer: 11a34f74 — verdict: approved — notes: All 6 metrics correct per spec. SENTENCE_ENDINGS as frozenset communicates immutability. Empty-token edge cases handled. Naive sentence counting matches spec exactly.

**Blocking issues (1 — resolved):**
1. ~~frequency.py: Negative top_n produces silently incorrect results~~ — FIXED by @27a458e8 (ValueError guard added).

**Non-blocking observations (3):**
1. parser.py: TOCTOU race — os.path.exists() before open(). Low risk, could be eliminated by try/except on open().
2. frequency.py + statistics.py: Module docstrings still contain stub boilerplate.
3. Cross-module: stopword-marking creates implicit coupling between tokenizer and downstream modules.

**Summary:** 1 blocking issue (now fixed). 5 approved + 1 approved-after-fix. All 6 files pass code review.

## Test Results
Format: `suite: name — tester: agent-id — result: pass(N)/fail(N) — details: string`

suite: unit/core — tester: 9174b332 — result: pass(52)/fail(0) — details: test_models(15) test_parser(10) test_tokenizer(8) test_frequency(6) test_sentiment(8) test_statistics(5)

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
- README section for core library: done (owner: a832aad1)
- API docstrings: done — all 7 modules verified against blackboard-cross.md contract
  - models.py: 5 dataclass + 4 error docstrings ✓
  - parser.py: parse_file, parse_string + helpers with params/raises ✓
  - tokenizer.py: tokenize + STOP_WORDS ✓
  - frequency.py: word_frequency ✓ (note: stub "Owner" line remains in module docstring)
  - sentiment.py: analyze_sentiment + lexicon sets ✓
  - statistics.py: compute_statistics ✓ (note: stub "Owner" line remains in module docstring)
  - __init__.py: module docstring + __all__ with 15 symbols ✓
