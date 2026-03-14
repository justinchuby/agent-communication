# Group D Rules — AECP v1 · 文言文 (Classical Chinese Blackboard)

## Protocol
- Shared blackboard: experiments/03-token-efficiency/blackboard-d.md
- Architect populates ALL design decisions on the blackboard **in 文言文 (Classical Chinese)**
- Protocol structure identical to Group B (same sections, status tracking, interface contract)
- Prose values, design decisions, and findings are expressed in Classical Chinese
- Interface contract (```python blocks) stays in Python — code is code
- All agents read the FULL blackboard when checking status
- Message budget: ≤5 per agent
- 默則工也 (silence = working)

## Structured Messages (文言文)
| Signal | Meaning |
|--------|---------|
| 畢(設計) | DONE(design) — architect finished design decisions |
| 畢(型與初) | DONE(types+init) — Dev A finished types.py + __init__.py |
| 畢(發射器) | DONE(emitter) — Dev B finished emitter.py |
| 判(通) | VERDICT(pass) — reviewer/tester: all good |
| 判(試，通) | VERDICT(tests, pass) — tester: tests passing |
| 誤(id，重) | BUG(id, severity) — reviewer found a bug |

## Status Values (文言文)
| 文言文 | English equivalent |
|--------|--------------------|
| 未始 | not_started |
| 阻(設計) | blocked(design) |
| 進行中 | in_progress |
| 畢 | done |
| 畢(通) | done(pass) |

## Your Team
- Architect: Fills blackboard design decisions + interface contract (decisions in 文言文)
- Dev A: Implements types.py + __init__.py per blackboard spec
- Dev B: Implements emitter.py per blackboard spec
- Reviewer: Reviews code, posts findings to blackboard (findings in 文言文)
- Tester: Writes and runs 15–20 tests

## Code Directory
experiments/03-token-efficiency/group-d-code/

## Workflow
1. Architect reads task spec → fills blackboard (文言文 decisions) → sends 畢(設計)
2. Dev A reads full blackboard → implements types.py + __init__.py → updates blackboard → sends 畢(型與初)
3. Dev B reads full blackboard → implements emitter.py → updates blackboard → sends 畢(發射器)
4. Reviewer reads full blackboard + all code → posts findings (文言文) → sends 判(通) or 誤(id，重)
5. Tester reads full blackboard + all code → writes tests → runs them → sends 判(試，通)

## Why 文言文?
This group tests hypothesis H10 from wenyanwen-analysis.md: whether 文言文's
extreme character-level density translates to token savings or whether the
tokenizer penalty makes it more expensive than English. The analysis predicts
文言文 will cost MORE total tokens due to CJK UTF-8 overhead, but we run the
experiment to gather empirical data.
