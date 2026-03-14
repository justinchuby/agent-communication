# AECP Experiments

Controlled experiments testing the Agent-Efficient Communication Protocol.

## Experiments

| # | Name | Type | Agents | Result |
|---|------|------|--------|--------|
| 00a | Bug Hunt | Live AECP test | 3 | 92% token reduction |
| 00b | 30-Agent Scale | Scalability test | 28 | 50 msgs for 28 agents (1.79/agent) |
| 01 | URL Shortener A/B | Controlled A/B | 10 | 77% message reduction, equal quality |
| 02 | Ambiguous Spec A/B | Controlled A/B | 10 | 100% clarification reduction, ~63-74% message reduction |
| 03 | Token Efficiency A/B/C | Controlled A/B/C | 15 | Message reduction overstates token savings by 3-15×; AECP v2 saves 22% |

## Experiment 03: Token Efficiency A/B/C Test

**Task:** TypeScript event emitter library (8 embedded ambiguities)  
**Purpose:** Measure actual token costs — test whether message reduction translates to token reduction  
**Groups:** 3 groups of 5 agents (English, AECP v1 monolithic, AECP v2 scoped views)  
**Protocol:** Group A = natural English, Group B = AECP v1 (full blackboard per message), Group C = AECP v2 (scoped views)

### Results

| Metric | Group A (English) | Group B (AECP v1) | Group C (AECP v2) |
|--------|-------------------|--------------------|--------------------|
| Tests passing | 18/18 | 18/18 | 18/18 |
| Messages | 12 | ~5 | ~5 |
| Token savings vs English | — | ~5% | ~22% |

### Key Findings

- **Message reduction ≠ token reduction:** AECP v1 cut messages by ~58% but only saved ~5% on tokens — structured payloads with full blackboard context are heavier per-message
- **Scoped views fix the overhead:** AECP v2 delivers each agent only the blackboard slice they need, achieving 22% real token savings
- **Message reduction overstated efficiency by 3–15×** across prior experiments
- **Equal quality across all three groups:** 18/18 tests passing in every group

**Artifacts:** [`experiments/03-token-efficiency/`](03-token-efficiency/)

## Experiment 02: Ambiguous-Spec A/B Test

**Task:** Python task queue library (deliberately ambiguous spec with 9 embedded ambiguities)  
**Purpose:** Test H3 (clarification reduction) — the metric Exp 01 couldn't test  
**Groups:** 5 agents each (Architect, Dev A, Dev B, Code Reviewer, QA Tester)  
**Protocol:** Group A = natural English, Group B = AECP with blackboard

### Results

| Metric | Group A (English) | Group B (AECP) | Change |
|--------|-------------------|----------------|--------|
| Tests passing | 21/21 | 18+ | Equal quality |
| Messages | ~19+ | ~5-7 | ~63-74% reduction |
| Clarifications | 12 | 0 | 100% reduction |

### Hypotheses

- **H2 CONFIRMED:** ~63-74% message reduction
- **H3 CONFIRMED:** 100% clarification reduction (12→0)
- **H4 CONFIRMED:** Equal task quality

### Key Insight

AECP transforms reactive Q&A into proactive documentation. Group A agents discovered ambiguities mid-task and had to stop and ask; Group B's blackboard pre-resolved them, eliminating all 12 clarification exchanges.

**Artifacts:** [`experiments/02-ambiguous-spec/`](02-ambiguous-spec/)

## Key Metrics
- RS (Readability Score): message quality
- CE (Communication Efficiency): task_success / messages_sent  
- CR (Coordination Residual): clarifications / tasks
