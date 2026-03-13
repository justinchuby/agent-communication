# AECP Experiment Design: Bug Hunt Protocol Comparison

**Companion to:** `unified-protocol-spec.md`  
**Primary author:** Architect, with experiment scenario by Radical Thinker  
**Status:** Ready for implementation

---

## 1. Objective

Measure the impact of the AECP protocol stack on token consumption, task quality, and human observability in a controlled multi-agent coordination task.

**Research question:** Does AECP achieve ≥60% token reduction vs. English communication while maintaining task quality (RS ≥ 0.75)?

---

## 2. Task: "Bug Hunt"

### Why This Task
A bug-hunting scenario exercises all coordination primitives:
- **Coordination:** who investigates what, avoiding duplicate work
- **Information sharing:** Agent A finds a clue, needs to inform Agent B
- **Decision-making:** diagnosing root cause, choosing a fix strategy
- **Clear success metric:** bug fixed, tests pass

### Scenario Setup

**Codebase:** A pre-built mini application (~5 files) with a planted bug that spans 2 files:
- `src/auth/validate.ts` — function signature was changed (added a required parameter)
- `src/routes/login.ts` — still calls the old signature (missing parameter)
- `src/models/user.ts` — data model (no bug, but agents must verify)
- `src/middleware/session.ts` — session management (no bug, but related to auth flow)
- `src/tests/auth.test.ts` — tests that fail due to the bug

The bug is realistic: a function signature change in one module that a dependent module doesn't account for. It requires reading multiple files, understanding the call chain, and coordinating a fix + test verification.

### Agent Roles

| Role | Responsibility |
|------|---------------|
| **Investigator** | Read code, trace the bug, identify root cause |
| **Fixer** | Implement the fix based on Investigator's findings |
| **Reviewer** | Verify the fix is correct, run tests, approve |

### Success Criteria
1. Bug is correctly identified (root cause matches planted bug)
2. Fix is implemented (code change resolves the issue)
3. Tests pass after fix
4. No regressions introduced

---

## 3. Experimental Conditions

Each condition uses the same task, same agent roles, same LLM model. Only the communication protocol differs.

| Condition | Layers Active | Description |
|-----------|--------------|-------------|
| **A: English Baseline** | None | Agents communicate freely in unrestricted natural language. No protocol constraints. |
| **B: SIP Only** | Layer 2 | All messages must use Structured Intent Protocol (typed JSON envelopes). No shared state, no compression. |
| **C: SBDS + SIP** | Layers 0 + 2 | Shared blackboard with task state + structured messages. Agents can read/write blackboard. No PCC. |
| **D: Full Stack** | Layers -1, 0, 1, 2, 3 | Complete AECP: expectation model, blackboard with triggers, content-addressable refs, SIP, PCC. Communication by exception. |
| **E: Full + Short Mode** | Layers -1, 0, 2 | Full stack minus PCC (testing short-session performance). Validates whether PCC adds value for a ~30-message task. |
| **F: Emergent Protocol** | None prescribed | Agents given a token budget constraint and told to "minimize token usage while maintaining task quality." NO protocol prescribed — tests whether agents converge on AECP-like structures independently. |

### Per-Condition Setup

**Condition A:** No special setup. Agents are prompted to communicate naturally.

**Condition B:** Agents receive the SIP schema (message types, payload schemas) and brevity code table. Instructed to use SIP for all communication.

**Condition C:** Blackboard initialized with task state:
```yaml
tasks:
  investigate-bug: {status: pending, owner: investigator}
  fix-bug: {status: pending, owner: fixer, depends: [investigate-bug]}
  review-fix: {status: pending, owner: reviewer, depends: [fix-bug]}
```
Agents read/write blackboard + use SIP for direct messages.

**Condition D:** Full AECP setup:
- Expectation model registered for each agent
- Blackboard with regulatory triggers (auto-unblock dependencies)
- Standard PCC codebook pre-loaded + session-specific refs as needed
- Content-addressable refs for codebase artifacts
- Adaptive heartbeats enabled

**Condition E:** Same as D but PCC disabled (short-session mode). Tests whether the overhead of PCC bootstrap is justified for a task of this length.

---

## 4. Metrics

### Primary Metric: Tokens per Successful Task Completion (TPSTC)

Total tokens consumed (input + output) across all 3 agents, counted only for runs where the bug is correctly fixed and tests pass.

```
TPSTC = Σ(input_tokens + output_tokens) for all agents / (1 if task_success else excluded)
```

### Secondary Metrics

| Metric | Definition | How Measured |
|--------|-----------|-------------|
| **Message count** | Total inter-agent messages (excluding heartbeats) | Count from message log |
| **Error rate** | Messages requiring clarification / total messages | Count EXPAND requests, "what do you mean?" patterns, and misunderstanding-induced rework |
| **Task quality** | Correctness of bug identification + fix | Binary: root cause correct AND fix correct AND tests pass |
| **Time-to-resolution** | Wall-clock time from task start to tests passing | Timestamp delta |

### Tertiary Metrics

| Metric | Definition | How Measured |
|--------|-----------|-------------|
| **Human Readability Score (RS)** | Composite score (0.0-1.0) per §12 of unified spec | 2-3 human evaluators score Reconstructability (0.5), Scannability (0.3), Level Accessibility (0.2) |
| **Adjusted efficiency** | `tokens_saved / RS_score` | Computed from TPSTC and RS |
| **Compression curve** | Tokens per message plotted over message sequence | Only meaningful for Condition D (PCC); expect downward trend |
| **Fidelity violations** | Count of F0-level errors per condition | Review all messages; any incorrect file path, line number, or identifier = F0 violation |
| **Message length distribution** | Histogram of tokens per message | From message log |

### Red-Team Metrics (per Radical Thinker's failure mode catalog)

For conditions C-E, additionally measure:
- **Stale reads:** Count of writes rejected by optimistic concurrency
- **Trigger misfires:** Count of triggers that fired incorrectly or cascaded
- **Dangling refs:** Count of references to invalidated content
- **Ref drift incidents:** Count of codebook sync mismatches
- **Schema escape rate:** Percentage of messages using `freeform` type

---

## 5. Controls

1. **Same LLM model and temperature** across all conditions (e.g., Claude Sonnet 4, temperature 0)
2. **Same task specification and codebase** — identical planted bug
3. **Randomized condition ordering** to control for any learning effects in the evaluation
4. **10 runs per condition** (per Generalist's power analysis: at α=0.05, power=0.80, effect size d≈2.0 → n≈5 for primary metric; n=10 for adequate power on secondary metrics like error rate)
5. **Same agent prompt structure** — only the protocol instructions differ
6. **No agent memory across runs** — each run starts from scratch
7. **Blinded human evaluators** — RS scoring done without knowledge of which condition produced the transcript

---

## 6. Hypotheses

| ID | Hypothesis | Significance Threshold |
|----|-----------|----------------------|
| H1 | Condition D TPSTC < 0.30 × Condition A TPSTC | Token reduction ≥ 70% |
| H2 | Condition D RS ≥ 0.75 | Readability maintained |
| H3 | Condition D error rate ≤ Condition A error rate | No increase in misunderstandings |
| H4 | Condition D task quality = Condition A task quality | No quality degradation |
| H5 | Condition D F0 violations ≤ Condition A F0 violations | No increase in critical errors |
| H6 | Condition D compression curve is monotonically decreasing | PCC improves over session |
| H7 | Condition E TPSTC ≈ Condition D TPSTC ± 10% | PCC adds marginal value for short tasks |
| H8 | Conditions B-E message count < 0.5 × Condition A message count | Fewer messages needed |

---

## 7. Analysis Plan

### Quantitative
1. Compute TPSTC mean and standard deviation for each condition
2. Pairwise comparison (A vs B, A vs C, A vs D, A vs E, D vs E) using appropriate statistical test (t-test if normal, Mann-Whitney otherwise)
3. Plot compression curve for Condition D — fit to a decay function
4. Compute per-condition error rates with confidence intervals
5. Cross-tabulate F0 violations vs. condition

### Qualitative
1. Review all Condition D/E transcripts for failure modes from §16 of unified spec
2. Identify any novel failure modes not predicted by the red-team analysis
3. Document examples where compression caused genuine misunderstanding vs. where it worked seamlessly
4. Interview human evaluators: what was easy/hard to follow in each condition?

### Decision Criteria
- If H1-H5 all pass: **AECP v0.2 is validated.** Proceed to production pilot.
- If H1 passes but H2 fails: **Compression is too aggressive.** Raise minimum disclosure level.
- If H3 or H5 fails: **Protocol has correctness issues.** Root-cause the F0 violations and fix.
- If H7 passes: **PCC unnecessary for short tasks.** Default to short-session mode.
- If H7 fails (D >> better than E): **PCC critical even for short tasks.** Lower the 30-message threshold.

---

## 8. Test Harness Requirements

### Codebase Builder
- Script to generate the 5-file mini codebase with the planted bug
- Parameterizable: different bug types for repeated runs (avoid agents "remembering" the bug)
- Test suite that fails before fix, passes after

### Protocol Enforcer
- For conditions B-E: middleware that validates messages conform to the active protocol
- Rejects non-conforming messages and counts violations
- For Condition A: passthrough (no enforcement)

### Measurement Collector
- Token counter: intercept all LLM API calls, count input/output tokens per agent
- Message logger: capture all inter-agent messages with timestamps
- Blackboard logger: capture all blackboard reads/writes with versions
- Timer: wall-clock start/end per run

### RS Evaluation Kit
- Anonymized transcript exporter (strips condition labels)
- Scoring rubric for human evaluators (Reconstructability, Scannability, Level Accessibility)
- Source map viewer: interactive expansion of compressed messages

---

## 9. Timeline

| Phase | Deliverable |
|-------|-------------|
| Phase 1 | Build test harness (codebase generator, protocol enforcer, measurement collector) |
| Phase 2 | Run Conditions A + B (baseline and SIP-only). Establish variance. |
| Phase 3 | Run Conditions C + D + E (blackboard, full stack, short mode). |
| Phase 4 | Human RS evaluation. Statistical analysis. |
| Phase 5 | Write up findings. Update unified spec based on results. |

---

## 10. Expected Outcomes

Based on theoretical analysis (§13 of unified spec):

| Condition | Expected TPSTC (relative to A) | Expected RS | Expected Error Rate |
|-----------|--------------------------------|-------------|-------------------|
| A (English) | 1.0x (baseline) | ~0.90 | ~5-10% |
| B (SIP) | 0.50-0.65x | ~0.85 | ~3-5% |
| C (SBDS + SIP) | 0.25-0.40x | ~0.80 | ~2-4% |
| D (Full stack) | 0.15-0.30x | ~0.75-0.80 | ~2-5% |
| E (Full - PCC) | 0.20-0.35x | ~0.78 | ~2-4% |

The interesting comparison is D vs E — if they're close, PCC doesn't pay for itself at this task size and we should raise the short-session threshold.

---

## 11. Key Finding from Preliminary Simulation

The Designer's RS (Readability Score) analysis of simulated message logs produced a surprising and important result:

**Structured protocols (SIP, SBDS+SIP) score HIGHER on readability than English.**

| Condition | Token Reduction | RS Score | RS + Source Map |
|-----------|----------------|----------|----------------|
| A: English | 0% (baseline) | 0.70 | 0.70 |
| B: SIP | 76% | **0.81** | 0.81 |
| C: SBDS+SIP | 87% | **0.82** | 0.82 |
| D: Full | 95% | 0.59 | 0.69 |
| E: Full+CAR | 97% | 0.31 | 0.51 |

**Implication:** For Layers 0-2, there is no compression-readability tradeoff. Structure aids scannability so much that it more than compensates for the loss of narrative flow. The v1 target (SBDS+SIP, Condition C) delivers 87% reduction at RS 0.82 — strictly better than English on both dimensions.

PCC (Conditions D-E) is where the tradeoff begins. The "compress values, not field names" constraint (added to AECP v0.3 §8) is designed to keep PCC above the RS ≥ 0.75 threshold.

**Caution:** These are simulated (hand-crafted) message logs, not live LLM runs. The primary experiment (Conditions A-F with live agents) is needed to validate these findings. See caveats in `.flightdeck/shared/experiment/final-report.md`.

---

*Designed for honest measurement, not for confirming our priors. If the protocol fails, we want to know exactly where and why.*
