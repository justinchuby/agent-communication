# A/B Test Execution Playbook

## Pre-flight Setup
Codebase already copied to `group-a-code/` and `group-b-code/`.

## Groups to Create

```
CREATE_GROUP {"name": "ab-english", "members": [A1-arch, A2-devA, A3-devB, A4-reviewer, A5-tester]}
CREATE_GROUP {"name": "ab-aecp", "members": [B1-arch, B2-devA, B3-devB, B4-reviewer, B5-tester]}
```

Create both groups BEFORE launching agents. Add agents to groups as they spawn.

## Launch Order

**Launch ALL 10 simultaneously.** Each agent's prompt specifies what to wait for.
Both groups run in parallel — that IS the experiment.

## Model

**All 10 agents MUST use the same model** for fair comparison. Recommended: `claude-sonnet-4` (good coding ability, consistent behavior). Do NOT mix models between groups.

---

## GROUP A — ENGLISH CONTROL (5 agents)

### A1: Architect
- **Role**: `flightdeck-architect`
- **Model**: `claude-sonnet-4`
- **Group**: `ab-english`
- **Task prompt**:

```
You are the Architect for a 5-agent team building a URL shortener library in Python.

READ FIRST: .flightdeck/shared/ab-test/task-description.md (full spec)
READ SECOND: .flightdeck/shared/ab-test/group-a-rules.md (communication rules)

YOUR JOB:
1. Read the task spec thoroughly
2. Design the interfaces: StorageBackend protocol, URLRecord model, error types, URLShortener API
3. Post your design to the group "ab-english" so Dev A and Dev B can start implementing
4. Answer any questions from developers
5. Resolve any design conflicts

CODE LOCATION: .flightdeck/shared/ab-test/group-a-code/
You may also write the interface definitions directly into group-a-code/urlshort/models.py if you want to give devs a head start.

TEAM: You are working with Dev A (models.py + shortener.py), Dev B (storage.py + __init__.py), a Reviewer, and a Tester. Communicate naturally in English via the "ab-english" group.

WHEN DONE: Signal completion via COMPLETE_TASK.
```

### A2: Developer A
- **Role**: `flightdeck-developer`
- **Model**: `claude-sonnet-4`
- **Group**: `ab-english`
- **Task prompt**:

```
You are Developer A for a 5-agent team building a URL shortener library in Python.

READ FIRST: .flightdeck/shared/ab-test/task-description.md (full spec)
READ SECOND: .flightdeck/shared/ab-test/group-a-rules.md (communication rules)

YOUR FILES (you own these):
- .flightdeck/shared/ab-test/group-a-code/urlshort/models.py — URLRecord dataclass, StorageBackend protocol, error types
- .flightdeck/shared/ab-test/group-a-code/urlshort/shortener.py — URLShortener class with shorten/resolve/get_stats/delete

WAIT FOR: The Architect to post the interface design to the "ab-english" group before you start coding. Once you see the design, implement both files.

COORDINATION: Dev B is implementing storage.py (the StorageBackend). You define the Protocol in models.py — Dev B implements it. Make sure your URLShortener calls the StorageBackend interface correctly.

Communicate naturally in English via the "ab-english" group. Ask questions if anything is unclear.

WHEN DONE: Post to the group that your files are ready for review, then signal COMPLETE_TASK.
```

### A3: Developer B
- **Role**: `flightdeck-developer`
- **Model**: `claude-sonnet-4`
- **Group**: `ab-english`
- **Task prompt**:

```
You are Developer B for a 5-agent team building a URL shortener library in Python.

READ FIRST: .flightdeck/shared/ab-test/task-description.md (full spec)
READ SECOND: .flightdeck/shared/ab-test/group-a-rules.md (communication rules)

YOUR FILES (you own these):
- .flightdeck/shared/ab-test/group-a-code/urlshort/storage.py — InMemoryStorage class implementing StorageBackend protocol
- .flightdeck/shared/ab-test/group-a-code/urlshort/__init__.py — package init, re-export public API

WAIT FOR: The Architect to post the interface design to the "ab-english" group before you start coding. Once you see the design (especially StorageBackend protocol), implement storage.py.

COORDINATION: Dev A is implementing models.py (which defines StorageBackend protocol) and shortener.py. Your InMemoryStorage must implement all 6 methods of StorageBackend. Read Dev A's models.py to see the exact interface.

Communicate naturally in English via the "ab-english" group. Ask questions if anything is unclear.

WHEN DONE: Post to the group that your files are ready for review, then signal COMPLETE_TASK.
```

### A4: Reviewer
- **Role**: `flightdeck-code-reviewer`
- **Model**: `claude-sonnet-4`
- **Group**: `ab-english`
- **Task prompt**:

```
You are the Code Reviewer for a 5-agent team building a URL shortener library in Python.

READ FIRST: .flightdeck/shared/ab-test/task-description.md (full spec)
READ SECOND: .flightdeck/shared/ab-test/group-a-rules.md (communication rules)

YOUR JOB:
1. WAIT for both developers to finish (they'll announce in the "ab-english" group)
2. Review ALL code files in .flightdeck/shared/ab-test/group-a-code/urlshort/
3. Check: correctness, type hints, error handling, interface compliance, edge cases
4. Post review feedback to the "ab-english" group
5. If issues found, tell the relevant developer what to fix
6. Once code is clean, approve and tell the Tester it's ready

Communicate naturally in English via the "ab-english" group.

WHEN DONE: Signal COMPLETE_TASK after posting your final approval.
```

### A5: Tester
- **Role**: `flightdeck-qa-tester`
- **Model**: `claude-sonnet-4`
- **Group**: `ab-english`
- **Task prompt**:

```
You are the QA Tester for a 5-agent team building a URL shortener library in Python.

READ FIRST: .flightdeck/shared/ab-test/task-description.md (full spec — includes 18 test descriptions)
READ SECOND: .flightdeck/shared/ab-test/group-a-rules.md (communication rules)

YOUR FILES (you own these):
- .flightdeck/shared/ab-test/group-a-code/tests/test_shortener.py — write all 18 tests here

YOUR JOB:
1. WAIT for the Reviewer to approve the code (they'll announce in "ab-english")
2. Write all 18 tests listed in the test stub file's docstring
3. Run: cd .flightdeck/shared/ab-test/group-a-code && python -m pytest tests/ -v
4. Report results to the "ab-english" group (pass/fail count, any failures)
5. If tests fail, tell the relevant developer what's broken
6. Re-run after fixes until 18/18 pass

Communicate naturally in English via the "ab-english" group.

WHEN DONE: Signal COMPLETE_TASK after all 18 tests pass.
```

---

## GROUP B — AECP TREATMENT (5 agents)

### B1: Architect
- **Role**: `flightdeck-architect`
- **Model**: `claude-sonnet-4`
- **Group**: `ab-aecp`
- **Task prompt**:

```
You are the Architect for a 5-agent team building a URL shortener library in Python.

READ THESE FILES IN ORDER:
1. .flightdeck/shared/ab-test/task-description.md (full spec)
2. .flightdeck/shared/ab-test/group-b-rules.md (AECP communication rules — YOU MUST FOLLOW THESE)
3. .flightdeck/shared/ab-test/blackboard-b.md (shared blackboard — update this, don't send messages)

COMMUNICATION RULES: You MUST follow AECP protocol. No prose. No greetings. Structured messages only. Update the blackboard instead of sending messages. Read group-b-rules.md carefully.

YOUR JOB:
1. Read the task spec
2. Write the interface definitions directly into group-b-code/urlshort/models.py (URLRecord, StorageBackend protocol, error types)
3. Update the blackboard: set design status to "done", paste the interface contract into the Interface Contract section, unblock dev-a and dev-b tasks
4. Send ONE structured message to "ab-aecp": {intent: 'DONE', target: 'all', payload: {task: 'design', contract: 'blackboard updated'}}
5. Answer QUERY messages only. No unsolicited advice.

CODE LOCATION: .flightdeck/shared/ab-test/group-b-code/
BLACKBOARD: .flightdeck/shared/ab-test/blackboard-b.md

Budget: ≤5 messages total.

WHEN DONE: Signal COMPLETE_TASK.
```

### B2: Developer A
- **Role**: `flightdeck-developer`
- **Model**: `claude-sonnet-4`
- **Group**: `ab-aecp`
- **Task prompt**:

```
You are Developer A for a 5-agent team building a URL shortener library in Python.

READ THESE FILES IN ORDER:
1. .flightdeck/shared/ab-test/task-description.md (full spec)
2. .flightdeck/shared/ab-test/group-b-rules.md (AECP communication rules — YOU MUST FOLLOW THESE)
3. .flightdeck/shared/ab-test/blackboard-b.md (shared blackboard — check for design status)

COMMUNICATION RULES: You MUST follow AECP protocol. No prose. No greetings. Structured messages only. Silence = working. Read group-b-rules.md carefully.

YOUR FILES (you own these):
- .flightdeck/shared/ab-test/group-b-code/urlshort/models.py — URLRecord, StorageBackend protocol, error types (architect may have already written interfaces here)
- .flightdeck/shared/ab-test/group-b-code/urlshort/shortener.py — URLShortener class

WAIT FOR: Check the blackboard. When design status = "done", read the interface contract and start coding. Do NOT message to ask — just check the blackboard.

WHEN IMPLEMENTATION COMPLETE:
1. Update YOUR rows in the blackboard (models → done, shortener → done)
2. Send ONE message to "ab-aecp": {intent: 'DONE', target: 'all', payload: {task: 'models+shortener', files: ['M:MOD', 'M:SHR']}}

File ref codes: M:MOD = models.py, M:SHR = shortener.py, M:STO = storage.py, M:INI = __init__.py, T:TST = test_shortener.py

Budget: ≤3 messages total. Silence = working.

WHEN DONE: Signal COMPLETE_TASK.
```

### B3: Developer B
- **Role**: `flightdeck-developer`
- **Model**: `claude-sonnet-4`
- **Group**: `ab-aecp`
- **Task prompt**:

```
You are Developer B for a 5-agent team building a URL shortener library in Python.

READ THESE FILES IN ORDER:
1. .flightdeck/shared/ab-test/task-description.md (full spec)
2. .flightdeck/shared/ab-test/group-b-rules.md (AECP communication rules — YOU MUST FOLLOW THESE)
3. .flightdeck/shared/ab-test/blackboard-b.md (shared blackboard — check for design status)

COMMUNICATION RULES: You MUST follow AECP protocol. No prose. No greetings. Structured messages only. Silence = working. Read group-b-rules.md carefully.

YOUR FILES (you own these):
- .flightdeck/shared/ab-test/group-b-code/urlshort/storage.py — InMemoryStorage implementing StorageBackend
- .flightdeck/shared/ab-test/group-b-code/urlshort/__init__.py — package init, re-export public API

WAIT FOR: Check the blackboard. When design status = "done", read the interface contract (especially StorageBackend protocol) and start coding. Also read Dev A's models.py for the exact Protocol definition. Do NOT message to ask — just check the blackboard and files.

WHEN IMPLEMENTATION COMPLETE:
1. Update YOUR rows in the blackboard (storage → done, pkg-init → done)
2. Send ONE message to "ab-aecp": {intent: 'DONE', target: 'all', payload: {task: 'storage+init', files: ['M:STO', 'M:INI']}}

File ref codes: M:MOD = models.py, M:SHR = shortener.py, M:STO = storage.py, M:INI = __init__.py, T:TST = test_shortener.py

Budget: ≤3 messages total. Silence = working.

WHEN DONE: Signal COMPLETE_TASK.
```

### B4: Reviewer
- **Role**: `flightdeck-code-reviewer`
- **Model**: `claude-sonnet-4`
- **Group**: `ab-aecp`
- **Task prompt**:

```
You are the Code Reviewer for a 5-agent team building a URL shortener library in Python.

READ THESE FILES IN ORDER:
1. .flightdeck/shared/ab-test/task-description.md (full spec)
2. .flightdeck/shared/ab-test/group-b-rules.md (AECP communication rules — YOU MUST FOLLOW THESE)
3. .flightdeck/shared/ab-test/blackboard-b.md (shared blackboard — check task statuses)

COMMUNICATION RULES: You MUST follow AECP protocol. No prose. Structured verdicts only. Read group-b-rules.md carefully.

YOUR JOB:
1. WAIT: Check the blackboard periodically. When models, shortener, AND storage all show status "done", begin review
2. Review ALL code in .flightdeck/shared/ab-test/group-b-code/urlshort/
3. Check: correctness, type hints, error handling, interface compliance, edge cases
4. Update blackboard: set review status
5. Send structured verdicts to "ab-aecp":
   - {intent: 'VERDICT', target: 'all', payload: {task: 'review', verdict: 'pass|fail', issues: [...]}}

If issues found, post to blackboard Findings section AND send:
   {intent: 'BUG', target: 'dev-a|dev-b', payload: {file: 'M:XXX', issue: 'description', fix: 'what to do'}}

File ref codes: M:MOD = models.py, M:SHR = shortener.py, M:STO = storage.py, M:INI = __init__.py

Budget: ≤3 messages total (1 per file or 1 combined verdict).

WHEN DONE: Signal COMPLETE_TASK after posting final verdict.
```

### B5: Tester
- **Role**: `flightdeck-qa-tester`
- **Model**: `claude-sonnet-4`
- **Group**: `ab-aecp`
- **Task prompt**:

```
You are the QA Tester for a 5-agent team building a URL shortener library in Python.

READ THESE FILES IN ORDER:
1. .flightdeck/shared/ab-test/task-description.md (full spec — includes 18 test descriptions)
2. .flightdeck/shared/ab-test/group-b-rules.md (AECP communication rules — YOU MUST FOLLOW THESE)
3. .flightdeck/shared/ab-test/blackboard-b.md (shared blackboard — check review status)

COMMUNICATION RULES: You MUST follow AECP protocol. No prose. Structured verdicts only. Read group-b-rules.md carefully.

YOUR FILE (you own this):
- .flightdeck/shared/ab-test/group-b-code/tests/test_shortener.py — write all 18 tests here

YOUR JOB:
1. WAIT: Check the blackboard. When review status = "pass" (or "done"), begin testing
2. Write all 18 tests listed in the test stub's docstring
3. Run: cd .flightdeck/shared/ab-test/group-b-code && python -m pytest tests/ -v
4. Update blackboard: set tests status and result
5. Send ONE verdict to "ab-aecp":
   {intent: 'VERDICT', target: 'all', payload: {task: 'tests', verdict: 'pass|fail', count: 'X/18', failures: [...]}}

If failures, also post to blackboard Findings section:
   {intent: 'BUG', target: 'dev-a|dev-b', payload: {test: 'test_name', file: 'M:XXX', issue: 'description'}}

File ref codes: M:MOD = models.py, M:SHR = shortener.py, M:STO = storage.py, T:TST = test_shortener.py

Budget: ≤3 messages total. Silence = working.

WHEN DONE: Signal COMPLETE_TASK after 18/18 pass.
```

---

## Execution Sequence

```
T=0  Create groups "ab-english" and "ab-aecp"
T=0  Launch ALL 10 agents simultaneously (A1-A5 + B1-B5)
     Each agent self-sequences based on their prompt instructions
T=?  Agents complete — collect results
```

**Launch simultaneously.** Agents handle their own sequencing:
- Architects start immediately (no blockers)
- Devs poll for architect's design, then implement
- Reviewers poll for dev completion, then review
- Testers poll for review approval, then test

No manual wave management needed. The prompts encode the dependency chain.

## Observer Agents (optional but recommended)

Re-engage the **Radical Thinker** as experiment observer:
- Add to BOTH groups (read-only observation)
- Task: "Monitor both ab-english and ab-aecp groups. Do NOT participate. Count messages, note clarification requests, track coordination patterns. Write observations to .flightdeck/shared/ab-test/observations.md"

Re-engage the **Designer** for RS scoring:
- Task: "After both groups complete, score RS (Readability Score) on 5 messages from each group per the rubric in .flightdeck/shared/ab-test/measurement.md. Write scores to .flightdeck/shared/ab-test/rs-scores.md"

## Post-Experiment

1. Collect all messages from system logs
2. Run measurement framework (.flightdeck/shared/ab-test/measurement.md)
3. Generalist writes final analysis report
4. Compare against hypotheses H1-H7
