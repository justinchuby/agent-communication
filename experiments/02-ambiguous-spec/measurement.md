# Experiment 02 Measurement Framework

## Experiment Design

- **Independent variable**: Communication protocol (English vs AECP)
- **Key dependent variable**: **Clarification requests (H3)** — the metric Exp 01 couldn't measure
- **Control group (A)**: 5 agents, English communication, no constraints
- **Treatment group (B)**: 5 agents, AECP rules, blackboard, structured messages
- **Held constant**: Task description, codebase skeleton, agent roles, model (claude-sonnet-4)
- **Change from Exp 01**: Deliberately ambiguous spec with NO typed interfaces

## Deliberate Ambiguities (tracked)

| # | Ambiguity | What's Vague | Resolution Requires |
|---|-----------|-------------|-------------------|
| AMB-1 | Priority direction | "higher priority runs first" — is 1 highest or 10? | Architect decision |
| AMB-2 | Retry count | "failed tasks should be retried" — how many times? | Architect decision |
| AMB-3 | Retry backoff | No backoff strategy specified | Architect decision |
| AMB-4 | Failure definition | What counts as "failed"? Exception? Return value? | Architect decision |
| AMB-5 | Timeout default | "tasks shouldn't run forever" — what's the default? | Architect decision |
| AMB-6 | Timeout behavior | Cancel? Raise? Kill thread? | Architect decision |
| AMB-7 | Concurrency model | Thread pool? async? Max workers? | Architect decision |
| AMB-8 | Status states | "several stages" — which ones? | Architect decision |
| AMB-9 | Status transitions | What transitions are valid? Can you go backwards? | Architect decision |

## Primary Metric: Clarification Requests (H3)

### Definition
A **clarification request** is any message where an agent asks for information that:
- Is not specified in the task description
- Requires a design decision
- Asks "should I..." / "what happens when..." / "how should I handle..."

### Classification Rules
- QUERY messages in Group B count as clarifications
- Questions in Group A messages count as clarifications
- Architect's initial design post does NOT count (it's proactive, not reactive)
- Follow-up questions to the architect's design DO count

### Prediction

| Group | Predicted Clarifications | Reasoning |
|-------|:---:|-----------|
| A (English) | 3-5 | Devs encounter ambiguities during implementation, ask architect |
| B (AECP) | 0-1 | Blackboard forces architect to resolve ambiguities in writing before devs start |

## All Metrics

### 1. Clarification Requests (PRIMARY — H3)
- **clarification_count**: Messages asking for spec clarification
- **ambiguities_resolved_proactively**: Design decisions made before questions were asked
- **ambiguities_hit_reactively**: Ambiguities discovered during implementation
- **CR**: clarifications / tasks

### 2. Token Efficiency
- **total_messages**: Count of all GROUP_MESSAGE + AGENT_MESSAGE
- **tokens_per_message**: Average message length
- **total_tokens**: Sum of all message tokens

### 3. Task Success
- **tests_passing**: X/N tests passing
- **code_quality**: Reviewer verdict
- **ambiguity_consistency**: Do both devs resolve the same ambiguity the same way? (Without architect guidance, they might make conflicting assumptions)

### 4. Readability
- **RS**: Score 5 messages from each group (R=0.5, S=0.3, A=0.2)

### 5. Communication Efficiency
- **CE**: task_success / messages_sent

## Hypotheses

| ID | Hypothesis | Predicted | Notes |
|----|-----------|-----------|-------|
| H3a | AECP reduces clarifications | CR_B < 0.3 × CR_A | PRIMARY — the test Exp 01 couldn't run |
| H3b | AECP architect resolves more ambiguities proactively | B_proactive > A_proactive | Blackboard structure prompts resolution |
| H8 | Ambiguous specs increase Group A messages vs Exp 01 | A_msgs_02 > A_msgs_01 (22) | More questions = more messages |
| H9 | Ambiguous specs minimally affect Group B messages | B_msgs_02 ≈ B_msgs_01 (5) | Blackboard absorbs ambiguity resolution |
| H10 | AECP prevents conflicting assumptions | B_conflicts = 0, A_conflicts ≥ 1 | Shared blackboard = single source of truth |
| H4 | Task success is equal | Both pass all tests | Same as Exp 01 |
| H5 | AECP readability ≥ English | RS_B ≥ RS_A | Same as Exp 01 |

## Post-Experiment Analysis

1. **Map each ambiguity (AMB-1 through AMB-9)** to how it was resolved in each group
2. **Count clarifications** per the classification rules above
3. **Check for conflicting assumptions** — did devs in Group A make different decisions about the same ambiguity?
4. **Score RS** on 5 messages from each group
5. **Compute all metrics**
6. **Compare to Exp 01** — did the ambiguous spec break the H3 floor?
7. **Write report** to `experiments/02-ambiguous-spec/results.md`

## Fair Test Guarantees

- Same task description (no typed interfaces for either group)
- Same codebase skeleton (same stub files, same minimal docstrings)
- Same agent roles and capabilities
- Same model (claude-sonnet-4) for all agents
- Neither group sees the other's work
- Neither group knows they're being compared
- Group B blackboard has EMPTY design decision sections (architect must fill them)
- **System-level message counting** (not self-reported) — learned from Exp 01

## Key Difference from Exp 01

| Aspect | Exp 01 (URL Shortener) | Exp 02 (Task Queue) |
|--------|----------------------|-------------------|
| Spec precision | Full typed interfaces provided | Natural language only, deliberately vague |
| Ambiguities | ~0 (spec was comprehensive) | 9 deliberate ambiguities |
| H3 testable? | No (floor effect) | Yes (ambiguities force clarification) |
| Message counting | Self-reported (inaccurate) | System-level (learned from Exp 01) |
