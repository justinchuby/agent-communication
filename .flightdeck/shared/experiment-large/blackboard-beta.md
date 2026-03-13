# Team Beta Blackboard — CLI + Reports

## Team
- sub-lead: TBD
- architect: TBD
- developers: [TBD × 5]
- reviewers: [TBD × 3]
- qa-testers: [TBD × 2]
- tech-writer: TBD
- radical-thinker: TBD

## API Dependencies
See blackboard-cross.md for Alpha's public API this team consumes.

## Tasks

### beta-cli
- owner: TBD
- status: pending
- file: B:CLI
- spec: argparse CLI entry point. Commands: `analyze <file>`, `analyze --format json|text|html`, `analyze --top-n 10`, `analyze --no-sentiment`. Exit codes: 0=success, 1=file-not-found, 2=parse-error.
- depends: cross-team API contract

### beta-formatter
- owner: TBD
- status: pending
- file: B:FMT
- spec: format_text(results) → str, format_json(results) → str. Text format: human-readable table. JSON: serialized results dict. Handle all result types (frequency, sentiment, statistics).
- depends: cross-team API contract, alpha-models (for result types)

### beta-html-report
- owner: TBD
- status: pending
- file: B:HTM
- spec: generate_html_report(results, output_path) → None. Self-contained HTML with inline CSS. Sections: summary stats, word frequency bar chart (CSS-only), sentiment gauge, top words table.
- depends: cross-team API contract, alpha-models

### beta-reporter
- owner: bdf6a559
- status: done
- file: B:RPT
- spec: Orchestrator: run_analysis(file_path, options) → AnalysisResults. Calls Alpha's API (parse → tokenize → frequency + sentiment + statistics), bundles results. Error handling with typed exceptions.
- depends: cross-team API contract, all alpha modules

### beta-init
- owner: TBD (architect or tech-writer)
- status: pending
- file: B:INI
- spec: Public API exports for CLI package.
- depends: all above

### beta-unit-tests
- owner: TBD (QA)
- status: pending
- file: T:U.cli
- spec: Unit tests for formatter, reporter, html_report. ≥3 tests per module. Mock Alpha's API.
- depends: all implementations

### beta-integration-tests
- owner: TBD (QA)
- status: pending
- file: T:I.pipeline
- spec: End-to-end tests: CLI invocation → output verification. Test all output formats. Test error cases. Use sample text files.
- depends: all alpha + all beta implementations

### beta-sample-data
- owner: 3335e448
- status: done
- file: tests/fixtures/
- spec: Create 3 sample text files: short (1 paragraph), medium (1 page), edge-case (empty, unicode, single word).
- depends: none

## Reviews
Format: `file: REF — reviewer: agent-id — verdict: approved|changes_needed — notes: string`

## Test Results
Format: `suite: name — tester: agent-id — result: pass(N)/fail(N) — details: string`

## Design Challenges
Format: `challenger: agent-id — target: REF/decision — challenge: string — resolution: string`

challenger: 0ac7cdd4 — target: B:RPT/naming — challenge: reporter.py is misnamed. It doesn't report anything — it orchestrates a pipeline (parse→tokenize→analyze). Calling it "reporter" confuses responsibility. A reporter formats/presents; this module sequences computation. — alternative: Rename to `pipeline.py` with `run_pipeline()`. Clearer intent, avoids confusion with formatter/html_report which are the actual reporters. — resolution: pending

challenger: 0ac7cdd4 — target: B:FMT+B:HTM/interface-asymmetry — challenge: formatter.py returns strings (format_text→str, format_json→str) but html_report.py writes directly to file (generate_html_report→None). This forces main.py to special-case HTML with separate I/O logic. Every new format must decide: am I a string-returner or a file-writer? This is a leaky abstraction. — alternative: Unify all formatters behind a single Protocol: `format(results: AnalysisResults) -> str`. ALL formatters return strings. The CLI owns ALL I/O (stdout or --output file). HTML just returns an HTML string. This eliminates the special case in main.py, makes testing trivial (no filesystem mocking for HTML), and makes adding new formats (CSV, Markdown, YAML) zero-change in main.py. — resolution: pending

challenger: 0ac7cdd4 — target: B:FMT+B:HTM+B:CLI/extensibility — challenge: Adding a new output format (e.g. CSV, Markdown) currently requires: (1) new module, (2) new dispatch branch in main.py, (3) update argparse choices. Three files change for one feature. This is the Open-Closed Principle violation. — alternative: Strategy/registry pattern. A dict mapping format names to formatter callables: `FORMATTERS = {"text": format_text, "json": format_json, "html": format_html}`. main.py reads --format, looks up the formatter, calls it. Adding CSV = one new function + one dict entry. argparse choices generated from FORMATTERS.keys(). Single point of change. — resolution: pending

challenger: 0ac7cdd4 — target: B:RPT/pipeline-rigidity — challenge: run_analysis() always computes frequency+statistics and optionally sentiment. But these three analyses are independent post-tokenization. If a user only wants statistics (e.g. word count for a quick check), they still pay for frequency analysis. The only toggle is --no-sentiment. Why not --no-frequency or --statistics-only? — alternative: Make analysis steps opt-in via AnalysisOptions flags: `include_frequency: bool = True`, `include_statistics: bool = True`, `include_sentiment: bool = True`. AnalysisResults fields become Optional. This also opens the door for future analysis types (readability scores, n-grams) without changing the pipeline signature. Minor cost: formatters must handle None fields. Major gain: composability and extensibility. — resolution: pending

challenger: 0ac7cdd4 — target: B:CLI/error-completeness — challenge: Exit codes only cover TextAnalyzerError subtypes (0=ok, 1=file-not-found, 2=parse-error). But what about: HTML file write permission denied (IOError)? Disk full? EmptyDocumentError has no exit code. Unexpected exceptions? The error model is incomplete. — alternative: Add exit code 3=empty-document, 99=unexpected-error. Wrap the entire main() in try/except with a final catch-all that prints "Unexpected error: ..." and returns 99. Also: IOError from HTML write should map to a distinct exit code (4=output-error). — resolution: pending

## Documentation
- README (full project): pending
- CLI usage guide: pending
- Installation instructions: pending
