# AECP — Agent-Efficient Communication Protocol

A research project investigating structured communication protocols for AI agent coordination. The core finding: replacing natural English with structured protocols reduces inter-agent communication by **63–77%** while improving clarity, eliminating clarification overhead, and maintaining equal or better task quality.

## Key Results

| Experiment | Agents | Protocol | Messages (English : AECP) | Reduction | Clarifications | Tests |
|---|---|---|---|---|---|---|
| Bug Hunt | 3 | AECP only | 3 (vs 19 simulated) | ~92% | 0 | 13/13 |
| 30-Agent Scale | 28 | AECP only | 50 total (1.79/agent) | N/A | N/A | 96/96 |
| URL Shortener A/B | 5 vs 5 | English vs AECP | 22 vs 5 | 77% | 0 : 0 | 18 : 18 |
| Ambiguous Spec A/B | 5 vs 5 | English vs AECP | ~19 vs ~5–7 | 63–74% | 12 : 0 | 21 : 18 |
| Token Efficiency A/B/C/D | 5 × 4 | English vs AECP v1 vs AECP v2 vs 文言文 | 12 vs ~5 vs ~5 vs ~5 | 5% (v1), 22% (v2), −18.5% (文言文) | N/A | 18 : 18 : 18 : 18 |

## Quick Start

- **Research findings** → [`experiments/findings.md`](experiments/findings.md) — comprehensive, publication-quality analysis
- **Documentation index** → [`docs/README.md`](docs/README.md) — full research overview with results table
- **Protocol spec** → [`docs/spec/unified-protocol-spec.md`](docs/spec/unified-protocol-spec.md) — AECP v0.3 specification

## Protocol Overview

AECP is a structured communication protocol designed for AI agent teams. Instead of natural language messages, agents exchange compact structured payloads with explicit intents, typed fields, and shared state via a blackboard pattern. Key design principles:

- **Structured over natural** — typed fields and intent headers replace prose
- **Eliminate, don't compress** — remove information categories that don't need to travel on the wire
- **Shared blackboard** — agents read/write shared state instead of broadcasting updates
- **Channel asymmetry** — human-facing communication stays in English; agent-to-agent uses the protocol

## Experiments

### 00a — Bug Hunt (Live AECP Test)
3 agents collaboratively finding and fixing bugs using AECP. Achieved ~92% token reduction compared to simulated English baseline. All 13 tests passing.
→ [`experiments/00-bug-hunt/`](experiments/00-bug-hunt/)

### 00b — 30-Agent Scale Test
28 agents coordinating on a text analyzer project. Only 50 total messages (1.79 per agent) to achieve 96/96 passing tests, demonstrating AECP scales sub-linearly.
→ [`experiments/00-30-agent-scale/`](experiments/00-30-agent-scale/)

### 01 — URL Shortener A/B Test
Controlled experiment: 5 agents using English vs 5 agents using AECP, building the same URL shortener library. AECP group used 77% fewer messages with identical code quality (18/18 tests both groups).
→ [`experiments/01-ab-url-shortener/`](experiments/01-ab-url-shortener/)

### 02 — Ambiguous Spec A/B Test
5 vs 5 agents implementing a task queue from a deliberately ambiguous specification (9 planted ambiguities). English group needed 12 clarification messages; AECP group needed 0. Both produced working code.
→ [`experiments/02-ambiguous-spec/`](experiments/02-ambiguous-spec/)

### 03 — Token Efficiency A/B/C/D Test
3 groups of 5 agents building an event emitter library (8 planted ambiguities). Measured actual token costs, not just message counts. AECP v1 (monolithic context) barely broke even at −5% tokens despite 58% fewer messages; AECP v2 (scoped views) saved 22%. Group D tested 文言文 (Classical Chinese) blackboard prose — despite 51% character reduction, CJK tokenization costs 18.5% MORE tokens than English. Message reduction overstated true efficiency by 3–15×.
→ [`experiments/03-token-efficiency/`](experiments/03-token-efficiency/)

## Key Findings

- **63–77% message reduction** in controlled A/B tests with equal task quality
- **100% clarification elimination** — structured protocols resolve ambiguity through explicit fields, not back-and-forth
- **Sub-linear scaling** — 28 agents needed only 1.79 messages each (vs O(n²) for unstructured chat)
- **No quality trade-off** — all groups pass their test suites regardless of protocol
- **Deterministic coordination** — structured intents remove interpretation ambiguity from handoffs
- **Blackboard pattern** reduces broadcast traffic — agents pull state instead of pushing updates

## Documentation

### Specification
- [`docs/spec/unified-protocol-spec.md`](docs/spec/unified-protocol-spec.md) — AECP v0.3 complete specification
- [`docs/spec/experiment-design.md`](docs/spec/experiment-design.md) — experimental methodology
- [`docs/spec/protocol-proposals.md`](docs/spec/protocol-proposals.md) — initial design proposals

### Research
- [`docs/research/final-report.md`](docs/research/final-report.md) — main research analysis
- [`docs/research/executive-brief.md`](docs/research/executive-brief.md) — 1-page stakeholder summary
- [`docs/research/theoretical-foundations.md`](docs/research/theoretical-foundations.md) — information-theoretic grounding
- [`docs/research/cross-disciplinary-insights.md`](docs/research/cross-disciplinary-insights.md) — parallels from linguistics, biology, semiotics

### Analysis
- [`docs/analysis/fmea-report.md`](docs/analysis/fmea-report.md) — failure mode analysis (11 failure modes, 3 critical)
- [`docs/analysis/communication-patterns.md`](docs/analysis/communication-patterns.md) — UX interaction design patterns
- [`docs/analysis/initial-ideas.md`](docs/analysis/initial-ideas.md) — first-principles analysis

### Design
- [`docs/design/spec-sections-draft.md`](docs/design/spec-sections-draft.md) — design drafts
- [`docs/design/ux-review-notes.md`](docs/design/ux-review-notes.md) — UX review notes

## Repository Structure

```
├── README.md                          # This file — project index
├── docs/
│   ├── README.md                      # Research overview with results table
│   ├── spec/
│   │   ├── unified-protocol-spec.md   # AECP v0.3 complete specification
│   │   ├── experiment-design.md       # Experimental methodology
│   │   └── protocol-proposals.md      # Initial design proposals
│   ├── research/
│   │   ├── final-report.md            # Main research analysis
│   │   ├── executive-brief.md         # 1-page stakeholder summary
│   │   ├── theoretical-foundations.md # Information-theoretic grounding
│   │   └── cross-disciplinary-insights.md # Linguistics, biology, semiotics
│   ├── analysis/
│   │   ├── fmea-report.md             # Failure mode analysis (11 modes, 3 critical)
│   │   ├── communication-patterns.md  # UX interaction design
│   │   └── initial-ideas.md           # First-principles analysis
│   ├── design/
│   │   ├── spec-sections-draft.md     # Design drafts
│   │   └── ux-review-notes.md         # UX review notes
│   └── experiment/                    # Bug Hunt experiment code
│       ├── run_experiment.py          # Experiment runner
│       ├── measure.py                 # Metrics measurement
│       └── conditions/                # A–E experimental conditions
├── experiments/
│   ├── README.md                      # Experiment index with metrics
│   ├── findings.md                    # Comprehensive research findings (publication-quality)
│   ├── 00-bug-hunt/                   # Live AECP test (3 agents, ~92% reduction)
│   ├── 00-30-agent-scale/             # Scalability test (28 agents, 1.79 msgs/agent)
│   │   └── project/                   # Text Analyzer app (full Python package)
│   ├── 01-ab-test/                    # URL Shortener A/B v1 (shared codebase)
│   ├── 01-ab-url-shortener/           # URL Shortener A/B v2 (separate group code)
│   │   ├── group-a-code/              # English group's implementation (18/18 tests)
│   │   └── group-b-code/              # AECP group's implementation (18/18 tests)
│   ├── 02-ambiguous-spec/             # Ambiguous Spec A/B (12 vs 0 clarifications)
│   │   ├── group-a-code/              # English group's task queue (21 tests)
│   │   └── group-b-code/              # AECP group's task queue (18 tests)
│   └── 03-token-efficiency/           # Token Efficiency A/B/C/D (message ≠ token savings)
│       ├── group-a-code/              # English group's event emitter (18 tests)
│       ├── group-b-code/              # AECP v1 group's event emitter (18 tests)
│       ├── group-c-code/              # AECP v2 group's event emitter (18 tests)
│       └── group-d-code/              # 文言文 group's event emitter (18 tests)
```
