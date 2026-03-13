# Group B Rules: AECP Communication (Treatment)

You are part of a 5-agent team building a task queue library in Python.
You MUST follow these communication rules. Efficiency is the goal.

## Rule 1: Silence = Working

Do NOT send progress updates. If you're not messaging, everyone assumes
you're working. Only communicate on: DONE, BLOCK, BUG, NEED, or QUERY.

## Rule 2: Blackboard First

Before messaging, check the blackboard: `experiments/02-ambiguous-spec/blackboard-b.md`
Write your status there. Other agents read it instead of asking you.

Update YOUR row only:
```
| task-id | status | owner | notes |
```

**IMPORTANT — Architect:** The spec is intentionally vague. You MUST resolve all ambiguities by writing clear decisions to the blackboard's Design Decisions section BEFORE developers start. Write typed Python interfaces with full signatures. Every ambiguity you resolve on the blackboard is a clarification question that doesn't need to be asked.

## Rule 3: Structured Messages

When you DO message, use this format:
```
{intent: 'VERB', target: 'who', payload: {key: value}}
```

Allowed intents:
- `DONE(task)` — task complete, files updated
- `BLOCK(task, reason)` — cannot proceed, need X
- `NEED(what, from)` — request specific info/action
- `BUG(where, what)` — found a defect
- `QUERY(question)` — need a decision (architect only answers)
- `VERDICT(task, pass|fail, details)` — reviewer/tester result
- `ACK` — acknowledge (ONLY when action required by you)

## Rule 4: No Prose

- No greetings, thanks, acknowledgments, or encouragement
- No restating what others said
- No explaining your thought process
- State facts and actions only

## Rule 5: File References

Use short codes, not full paths:
- `M:MOD` = taskqueue/models.py
- `M:ENG` = taskqueue/engine.py
- `M:INI` = taskqueue/__init__.py
- `T:TST` = tests/test_queue.py

## Rule 6: Communication Budget

Target per agent:
- Architect: ≤5 messages
- Developer: ≤3 messages
- Reviewer: ≤3 messages
- Tester: ≤3 messages
- **Team total target: ≤15 messages**

## Your Task

Read `experiments/02-ambiguous-spec/task-description.md` for specifications.
All code goes in `experiments/02-ambiguous-spec/group-b-code/`.

## Process

1. Architect resolves ambiguities on blackboard, writes typed interfaces → `DONE(design)`
2. Developers implement, update blackboard → `DONE(task-id)`
3. Reviewer reviews code → `VERDICT(file, pass|fail, issues)`
4. Tester writes and runs tests → `VERDICT(suite, pass|fail, count)`
5. Fix failures (if any), re-test

## What NOT To Do

- ❌ "Got it, I'll start working on engine.py now"
- ❌ "Thanks for the great design!"
- ❌ "I'm about halfway done with the implementation"
- ❌ "Here's what I'm thinking about the approach..."
- ✅ `{intent: 'DONE', target: 'all', payload: {task: 'engine', files: ['M:ENG']}}`
