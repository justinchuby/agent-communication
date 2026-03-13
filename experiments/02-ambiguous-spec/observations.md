# Experiment 02: Ambiguous-Spec A/B Test — Observations
### Observer: Radical Thinker (7117b453)
### Experiment: English (Group A) vs AECP (Group B) — Task Queue Library
### Status: COMPLETE
### Key Difference from Exp 01: 9 deliberate ambiguities, NO typed interfaces in spec

---

## Group A (English / ab2-english) Observations

### Communication Pattern
- Dev A sent 5 clarification questions BEFORE the architect posted a design (priority direction, retry behavior, timeout handling, concurrency model, status states)
- Dev B sent 6 clarification questions BEFORE the architect posted a design + 1 follow-up after
- Architect posted ONE comprehensive design message resolving all 9 ambiguities at once
- After design: status updates, code review, fix confirmations, social/celebration messages
- Total messages: ~19+ (approximate — counted from system notifications)
- Total clarifications: 12 (5 + 6 + 1)

### Development Flow
1. Devs started, immediately hit ambiguities, asked questions
2. Architect posted comprehensive design
3. Dev A implemented models.py + __init__.py (FSM, Task dataclass, error types)
4. Dev B implemented engine.py (TaskQueue, ThreadPoolExecutor, priority scheduling)
5. Code Reviewer found 2 medium issues (cancelled task error=None, Python 3.10 TimeoutError compat) + 2 low
6. Both devs fixed issues
7. Reviewer approved
8. QA Tester wrote 21 tests — all passed

### Key Observations
- Clarification questions came in BURSTS — both devs asked multiple questions in single messages
- Architect waited for questions before posting design (reactive pattern)
- Review found real bugs that testing alone wouldn't catch (Python 3.10 compat)
- Social messages at end (celebration, thanks) added ~4 messages with no technical content

---

## Group B (AECP / Blackboard) Observations

### Communication Pattern
- Architect wrote ALL design decisions to blackboard BEFORE devs started
- Architect also wrote typed Python interface contracts (not just prose)
- Devs read blackboard silently, implemented exactly what was specified
- Reviewer wrote findings to blackboard Findings section (not messages)
- Total messages: ~5-7 (structured DONE/VERDICT signals only)
- Total clarifications: 0

### Development Flow
1. Architect resolved all 9 ambiguities on blackboard with typed interfaces
2. Dev A implemented models.py + __init__.py (following interface contract verbatim)
3. Dev B implemented engine.py (citing "Design decisions from architect blackboard" in code comments)
4. Reviewer checked code, found 2 minor non-blocking issues, wrote to blackboard Findings
5. Dev A fixed off-by-one (F-1) after reading blackboard
6. QA Tester wrote 18 tests — all passed

### Key Observations
- Zero clarification traffic — blackboard forced proactive ambiguity resolution
- Developers CITED the blackboard in their code (engine.py line 8: "Design decisions (from architect blackboard)")
- Reviewer used blackboard Findings section instead of messages — even review is async/artifact-based
- No social/celebration messages — pure signal, no noise
- Self-reported "1 message" on blackboard is inaccurate (min 5 signals required by protocol)

---

## Cross-Group Comparison

### Clarification Patterns
- Group A: 12 clarifications (reactive — devs discover ambiguities during work)
- Group B: 0 clarifications (proactive — architect resolves before work begins)
- Pattern: In Group A, ambiguity discovery is DISTRIBUTED (each dev finds ambiguities independently). In Group B, resolution is CENTRALIZED (architect does it once on blackboard).

### Design Convergence
Both groups independently chose nearly identical architectures:
- ThreadPoolExecutor with 4 default workers
- Priority 1 = highest, range 1-10
- 3 retries with exponential backoff
- 30s default timeout
- FSM-based status transitions
- Only difference: Group B has 7 status states (adds RETRYING), Group A has 6

### Communication Efficiency
- Group A: ~19+ messages for 12 clarifications + coordination + social
- Group B: ~5-7 messages for 0 clarifications + structured signals only
- Ratio: ~3:1 message reduction
- The 12 clarification messages in Group A represent ~63% of their communication overhead

### Quality Comparison
- Group A review found 2 medium bugs (cancelled error, Py3.10 compat)
- Group B review found 2 minor issues (off-by-one, import style)
- Both groups produced working, tested code
- Group A arguably had MORE thorough review (English discussion enables deeper exploration)

---

## Observer Notes
- Radical Thinker observer (7117b453) could NOT join either group chat (system access limitation — same issue as Exp 01)
- Message counts reconstructed from system notifications and artifact analysis, not direct observation
- Self-reported blackboard metrics confirmed unreliable (claimed 1 message, actual ~5-7)
- Future experiments need automated system-level message capture

---

## Measurement Framework Results
(Filling in the metrics from measurement.md)

| Metric | Group A (English) | Group B (AECP) | Delta |
|--------|:-:|:-:|:-:|
| Total messages | ~19+ | ~5-7 | ~63-74% reduction |
| Clarification requests | 12 | 0 | 100% reduction |
| Tests passing | 21/21 | 18/18+ | Both pass |
| Code review issues | 2 medium + 2 low | 2 minor | Lower severity in B |
| Ambiguities resolved | 9/9 (reactive) | 9/9 (proactive) | Same coverage, different timing |
