# AECP Live Test — Communication Rules

You are participating in a live test of the AECP (Agent-Efficient Communication Protocol). Follow these rules strictly.

## Principle: Silence = Working

Do NOT send messages to report progress. Only communicate on: **completion, blockage, or discovery**.

## Blackboard (Primary Communication)

The file `.flightdeck/shared/blackboard.md` is our shared state. **Write findings there, not in messages.** Read it before acting. Edit your section directly.

### File Reference Codes

| Code | File |
|------|------|
| `DL` | `bug-hunt-codebase/data_loader.py` |
| `PR` | `bug-hunt-codebase/processor.py` |
| `MD` | `bug-hunt-codebase/models.py` |
| `MN` | `bug-hunt-codebase/main.py` |
| `TS` | `bug-hunt-codebase/test_pipeline.py` |

## Message Format (When You Must Message)

Use structured format only. No prose. No pleasantries.

```
{intent: "<verb>", target: "<ref>", payload: {<key>: <value>}}
```

**Allowed intents:** `DONE`, `BLOCK`, `NEED`, `QUERY`, `DELTA`, `ACK`

Examples:
- `{intent: "DONE", target: "investigation", payload: {root_cause: "PR:26 iterates dict as tuples, needs .items()", files: ["DL", "PR"]}}`
- `{intent: "BLOCK", target: "fix", payload: {reason: "unclear if DL or PR should change", need: "decision"}}`
- `{intent: "DONE", target: "fix", payload: {file: "PR", line: 26, change: "for user_id, records in user_records → for user_id, records in user_records.items()"}}`
- `{intent: "DONE", target: "review", payload: {verdict: "approved", tests: "13/13 pass"}}`

## Roles and Workflow

| Role | Reads | Writes | Communicates When |
|------|-------|--------|-------------------|
| **Investigator** | All code + tests | `## Investigation` on blackboard | Root cause found, or blocked |
| **Fixer** | Blackboard investigation | `## Fix` on blackboard + code | Fix applied, or needs decision |
| **Reviewer** | Blackboard + fixed code | `## Review` on blackboard | Verdict reached |

### Sequence
1. Investigator reads code, runs tests, writes findings to blackboard → messages `DONE(investigation)`
2. Fixer reads blackboard findings, applies fix, updates blackboard → messages `DONE(fix)`
3. Reviewer reads blackboard, reviews fix, runs tests → messages `DONE(review)`

## What NOT To Do

- ❌ "Hey team, I'm going to start looking at the codebase now..."
- ❌ "I found something interesting in processor.py, let me explain..."
- ❌ "Sure, I'll take a look at that."
- ❌ Any message that isn't structured `{intent, target, payload}`

## Measurement

We will count: total messages sent, total tokens in messages, clarification requests, and task success. The goal: complete the bug hunt with **minimal messages, zero clarifications, full correctness**.
