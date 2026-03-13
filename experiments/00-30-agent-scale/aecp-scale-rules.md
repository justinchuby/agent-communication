# AECP Scale Rules — 30-Agent Experiment

## Core Principle
Silence = working. Blackboard = source of truth. Messages = exceptions only.

## Teams
- **Alpha** (library): blackboard-alpha.md — builds `textanalyzer.core`
- **Beta** (CLI/reports): blackboard-beta.md — builds `textanalyzer.cli` + tests
- **Cross-team**: blackboard-cross.md — API contracts between Alpha and Beta

## File Reference Codes

### Team Alpha (core library)
| Code | File |
|------|------|
| `A:MOD` | `core/models.py` |
| `A:PAR` | `core/parser.py` |
| `A:TOK` | `core/tokenizer.py` |
| `A:FRQ` | `core/frequency.py` |
| `A:SNT` | `core/sentiment.py` |
| `A:STA` | `core/statistics.py` |
| `A:INI` | `core/__init__.py` |

### Team Beta (CLI + reports)
| Code | File |
|------|------|
| `B:CLI` | `cli/main.py` |
| `B:FMT` | `cli/formatter.py` |
| `B:RPT` | `cli/reporter.py` |
| `B:HTM` | `cli/html_report.py` |
| `B:INI` | `cli/__init__.py` |

### Shared
| Code | File |
|------|------|
| `S:SET` | `setup.py` |
| `S:RDM` | `README.md` |
| `S:PKG` | `__init__.py` |
| `T:U.*` | `tests/unit/test_*.py` |
| `T:I.*` | `tests/integration/test_*.py` |

## Message Format
```
{intent: "<VERB>", target: "<ref>", payload: {<key>: <value>}}
```
Intents: `DONE`, `BLOCK`, `NEED`, `QUERY`, `DELTA`, `ACK`, `VERDICT`, `RESULT`

## Role-Specific Rules

| Role | Writes to Blackboard | Messages When |
|------|---------------------|---------------|
| **Sub-Lead** | Task assignments, decisions | Resolving blockers, cross-team coordination |
| **Architect** | API design in `## API Contracts` | Design done, or needs decision |
| **Developer** | Own task status in `## Tasks` | `DONE(file)` or `BLOCK(reason)` |
| **Reviewer** | Verdicts in `## Reviews` | `VERDICT(file, approved/changes_needed)` |
| **QA Tester** | Results in `## Test Results` | `RESULT(suite, pass/fail, details)` |
| **Tech Writer** | Doc status in `## Documentation` | `DONE(docs)` |
| **Radical Thinker** | Challenges in `## Design Challenges` | Only when challenging a decision |

## Cross-Team Protocol

1. Alpha architect writes API contracts to `blackboard-cross.md`
2. Beta architect reads contracts and designs CLI around them
3. Contract changes require BOTH architects to sign off
4. Cross-team messages go through sub-leads OR directly with `{intent: "NEED", target: "cross-team", ...}`

## Blackboard Update Format
```markdown
### task-id
- owner: agent-id
- status: pending|in-progress|done|blocked
- file: REF_CODE
- notes: brief string
```

## Communication Budget Target
- Per developer: ≤3 messages for entire task (DONE + maybe 1-2 BLOCK/NEED)
- Per reviewer: ≤2 messages per file reviewed (VERDICT)
- Per tester: ≤2 messages per test suite (RESULT)
- Sub-leads: ≤10 messages total (assignments + blocker resolution)
- **Target for 30-agent project: <80 total messages**

## What NOT To Do
- ❌ English prose in messages
- ❌ Progress updates ("I'm working on...")
- ❌ Acknowledgments ("Got it", "Sure")
- ❌ Re-describing what's on the blackboard
- ❌ Cross-team messages without going through blackboard-cross.md first
