# Experiment 03: Token Efficiency — Controlled A/B/C Test

**Status:** Design (ready for review)
**Author:** Architect
**Date:** 2025-07-14
**Depends on:** `findings.md` §7 (Blackboard Read Costs), `02-ambiguous-spec/final-report.md`, `03-token-efficiency/design-proposal.md`, `03-token-efficiency/radical-ideas.md`

---

## 0. Motivation

Experiments 01 and 02 established that AECP reduces inter-agent **messages** by 63–77%. But as findings.md §7 states:

> "It is entirely possible that total token consumption — messages sent plus blackboard reads plus code artifact reads — is comparable between AECP and unstructured English groups, or even higher for AECP."

This is the single most important open question in the research. Message count is a proxy metric. **Total tokens consumed** is the real cost. The design-proposal.md estimates that at 5 agents, AECP v1 is ~2.6× cheaper than English in total tokens — but this has never been empirically tested. And at 14+ agents, the ratio may invert (AECP becomes MORE expensive) due to read amplification.

This experiment resolves the question definitively by:
1. Measuring actual total tokens (not message counts) across all groups
2. Testing two specific blackboard optimizations that should reduce read costs by ~65%
3. Comparing against an English baseline to establish absolute efficiency

---

## 1. Research Questions

| ID | Question | Why It Matters |
|----|----------|----------------|
| **RQ1** | Does AECP v1 reduce **total tokens** compared to English? | The core claim. §7 says we don't know. |
| **RQ2** | Do role-scoped views reduce blackboard read tokens? | Tests the highest-leverage structural optimization. |
| **RQ3** | Do delta-only re-reads reduce blackboard read tokens? | Tests the highest-impact single mechanism (est. 63% savings). |
| **RQ4** | Does optimized AECP (v2) preserve task quality? | Ensures optimizations don't degrade coordination. |
| **RQ5** | What is the token cost breakdown by category? | Maps where tokens actually go — messages, BB reads, code reads, system prompts. |

---

## 2. Hypotheses

| ID | Hypothesis | Metric | Predicted |
|----|-----------|--------|-----------|
| **H11** | AECP v1 total tokens < English total tokens | T_total | B < 0.6 × A |
| **H12** | AECP v2 total tokens < AECP v1 total tokens | T_total | C < 0.6 × B |
| **H13** | AECP v2 BB read tokens < 40% of AECP v1 BB reads | T_bb | C_bb < 0.4 × B_bb |
| **H14** | Task quality equal across all three groups | tests_passing, review_issues | A ≈ B ≈ C |
| **H15** | Blackboard reads dominate AECP v1 token budget | T_bb / T_total | > 60% of Group B's total |
| **H16** | Messages dominate English token budget | T_msg_context / T_total | > 60% of Group A's total |

Numbering continues from Exp 02 (H1–H10 established).

---

## 3. Experimental Design

### 3.1 Independent Variable

**Blackboard access pattern** with three levels:

| Group | Protocol | Blackboard Pattern | Label |
|-------|----------|--------------------|-------|
| **A** | English (natural language) | No blackboard | Control |
| **B** | AECP v1 (current protocol) | Monolithic blackboard, full reads | AECP-Naive |
| **C** | AECP v2 (optimized protocol) | Scoped views + delta re-reads | AECP-Optimized |

### 3.2 Held Constant

- **Task**: Same for all three groups (see §4)
- **Roles**: Architect, Dev A, Dev B, Reviewer, Tester (5 agents per group)
- **Model**: claude-sonnet-4 for all 15 agents
- **Codebase**: Same skeleton files, same directory structure
- **Isolation**: Groups cannot see each other's work
- **Blinding**: Agents do not know they are being compared

### 3.3 Dependent Variables (Primary)

| Metric | Symbol | Unit | How Measured |
|--------|--------|------|--------------|
| Total tokens consumed | T_total | tokens (est.) | Sum of all categories below |
| Blackboard read tokens | T_bb | tokens (est.) | File size at time of each read × reads |
| Message tokens (sent) | T_msg_out | tokens (est.) | Word count × 1.3 for each message |
| Message tokens (context) | T_msg_ctx | tokens (est.) | Accumulated conversation size × agents × turns |
| Code artifact read tokens | T_code | tokens (est.) | File sizes × reads per agent |
| System prompt tokens | T_sys | tokens (est.) | Prompt word count × 1.3, paid once per agent |

### 3.4 Dependent Variables (Secondary)

| Metric | Unit | How Measured |
|--------|------|--------------|
| Tests passing | X/18 | pytest output |
| Review issues found | count + severity | Reviewer output |
| Clarification requests | count | Manual classification |
| Messages sent | count | System logs |
| Blackboard reads per agent | count | File access log |
| Wall clock time to completion | minutes | Timestamps |

---

## 4. Task: Python Event Emitter Library

### 4.1 Why a New Task

Exp 01 used a URL shortener. Exp 02 used a task queue. Reusing either risks confounding through model familiarity with these exact patterns. A fresh task controls for this.

### 4.2 Task Design Criteria

The task must:
- Require inter-developer coordination (shared interfaces)
- Have enough design decisions to populate a meaningful blackboard
- Be completable in a single session by 5 agents
- Produce measurable output (tests)
- Be **moderately ambiguous** (like Exp 02) to stress-test coordination

### 4.3 Task Specification

**Build a Python Event Emitter Library**

Build an event emitter library that lets users register listeners, emit events, and manage subscriptions with filtering, priority, and error handling.

**Modules:**

```
eventemitter/
├── __init__.py    # Package init — export public API (Dev A)
├── types.py       # Event, Listener, Subscription types (Dev A)
├── emitter.py     # EventEmitter core logic (Dev B)
tests/
├── __init__.py
└── test_emitter.py  # All tests (Tester)
```

**What it should do:**

The library manages event subscriptions. Users register listener functions for named events. When an event is emitted, all matching listeners are called. Listeners can have priorities — higher priority listeners should be called first. Listeners can be one-shot (auto-removed after first call). Events can carry data payloads. Errors in listeners shouldn't crash the emitter.

**Deliberately ambiguous areas** (architect must resolve):

1. **Priority direction**: Is priority=1 highest or lowest?
2. **Error handling policy**: Swallow listener errors silently? Collect and re-raise? Call an error handler?
3. **Wildcard support**: Should `on("*", fn)` catch all events? What about patterns like `user.*`?
4. **Async support**: Sync-only? Async-optional? Both?
5. **Max listeners**: Per-event cap? Global cap? No cap? Warning threshold?
6. **Event data model**: Positional args? Keyword args? Typed Event object?
7. **Listener ordering**: Within same priority, FIFO? LIFO? Undefined?
8. **Return values**: Do listeners return values? If so, how are they collected?

**Requirements:**
- Pure Python (stdlib only)
- Python 3.10+
- Type hints on public API
- 15–20 test cases

**Roles:**

| Role | Owns |
|------|------|
| Architect | Design decisions — resolve ambiguities, define interfaces |
| Developer A | `types.py` + `__init__.py` |
| Developer B | `emitter.py` |
| Reviewer | Review all code |
| Tester | `test_emitter.py` — write and run tests |

### 4.4 Why This Task Works

- **8 ambiguities** (comparable to Exp 02's 9) — ensures the blackboard carries meaningful design content
- **Clear module boundaries** — types.py defines the shared contract, emitter.py implements it
- **Coordination-dependent** — Dev B's emitter.py calls types defined by Dev A
- **Testable** — produces clear pass/fail results
- **Similar complexity** — comparable to task queue (Exp 02) in scope and decision count

---

## 5. Optimization Mechanisms Under Test

### 5.1 Mechanism 1: Role-Scoped Blackboard Views

**What:** Instead of every agent reading the full blackboard, each agent reads a role-specific filtered view containing only the sections relevant to their work.

**How it works:**

The architect writes the master blackboard (same as AECP v1). But Group C's protocol rules instruct the architect to also generate per-role view files:

```
blackboard-c.md              # Master (architect reads this)
blackboard-c-deva.md         # Dev A's view (types.py scope)
blackboard-c-devb.md         # Dev B's view (emitter.py scope)
blackboard-c-reviewer.md     # Reviewer's view (all code-relevant)
blackboard-c-tester.md       # Tester's view (contract + test scope)
```

**Scoping rules:**

| Section | Architect | Dev A | Dev B | Reviewer | Tester |
|---------|-----------|-------|-------|----------|--------|
| Task header | ✅ | ✅ | ✅ | ✅ | ✅ |
| All design decisions | ✅ | own-module | own-module | ✅ | ❌ |
| Interface contract | ✅ | ✅ | ✅ | ✅ | ✅ |
| Assignments | ✅ | own-row | own-row | all | status-only |
| Findings | ✅ | own | own | all | ❌ |
| Metrics | ✅ | ❌ | ❌ | ❌ | ❌ |

Dev A gets: task header + priority decision + listener ordering + event data model + interface contract + own assignment row.
Dev B gets: task header + all design decisions (emitter implements all of them) + interface contract + own assignment row.
Tester gets: task header + interface contract + assignment statuses.

**Predicted savings (based on Exp 02 analysis):**

The Exp 02 blackboard was ~1,098 tokens. Scoping reduced per-read cost by 17% on average (range: 0–45% depending on role). For this experiment, with 8 design decisions and more module specialization, we predict 20–35% average reduction per read.

**Implementation:** The architect manually creates the scoped files (adds ~5 minutes of work). The protocol rules specify which file each role reads. This requires zero infrastructure changes — it's just a file-naming convention.

### 5.2 Mechanism 2: Delta-Only Re-reads

**What:** After the first full read, agents read only a changelog file showing what changed since they last checked.

**How it works:**

The master blackboard tracks a version number. When the architect (or any agent) updates the blackboard, they append to a changelog file:

```markdown
# Blackboard Changelog

## v2 (after architect design)
- SET decisions.priority: 1=highest, range 1-10
- SET decisions.error_handling: collect errors, call on_error callback
- SET decisions.wildcard: prefix matching with `*` glob
- SET decisions.async: sync-only (stdlib constraint)
- SET decisions.max_listeners: 100 per event, warning at 80
- SET decisions.event_data: typed Event(name, data: dict, timestamp)
- SET decisions.listener_ordering: same-priority FIFO
- SET decisions.return_values: ignored (listeners are side-effect-only)
- SET interface_contract: <full typed Python contract>
- SET assignments: dev-a → types.py, dev-b → emitter.py

## v3 (after dev-a completion)
- SET assignments.types.status: done
- APPEND findings: F-1: consider making Event frozen dataclass

## v4 (after dev-b completion)
- SET assignments.emitter.status: done
```

**Protocol rules for agents:**

1. **First activation:** Read your role-scoped blackboard view (full read).
2. **Subsequent checks:** Read `blackboard-c-changelog.md` only. If no new versions since your last read, stop (0 useful tokens consumed beyond the changelog check).
3. **If changelog references a section you need in full:** Read that specific section from the master blackboard.

**Predicted savings:**

Based on Exp 02 analysis (design-proposal.md §3.4):
- First reads: ~4,538 tokens (scoped) → unavoidable
- Re-reads without deltas: 5 agents × 2 re-reads × ~900 avg scoped view = 9,000 tokens
- Re-reads with deltas: 5 agents × 2 re-reads × ~60 avg delta = 600 tokens
- **Re-read savings: ~93%**

### 5.3 Combined Predicted Impact

```
                            Group B (AECP v1)    Group C (AECP v2)     Savings
First BB reads (5 agents):  5 × 1,100 = 5,500   5 × 770 = 3,850      30%
Re-reads (5 agents × 2):   5 × 2 × 1,100 = 11,000  5 × 2 × 60 = 600  95%
                            ────────────────     ──────────────────
Total BB read tokens:       16,500               4,450                  73%
```

Combined with message reduction (from AECP v1, carried forward): the total token budget for Group C should be significantly lower than both Group A and Group B.

---

## 6. Token Accounting Methodology

### 6.1 The Full Token Equation

```
T_total(group) = T_sys + T_bb + T_msg_out + T_msg_ctx + T_code
```

Where:
- **T_sys** = system prompt tokens, paid once per agent at session start
- **T_bb** = blackboard read tokens (Group A: 0, Group B: full reads, Group C: scoped + deltas)
- **T_msg_out** = tokens in messages produced (output tokens)
- **T_msg_ctx** = tokens in conversation context consumed on each turn (input tokens from accumulated messages). This is the key cost for English — the conversation grows, and every agent re-reads the full history on each turn.
- **T_code** = tokens consumed reading code files (source files, test output)

Note: We intentionally **exclude** internal reasoning tokens (chain-of-thought) because they are not observable and are driven by task complexity rather than communication protocol. We also exclude code generation output tokens — those measure implementation effort, not coordination cost.

### 6.2 Measurement Method: Word Count × 1.3

We approximate token counts as `word_count × 1.3`. This is a standard approximation for English text with code (pure English ≈ 1.33 words/token; code ≈ 1.5 words/token; blended ≈ 1.3).

Every measurable text artifact is captured:
- System prompts (fixed, measured before experiment)
- Blackboard files (measured at each version)
- Messages (captured from system logs)
- Code files (measured at each version read by an agent)

### 6.3 What We Measure and When

| Event | What to Record | Token Calculation |
|-------|---------------|-------------------|
| Agent spawns | System prompt text | words × 1.3 |
| Agent reads blackboard | File content at read time | words × 1.3 |
| Agent reads changelog | Changelog content | words × 1.3 |
| Agent reads code file | File content at read time | words × 1.3 |
| Agent sends message | Message text | words × 1.3 |
| Agent receives messages | All unread messages in context | Σ(message words) × 1.3 |
| Agent reads test output | pytest output text | words × 1.3 |

### 6.4 Tracking File Reads

This is the hardest measurement challenge. Unlike messages (observable in system logs), file reads are internal to each agent's turn. We use two complementary approaches:

**Approach 1: Protocol-mandated logging.** Each agent's prompt includes:
> "Before reading any file, log the read to `token-log-{group}.md` in the format: `{agent} READ {file} at {timestamp}`"

**Approach 2: Workflow-based estimation.** Each agent's workflow is predictable:
- Architect: reads task spec (1×), writes blackboard (0 reads), reads code for decisions (0×)
- Dev A: reads blackboard (1× initial + 1–2 re-reads), reads task spec (1×), reads own code (while editing, not a "read")
- Dev B: reads blackboard (1× initial + 1–2 re-reads), reads task spec (1×), reads Dev A's types.py (1×)
- Reviewer: reads blackboard (1×), reads all code files (1× each = 3 files), reads task spec (1×)
- Tester: reads blackboard (1×), reads all code files (1× each = 3 files), reads task spec (1×), reads test output (1–3×)

We use Approach 2 as the primary estimate and Approach 1 as validation. If they diverge by >20%, we investigate.

### 6.5 Conversation Context Growth Model (Group A)

For the English group, the key cost driver is **conversation context accumulation**. Each agent turn includes all prior messages in the conversation. We model this as:

```
T_msg_ctx = Σ_turns [ |accumulated_messages_at_turn_t| × 1.3 ]
```

This requires tracking the message-by-message conversation growth. We reconstruct this from system logs post-experiment, computing the cumulative token count at each turn.

For AECP groups (B and C), T_msg_ctx is minimal because only 5–7 structured messages are exchanged (each ~20 tokens), so context accumulation is negligible.

---

## 7. Group Protocols

### 7.1 Group A: English (Control)

Identical to Exp 01/02 Group A protocol:
- Agents communicate freely in natural English via group chat
- No blackboard, no structured message format
- No message budget
- Agents coordinate by reading conversation history

**Communication rules file:** `group-a-rules.md`
> "Communicate naturally in English. Use the group chat to coordinate. Ask questions when things are unclear. Share your progress. There are no special rules — just work together to build the library."

### 7.2 Group B: AECP v1 — Monolithic Blackboard (Baseline)

Identical to Exp 01/02 Group B protocol:
- Shared blackboard file: `blackboard-b.md`
- Architect populates design decisions and interface contract
- Agents read the **full** blackboard on every check
- Structured messages only (DONE, VERDICT, BUG signals)
- Message budget: ≤5 per agent

**Communication rules file:** `group-b-rules.md`
> Standard AECP v1 rules (silence = working, update blackboard, structured signals only).

**Blackboard template:** Same structure as Exp 02 — Task, Design Decisions, Interface Contract, Assignments, Findings, Metrics sections.

### 7.3 Group C: AECP v2 — Scoped Views + Delta Re-reads (Treatment)

The new optimized protocol:

**Blackboard files:**
```
blackboard-c.md                # Master blackboard (architect writes here)
blackboard-c-deva.md           # Dev A's scoped view
blackboard-c-devb.md           # Dev B's scoped view
blackboard-c-reviewer.md       # Reviewer's scoped view
blackboard-c-tester.md         # Tester's scoped view
blackboard-c-changelog.md      # Delta log (all agents read for re-reads)
```

**Protocol rules for Group C:**

**Architect:**
1. Read task spec. Resolve all 8 ambiguities.
2. Write the full master blackboard (`blackboard-c.md`) with all design decisions and the typed interface contract.
3. Generate per-role scoped views by copying only the relevant sections into each role's file. (The experiment design provides a section→role mapping table to follow.)
4. Send ONE structured DONE message to the group.
5. When any agent updates the blackboard (status changes, findings), append the change to `blackboard-c-changelog.md` with a version number.

**Developers (A and B):**
1. **First read:** Read your role-scoped blackboard view (`blackboard-c-dev{a,b}.md`). Do NOT read the master blackboard.
2. **Re-reads:** Read ONLY `blackboard-c-changelog.md`. If a changelog entry references a section you need in full, read that specific section from your scoped view.
3. Implement your assigned files.
4. When done, update the master blackboard (assignment status) AND append to the changelog.
5. Send ONE structured DONE message.

**Reviewer:**
1. **First read:** Read `blackboard-c-reviewer.md`.
2. **Re-reads:** Read ONLY `blackboard-c-changelog.md`.
3. Review all code files.
4. Post findings to master blackboard + changelog.
5. Send ONE structured VERDICT message.

**Tester:**
1. **First read:** Read `blackboard-c-tester.md`.
2. **Re-reads:** Read ONLY `blackboard-c-changelog.md`.
3. Write tests, run suite.
4. Post results to master blackboard + changelog.
5. Send ONE structured VERDICT message.

**Communication rules file:** `group-c-rules.md`
> "Follow AECP protocol with two optimizations: (1) Read ONLY your role-specific blackboard file, not the master. (2) For re-reads, read ONLY the changelog file. These rules minimize token waste. All other AECP rules apply: silence = working, structured signals only, message budget ≤5."

---

## 8. Predicted Token Budgets

### 8.1 Group A (English) — Predicted

Based on Exp 02 Group A data, scaled to the new task:

```
T_sys:      5 agents × ~800 words × 1.3                    =   5,200 tokens
T_bb:       0 (no blackboard)                               =       0 tokens
T_msg_out:  ~20 messages × ~80 words × 1.3                  =   2,080 tokens
T_msg_ctx:  5 agents × ~8 turns × ~1,200 avg ctx words × 1.3= 62,400 tokens
T_code:     3 agents × 3 files × ~150 words × 1.3           =   1,755 tokens
                                                     ─────────────────────
T_total_A ≈                                                   71,435 tokens
```

The dominant cost is **T_msg_ctx** (87%) — agents re-reading the growing conversation on every turn.

### 8.2 Group B (AECP v1) — Predicted

Based on Exp 02 Group B data:

```
T_sys:      5 agents × ~900 words × 1.3                    =   5,850 tokens
T_bb:       5 agents × 3 reads × ~1,100 words × 1.3        =  21,450 tokens
T_msg_out:  ~6 messages × ~20 words × 1.3                   =     156 tokens
T_msg_ctx:  5 agents × ~2 turns × ~60 avg ctx words × 1.3   =     780 tokens
T_code:     3 agents × 3 files × ~150 words × 1.3           =   1,755 tokens
                                                     ─────────────────────
T_total_B ≈                                                   29,991 tokens
```

The dominant cost is **T_bb** (72%) — agents reading the full blackboard repeatedly. This directly validates or refutes H15.

### 8.3 Group C (AECP v2) — Predicted

```
T_sys:      5 agents × ~1,000 words × 1.3                  =   6,500 tokens
T_bb_first: 5 agents × 1 read × ~770 avg scoped words × 1.3=   5,005 tokens
T_bb_delta: 5 agents × 2 reads × ~50 avg delta words × 1.3 =     650 tokens
T_bb:       (first + delta)                                 =   5,655 tokens
T_msg_out:  ~6 messages × ~20 words × 1.3                   =     156 tokens
T_msg_ctx:  5 agents × ~2 turns × ~60 avg ctx words × 1.3   =     780 tokens
T_code:     3 agents × 3 files × ~150 words × 1.3           =   1,755 tokens
                                                     ─────────────────────
T_total_C ≈                                                   14,846 tokens
```

### 8.4 Predicted Ratios

```
T_total_A (English):       ~71,400 tokens (baseline)
T_total_B (AECP v1):       ~30,000 tokens (58% reduction vs A)
T_total_C (AECP v2):       ~14,800 tokens (79% reduction vs A, 51% reduction vs B)
```

If these predictions hold:
- **H11 confirmed**: AECP v1 is ~2.4× cheaper than English in total tokens
- **H12 confirmed**: AECP v2 is ~2× cheaper than AECP v1
- **H13 confirmed**: BB reads drop from ~21,450 to ~5,655 (74% reduction)
- **H15 confirmed**: BB reads are 72% of Group B's budget
- **H16 confirmed**: Message context is 87% of Group A's budget

---

## 9. Execution Plan

### 9.1 Pre-Experiment Setup

1. **Create codebase skeleton** — identical `eventemitter/` directory for all three groups:
   ```
   group-a-code/eventemitter/{__init__.py, types.py, emitter.py}
   group-a-code/tests/{__init__.py, test_emitter.py}
   group-b-code/...  (identical copy)
   group-c-code/...  (identical copy)
   ```

2. **Create protocol materials:**
   - `task-description.md` — shared across all groups
   - `group-a-rules.md` — English protocol
   - `group-b-rules.md` — AECP v1 protocol
   - `group-c-rules.md` — AECP v2 protocol (scoped views + delta re-reads)
   - `blackboard-b.md` — empty AECP v1 blackboard template
   - `blackboard-c.md` — empty AECP v2 master blackboard template
   - `blackboard-c-changelog.md` — empty changelog
   - `blackboard-c-{deva,devb,reviewer,tester}.md` — empty scoped view templates

3. **Create token accounting infrastructure:**
   - `token-log-a.md`, `token-log-b.md`, `token-log-c.md` — agent-reported file read logs
   - `token-accounting.md` — post-experiment token calculation spreadsheet template

4. **Pre-measure fixed costs:**
   - Count words in each system prompt (task description + rules file + blackboard instructions)
   - Record T_sys for each agent in each group

### 9.2 Agent Launch

**15 agents launched simultaneously** (5 per group):

```
Group A: A1-arch, A2-devA, A3-devB, A4-reviewer, A5-tester
Group B: B1-arch, B2-devA, B3-devB, B4-reviewer, B5-tester
Group C: C1-arch, C2-devA, C3-devB, C4-reviewer, C5-tester
```

**Three groups created:**
```
CREATE_GROUP {"name": "exp03-english",  "members": [A1..A5]}
CREATE_GROUP {"name": "exp03-aecp-v1",  "members": [B1..B5]}
CREATE_GROUP {"name": "exp03-aecp-v2",  "members": [C1..C5]}
```

All agents use `claude-sonnet-4`. Groups run in parallel.

### 9.3 During Experiment

The experiment lead (or observer agent) monitors:
- Group chat messages (captured automatically by system logs)
- File modifications (via `git log` or filesystem timestamps)
- Agent completion signals

**No manual intervention** during the experiment. If an agent gets stuck, let it resolve naturally (this is part of the measurement — coordination failures cost tokens).

### 9.4 Post-Experiment Data Collection

**Phase 1: Raw data extraction (within 1 hour of completion)**

1. Export all group chat messages (text + timestamps + sender)
2. Capture final state of all blackboard files (including changelogs)
3. Capture final state of all code files
4. Record git log of all file modifications with timestamps
5. Collect pytest output from all three groups
6. Collect each agent's token-log file

**Phase 2: Token accounting (within 24 hours)**

For each group, compute:

```
For each agent a in group:
  T_sys(a)     = word_count(system_prompt_for_a) × 1.3
  T_bb(a)      = Σ_reads [ word_count(blackboard_at_read_time) × 1.3 ]
  T_msg_out(a) = Σ_messages_sent [ word_count(msg) × 1.3 ]
  T_msg_ctx(a) = Σ_turns [ word_count(all_messages_before_turn) × 1.3 ]
  T_code(a)    = Σ_file_reads [ word_count(file_at_read_time) × 1.3 ]
  T_total(a)   = T_sys(a) + T_bb(a) + T_msg_out(a) + T_msg_ctx(a) + T_code(a)

T_total(group) = Σ_agents T_total(a)
```

**Phase 3: Analysis and report (within 48 hours)**

- Test all hypotheses H11–H16
- Generate token breakdown charts (pie chart per group, stacked bar across groups)
- Compare actual vs predicted budgets from §8
- Qualitative analysis of coordination patterns
- Write final report to `experiments/03-token-efficiency/final-report.md`

---

## 10. Risks and Mitigations

### 10.1 Measurement Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agents don't log file reads | Missing T_bb and T_code data | Use workflow-based estimation (§6.4 Approach 2) as backup; cross-validate with git timestamps |
| Word×1.3 approximation is inaccurate | Token estimates off by 10–20% | Apply same approximation to all groups — relative comparisons remain valid even if absolute numbers are off |
| Conversation context model is wrong | T_msg_ctx estimate unreliable | Extract actual message sequence from logs; compute exact accumulation |
| Group C architect doesn't follow scoping rules | Scoped views are actually full blackboard copies | Pre-experiment training prompt; validate scoped files post-hoc (verify they're actually smaller) |

### 10.2 Experimental Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Group C protocol overhead slows work | Quality degrades, confounding H14 | Monitor; if quality drops >20%, note as finding rather than protocol failure |
| Changelog maintenance is error-prone | Agents forget to update changelog | Make it part of the DONE signal protocol — "update changelog THEN send DONE" |
| Scoped views miss critical information | Dev produces wrong output, needs rework | Include interface contract in ALL scoped views; scoping only removes irrelevant design decisions |
| N=1 per condition (same as Exp 01/02) | No statistical power | Acknowledged limitation; this experiment establishes the measurement methodology for future N=10 replication |

### 10.3 Design Risk: Scoping Adds Architect Overhead

The biggest practical risk is that Group C's architect spends significant extra effort creating scoped views (5 files instead of 1), which consumes more tokens in the architect's session. We must account for this:

**Architect overhead estimate:**
- Writing master blackboard: ~500 output tokens (same as Group B)
- Creating 4 scoped views: ~200 output tokens (copy-paste with deletion)
- Creating changelog: ~50 output tokens (initial structure)
- **Total overhead: ~250 extra output tokens for architect**

This overhead is small compared to the read savings (~16,500 saved across team). But we measure it explicitly to confirm.

---

## 11. Success Criteria

The experiment succeeds if it produces **definitive answers** to RQ1–RQ5, regardless of which hypotheses are confirmed or refuted.

Specifically:

1. **All three groups complete the task** with passing tests (≥15/18). If any group fails to produce working code, the quality comparison (H14) is still informative.

2. **Token accounting is complete** for all three groups — every category (T_sys, T_bb, T_msg_out, T_msg_ctx, T_code) has a measured or estimated value with documented methodology.

3. **The total token comparison has clear signal** — if T_total_B < T_total_A, we can quantify by how much. If T_total_B ≈ T_total_A (within 20%), we've discovered that AECP's message reduction is offset by read costs — an equally valuable finding.

4. **The optimization mechanisms show measurable effect** — T_bb for Group C is measurably different from Group B (>20% difference).

---

## 12. Relationship to Prior Work

| Aspect | Exp 01 | Exp 02 | Exp 03 (this) |
|--------|--------|--------|----------------|
| Primary metric | Messages | Clarifications | **Total tokens** |
| Groups | 2 (A/B) | 2 (A/B) | **3 (A/B/C)** |
| Spec type | Well-defined | Ambiguous | **Ambiguous** |
| Token measurement | ❌ None | ❌ None | **✅ Full accounting** |
| BB optimization | None | None | **Scoped views + deltas** |
| Task | URL shortener | Task queue | **Event emitter** |
| Hypotheses tested | H1–H5 | H3, H8–H10 | **H11–H16** |

This experiment directly addresses the #1 limitation identified in findings.md §7 and the #3 future work priority (automated measurement).

---

## 13. Open Questions for Review

1. **Should we add a 4th group testing tool-based blackboard access?** The radical-ideas.md proposes this (§3). It's the most architecturally interesting mechanism but requires agents to use function calls to query the blackboard rather than reading it as a file. This may require custom infrastructure. **Recommendation:** Defer to Exp 04. Keep Exp 03 focused on the two mechanisms that work within existing infrastructure.

2. **Should we reuse the Exp 02 task?** Reusing the task queue spec would allow direct comparison with Exp 02 data. But it risks model familiarity confounds. **Recommendation:** New task (event emitter), with the Exp 02 data as a cross-validation reference point for Groups A and B.

3. **Should we attempt N=3 per condition instead of N=1?** Running each condition 3 times would give 9 groups / 45 agents. This is expensive but would provide minimal statistical confidence. **Recommendation:** N=1 for this experiment (establishes methodology). Budget N=3 for Exp 03b replication if results are promising.

4. **Should prompt caching be considered?** radical-ideas.md §1 argues that prompt caching (available now on Anthropic) may dominate all other optimizations. However, prompt caching is a platform feature, not a protocol design — it affects cost but not token count. **Recommendation:** Note as a confound. Measure raw tokens (what the model processes), not cost (what you pay). Caching analysis can be layered on top of our token data post-hoc.

---

## Appendix A: Blackboard Templates

### A.1 Master Blackboard Template (Groups B and C)

```markdown
# Group {B,C} Blackboard

## Task
status: not_started
spec: experiments/03-token-efficiency/task-description.md

## Design Decisions

### Priority Direction
decision: [architect fills]

### Error Handling Policy
decision: [architect fills]

### Wildcard Support
decision: [architect fills]

### Async Support
decision: [architect fills]

### Max Listeners
decision: [architect fills]

### Event Data Model
decision: [architect fills]

### Listener Ordering
decision: [architect fills]

### Return Values
decision: [architect fills]

### Interface Contract
```python
# [architect fills with typed Python interface]
```

## Assignments

| task-id | file | owner | status | notes |
|---------|------|-------|--------|-------|
| design | — | architect | not_started | |
| types | types.py | dev-a | blocked(design) | |
| pkg-init | __init__.py | dev-a | blocked(design) | |
| emitter | emitter.py | dev-b | blocked(design) | |
| review | all | reviewer | blocked(impl) | |
| tests | test_emitter.py | tester | blocked(review) | |

## Findings
(none yet)

## Metrics
messages_sent: 0
clarifications: 0
```

### A.2 Changelog Template (Group C only)

```markdown
# Blackboard Changelog

Format: ## v{N} ({who}, {what})

(Agents: after EVERY blackboard update, append an entry here.
List only CHANGED fields, not the full blackboard.)
```

### A.3 Scoped View Template Example — Tester (Group C only)

```markdown
# Tester's Blackboard View

## Task
status: [mirrors master]
spec: experiments/03-token-efficiency/task-description.md

## Interface Contract
```python
# [same as master — tester needs full contract to write tests]
```

## Assignment Statuses
| task-id | status |
|---------|--------|
| types | [status] |
| emitter | [status] |
| review | [status] |
| tests | [status] |

(For design decisions or full details, read the changelog or
ask the architect. Your scoped view intentionally excludes
design rationale you don't need for writing tests.)
```

---

## Appendix B: Token Accounting Spreadsheet Template

```markdown
# Token Accounting — Experiment 03

## Group A (English)

| Agent | T_sys | T_bb | T_msg_out | T_msg_ctx | T_code | T_total |
|-------|-------|------|-----------|-----------|--------|---------|
| A1-arch | | 0 | | | | |
| A2-devA | | 0 | | | | |
| A3-devB | | 0 | | | | |
| A4-reviewer | | 0 | | | | |
| A5-tester | | 0 | | | | |
| **TOTAL** | | **0** | | | | |

## Group B (AECP v1)

| Agent | T_sys | T_bb | T_msg_out | T_msg_ctx | T_code | T_total |
|-------|-------|------|-----------|-----------|--------|---------|
| B1-arch | | | | | | |
| B2-devA | | | | | | |
| B3-devB | | | | | | |
| B4-reviewer | | | | | | |
| B5-tester | | | | | | |
| **TOTAL** | | | | | | |

## Group C (AECP v2)

| Agent | T_sys | T_bb_first | T_bb_delta | T_bb | T_msg_out | T_msg_ctx | T_code | T_total |
|-------|-------|------------|------------|------|-----------|-----------|--------|---------|
| C1-arch | | (master) | — | | | | | |
| C2-devA | | | | | | | | |
| C3-devB | | | | | | | | |
| C4-reviewer | | | | | | | | |
| C5-tester | | | | | | | | |
| **TOTAL** | | | | | | | | |

## Cross-Group Comparison

| Metric | Group A | Group B | Group C | B/A ratio | C/A ratio | C/B ratio |
|--------|---------|---------|---------|-----------|-----------|-----------|
| T_sys | | | | | | |
| T_bb | 0 | | | — | — | |
| T_msg_out | | | | | | |
| T_msg_ctx | | | | | | |
| T_code | | | | | | |
| **T_total** | | | | | | |
```
