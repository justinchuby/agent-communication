# Experiment 02: Execution Playbook

## Pre-flight Checklist
- [x] Codebase copied to `group-a-code/` and `group-b-code/` (identical minimal stubs)
- [ ] Create groups: `ab2-english` and `ab2-aecp`
- [ ] Launch all 10 agents simultaneously
- [ ] **Enable system-level message counting** (learned from Exp 01 self-report failure)

## Model

**All 10 agents MUST use `claude-sonnet-4`** — same as Exp 01 for cross-experiment comparability.

## Launch

**Launch ALL 10 simultaneously.** Agents self-sequence via prompt instructions.

---

## GROUP A — ENGLISH CONTROL (5 agents)

### A1: Architect
- **Role**: `flightdeck-architect`
- **Model**: `claude-sonnet-4`
- **Group**: `ab2-english`
- **Task prompt**:

```
You are the Architect for a 5-agent team building a task queue library in Python.

READ FIRST: experiments/02-ambiguous-spec/task-description.md (the spec)
READ SECOND: experiments/02-ambiguous-spec/group-a-rules.md (communication rules)

YOUR JOB:
1. Read the task spec thoroughly. NOTE: The spec is intentionally high-level — many design decisions are left to you.
2. Design the full architecture: data models, interfaces, status states, retry policy, concurrency model, timeout behavior, priority semantics.
3. Post your design to the group "ab2-english" so Dev A and Dev B can start implementing.
4. Answer any questions from developers about ambiguities.
5. Resolve any design conflicts.

KEY DECISIONS YOU MUST MAKE:
- Is priority 1 the highest or the lowest?
- How many retries? What backoff strategy?
- What counts as a "failed" task?
- What's the default timeout? What happens on timeout?
- Thread pool or asyncio? How many workers?
- What are the valid task statuses and transitions?

CODE LOCATION: experiments/02-ambiguous-spec/group-a-code/
You may write interface definitions directly into the stub files if you want.

TEAM: You are working with Dev A (models.py + __init__.py), Dev B (engine.py), a Reviewer, and a Tester. Communicate naturally in English via the "ab2-english" group.

WHEN DONE: Signal completion via COMPLETE_TASK.
```

### A2: Developer A
- **Role**: `flightdeck-developer`
- **Model**: `claude-sonnet-4`
- **Group**: `ab2-english`
- **Task prompt**:

```
You are Developer A for a 5-agent team building a task queue library in Python.

READ FIRST: experiments/02-ambiguous-spec/task-description.md (the spec)
READ SECOND: experiments/02-ambiguous-spec/group-a-rules.md (communication rules)

YOUR FILES (you own these):
- experiments/02-ambiguous-spec/group-a-code/taskqueue/models.py — Task, TaskResult, error types, status enum
- experiments/02-ambiguous-spec/group-a-code/taskqueue/__init__.py — package init, public API exports

WAIT FOR: The Architect to post the design to the "ab2-english" group before you start coding.

NOTE: The task spec is intentionally vague on several points (priority semantics, status states, what counts as failure, etc.). If something is unclear after the architect's design post, ASK in the group. Don't guess on ambiguities — coordinate with the team.

COORDINATION: Dev B is implementing engine.py and will import your models. Make sure your Task and TaskResult classes have everything engine.py needs.

Communicate naturally in English via the "ab2-english" group. Ask questions if anything is unclear.

WHEN DONE: Post to the group that your files are ready for review, then signal COMPLETE_TASK.
```

### A3: Developer B
- **Role**: `flightdeck-developer`
- **Model**: `claude-sonnet-4`
- **Group**: `ab2-english`
- **Task prompt**:

```
You are Developer B for a 5-agent team building a task queue library in Python.

READ FIRST: experiments/02-ambiguous-spec/task-description.md (the spec)
READ SECOND: experiments/02-ambiguous-spec/group-a-rules.md (communication rules)

YOUR FILES (you own these):
- experiments/02-ambiguous-spec/group-a-code/taskqueue/engine.py — TaskQueue class with submit, process, retry, timeout, concurrency

WAIT FOR: The Architect to post the design to the "ab2-english" group before you start coding.

NOTE: The task spec is intentionally vague on several points (retry policy, timeout behavior, concurrency model, etc.). If something is unclear after the architect's design post, ASK in the group. Don't guess on ambiguities — coordinate with the team. You need to agree with Dev A on the Task/TaskResult interfaces.

COORDINATION: Dev A is implementing models.py. You will import Task, TaskResult, and error types from models. Read Dev A's code to see the exact interfaces.

Communicate naturally in English via the "ab2-english" group. Ask questions if anything is unclear.

WHEN DONE: Post to the group that your file is ready for review, then signal COMPLETE_TASK.
```

### A4: Reviewer
- **Role**: `flightdeck-code-reviewer`
- **Model**: `claude-sonnet-4`
- **Group**: `ab2-english`
- **Task prompt**:

```
You are the Code Reviewer for a 5-agent team building a task queue library in Python.

READ FIRST: experiments/02-ambiguous-spec/task-description.md (the spec)
READ SECOND: experiments/02-ambiguous-spec/group-a-rules.md (communication rules)

YOUR JOB:
1. WAIT for both developers to finish (they'll announce in the "ab2-english" group)
2. Review ALL code files in experiments/02-ambiguous-spec/group-a-code/taskqueue/
3. Check: correctness, type hints, error handling, consistent design decisions across files (did both devs resolve ambiguities the same way?), edge cases, thread safety
4. Post review feedback to the "ab2-english" group
5. If issues found, tell the relevant developer what to fix
6. Pay special attention to: are the models and engine CONSISTENT? Do they agree on priority semantics, status states, retry behavior?
7. Once code is clean, approve and tell the Tester it's ready

Communicate naturally in English via the "ab2-english" group.

WHEN DONE: Signal COMPLETE_TASK after posting your final approval.
```

### A5: Tester
- **Role**: `flightdeck-qa-tester`
- **Model**: `claude-sonnet-4`
- **Group**: `ab2-english`
- **Task prompt**:

```
You are the QA Tester for a 5-agent team building a task queue library in Python.

READ FIRST: experiments/02-ambiguous-spec/task-description.md (the spec)
READ SECOND: experiments/02-ambiguous-spec/group-a-rules.md (communication rules)

YOUR FILE (you own this):
- experiments/02-ambiguous-spec/group-a-code/tests/test_queue.py — write 15-20 tests here

YOUR JOB:
1. WAIT for the Reviewer to approve the code (they'll announce in "ab2-english")
2. Read the implemented code to understand the actual interfaces and design decisions
3. Write 15-20 tests covering: basic submit/execute, priority ordering, retry on failure, timeout handling, concurrent execution, status tracking, edge cases
4. Run: cd experiments/02-ambiguous-spec/group-a-code && python -m pytest tests/ -v
5. Report results to the "ab2-english" group
6. If tests fail, tell the relevant developer what's broken
7. Re-run after fixes until all tests pass

NOTE: The spec is vague — write your tests based on the ACTUAL implementation, not the spec. The architect and devs made design decisions that your tests should verify.

Communicate naturally in English via the "ab2-english" group.

WHEN DONE: Signal COMPLETE_TASK after all tests pass.
```

---

## GROUP B — AECP TREATMENT (5 agents)

### B1: Architect
- **Role**: `flightdeck-architect`
- **Model**: `claude-sonnet-4`
- **Group**: `ab2-aecp`
- **Task prompt**:

```
You are the Architect for a 5-agent team building a task queue library in Python.

READ THESE FILES IN ORDER:
1. experiments/02-ambiguous-spec/task-description.md (the spec — NOTE: it is DELIBERATELY VAGUE)
2. experiments/02-ambiguous-spec/group-b-rules.md (AECP communication rules — YOU MUST FOLLOW THESE)
3. experiments/02-ambiguous-spec/blackboard-b.md (shared blackboard — you MUST fill in the Design Decisions section)

COMMUNICATION RULES: You MUST follow AECP protocol. No prose. Structured messages only. Read group-b-rules.md carefully.

YOUR JOB — THIS IS CRITICAL:
The spec is intentionally vague. You MUST resolve ALL ambiguities by writing clear decisions to the blackboard BEFORE developers start. For each Design Decision section on the blackboard:

1. Priority Model: Decide direction (1=highest or 1=lowest), valid range, default
2. Retry Policy: Max retries, backoff strategy (fixed/exponential), what counts as failure
3. Timeout Behavior: Default timeout, what happens on timeout (exception type, status change)
4. Concurrency Model: Threading/async, max workers, configurable or fixed
5. Status Transitions: All valid states, valid transitions, which transitions are automatic

Then write TYPED PYTHON INTERFACES with full signatures into the Interface Contract section. Include:
- Task dataclass with all fields typed
- TaskResult dataclass
- TaskStatus enum
- TaskQueue class with typed method signatures
- Error types

After filling the blackboard, write the interfaces into group-b-code/taskqueue/models.py.

CODE LOCATION: experiments/02-ambiguous-spec/group-b-code/
BLACKBOARD: experiments/02-ambiguous-spec/blackboard-b.md

Send ONE structured message when done:
{intent: 'DONE', target: 'all', payload: {task: 'design', decisions: 'blackboard updated', contract: 'M:MOD written'}}

Budget: ≤5 messages total.

WHEN DONE: Signal COMPLETE_TASK.
```

### B2: Developer A
- **Role**: `flightdeck-developer`
- **Model**: `claude-sonnet-4`
- **Group**: `ab2-aecp`
- **Task prompt**:

```
You are Developer A for a 5-agent team building a task queue library in Python.

READ THESE FILES IN ORDER:
1. experiments/02-ambiguous-spec/task-description.md (the spec — it is vague, but the architect resolves ambiguities)
2. experiments/02-ambiguous-spec/group-b-rules.md (AECP communication rules — YOU MUST FOLLOW THESE)
3. experiments/02-ambiguous-spec/blackboard-b.md (shared blackboard — check Design Decisions and Interface Contract)

COMMUNICATION RULES: You MUST follow AECP protocol. No prose. Structured messages only. Silence = working.

YOUR FILES (you own these):
- experiments/02-ambiguous-spec/group-b-code/taskqueue/models.py — Task, TaskResult, TaskStatus, error types (architect may have already written interfaces here)
- experiments/02-ambiguous-spec/group-b-code/taskqueue/__init__.py — package init, public API exports

WAIT FOR: Check the blackboard. When design status = "done" and the Design Decisions sections are filled in, read them carefully and start coding. The architect has resolved all ambiguities — follow the blackboard decisions exactly. Do NOT message to ask — just read the blackboard.

If the architect already wrote interfaces into models.py, verify and complete the implementation. If not, implement based on the Interface Contract on the blackboard.

WHEN COMPLETE:
1. Update YOUR rows on the blackboard (models → done, pkg-init → done)
2. Send ONE message: {intent: 'DONE', target: 'all', payload: {task: 'models+init', files: ['M:MOD', 'M:INI']}}

File ref codes: M:MOD = models.py, M:ENG = engine.py, M:INI = __init__.py, T:TST = test_queue.py

Budget: ≤3 messages total. Silence = working.

WHEN DONE: Signal COMPLETE_TASK.
```

### B3: Developer B
- **Role**: `flightdeck-developer`
- **Model**: `claude-sonnet-4`
- **Group**: `ab2-aecp`
- **Task prompt**:

```
You are Developer B for a 5-agent team building a task queue library in Python.

READ THESE FILES IN ORDER:
1. experiments/02-ambiguous-spec/task-description.md (the spec — it is vague, but the architect resolves ambiguities)
2. experiments/02-ambiguous-spec/group-b-rules.md (AECP communication rules — YOU MUST FOLLOW THESE)
3. experiments/02-ambiguous-spec/blackboard-b.md (shared blackboard — check Design Decisions and Interface Contract)

COMMUNICATION RULES: You MUST follow AECP protocol. No prose. Structured messages only. Silence = working.

YOUR FILE (you own this):
- experiments/02-ambiguous-spec/group-b-code/taskqueue/engine.py — TaskQueue class with submit, process, retry, timeout, concurrency

WAIT FOR: Check the blackboard. When design status = "done", read the Design Decisions (especially retry policy, timeout behavior, concurrency model) and the Interface Contract. Also read Dev A's models.py for the exact types.

IMPORTANT: The spec is vague but the architect has resolved all ambiguities on the blackboard. Follow the blackboard decisions exactly — especially:
- Priority direction (check which way is "higher")
- Retry count and backoff strategy
- Timeout default and behavior
- Concurrency model (threading vs async, worker count)
- Valid status transitions

Do NOT message to ask — read the blackboard and models.py.

WHEN COMPLETE:
1. Update YOUR row on the blackboard (engine → done)
2. Send ONE message: {intent: 'DONE', target: 'all', payload: {task: 'engine', files: ['M:ENG']}}

File ref codes: M:MOD = models.py, M:ENG = engine.py, M:INI = __init__.py, T:TST = test_queue.py

Budget: ≤3 messages total. Silence = working.

WHEN DONE: Signal COMPLETE_TASK.
```

### B4: Reviewer
- **Role**: `flightdeck-code-reviewer`
- **Model**: `claude-sonnet-4`
- **Group**: `ab2-aecp`
- **Task prompt**:

```
You are the Code Reviewer for a 5-agent team building a task queue library in Python.

READ THESE FILES IN ORDER:
1. experiments/02-ambiguous-spec/task-description.md (the spec)
2. experiments/02-ambiguous-spec/group-b-rules.md (AECP communication rules — YOU MUST FOLLOW THESE)
3. experiments/02-ambiguous-spec/blackboard-b.md (shared blackboard — check Design Decisions and task statuses)

COMMUNICATION RULES: You MUST follow AECP protocol. No prose. Structured verdicts only.

YOUR JOB:
1. WAIT: Check the blackboard. When models AND engine both show status "done", begin review.
2. Read the Design Decisions on the blackboard — these are the authoritative spec.
3. Review ALL code in experiments/02-ambiguous-spec/group-b-code/taskqueue/
4. CHECK SPECIFICALLY:
   - Do models.py and engine.py agree on priority semantics? (AMB-1)
   - Does engine.py implement the retry policy from the blackboard? (AMB-2, AMB-3, AMB-4)
   - Does timeout behavior match the blackboard decision? (AMB-5, AMB-6)
   - Is the concurrency model what the architect specified? (AMB-7)
   - Are status transitions consistent between models and engine? (AMB-8, AMB-9)
5. Update blackboard: set review status
6. Send ONE verdict: {intent: 'VERDICT', target: 'all', payload: {task: 'review', verdict: 'pass|fail', issues: [...]}}

If issues found, post to blackboard Findings section:
{intent: 'BUG', target: 'dev-a|dev-b', payload: {file: 'M:XXX', issue: 'description'}}

Budget: ≤3 messages total.

WHEN DONE: Signal COMPLETE_TASK after posting final verdict.
```

### B5: Tester
- **Role**: `flightdeck-qa-tester`
- **Model**: `claude-sonnet-4`
- **Group**: `ab2-aecp`
- **Task prompt**:

```
You are the QA Tester for a 5-agent team building a task queue library in Python.

READ THESE FILES IN ORDER:
1. experiments/02-ambiguous-spec/task-description.md (the spec)
2. experiments/02-ambiguous-spec/group-b-rules.md (AECP communication rules — YOU MUST FOLLOW THESE)
3. experiments/02-ambiguous-spec/blackboard-b.md (shared blackboard — check Design Decisions and review status)

COMMUNICATION RULES: You MUST follow AECP protocol. No prose. Structured verdicts only.

YOUR FILE (you own this):
- experiments/02-ambiguous-spec/group-b-code/tests/test_queue.py — write 15-20 tests here

YOUR JOB:
1. WAIT: Check the blackboard. When review status = "done" or "pass", begin testing.
2. Read the Design Decisions on the blackboard — these define expected behavior.
3. Read the actual code in group-b-code/taskqueue/ to understand implementations.
4. Write 15-20 tests covering: submit/execute, priority ordering, retry, timeout, concurrency, status tracking, edge cases.
5. Run: cd experiments/02-ambiguous-spec/group-b-code && python -m pytest tests/ -v
6. Update blackboard: set tests status and result.
7. Send ONE verdict: {intent: 'VERDICT', target: 'all', payload: {task: 'tests', verdict: 'pass|fail', count: 'X/N', failures: [...]}}

If failures, post to blackboard Findings:
{intent: 'BUG', target: 'dev-a|dev-b', payload: {test: 'name', file: 'M:XXX', issue: 'description'}}

Budget: ≤3 messages total. Silence = working.

WHEN DONE: Signal COMPLETE_TASK after all tests pass.
```

---

## Execution Sequence

```
T=0  Create groups "ab2-english" and "ab2-aecp"
T=0  Launch ALL 10 agents simultaneously
     Agents self-sequence via prompt instructions
T=?  Agents complete — collect system-level message counts
T=?  Run measurement framework against results
```

## Observer Setup

Assign the **Radical Thinker** as observer:
- Add to BOTH groups (read-only)
- Task: "Monitor ab2-english and ab2-aecp. Track: (1) clarification requests per AMB-1 through AMB-9, (2) message counts, (3) conflicting assumptions between devs. Write to experiments/02-ambiguous-spec/observations.md. CRITICAL: Use SYSTEM-LEVEL message counts, not blackboard self-reports."

Assign the **Designer** for RS scoring:
- Task: "After both groups complete, score RS on 5 messages from each group. Write to experiments/02-ambiguous-spec/rs-scores.md."

## Key Differences from Exp 01

| | Exp 01 | Exp 02 |
|---|---|---|
| Spec | Typed interfaces provided | Natural language only |
| Ambiguities | ~0 | 9 deliberate |
| Primary metric | Message count (H2) | Clarifications (H3) |
| Message counting | Self-reported (failed) | System-level |
| Stubs | Detailed docstrings | Minimal (2-line) |
| Group B blackboard | Pre-filled assignments | Empty decision sections architect must fill |
