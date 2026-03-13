# A/B Test Measurement Framework

## Experiment Design

- **Independent variable**: Communication protocol (English vs AECP)
- **Dependent variables**: See metrics below
- **Control group (A)**: 5 agents, English communication, no constraints
- **Treatment group (B)**: 5 agents, AECP rules, blackboard, structured messages
- **Held constant**: Task description, codebase skeleton, agent roles, agent models

## Primary Metrics

### 1. Token Efficiency
- **total_tokens_exchanged**: Sum of all tokens in all messages (both groups)
- **message_count**: Number of GROUP_MESSAGE + AGENT_MESSAGE calls
- **tokens_per_message**: Average message length in tokens
- **measurement**: Count from system logs post-experiment

### 2. Coordination Overhead
- **clarification_requests**: Messages asking for info that was already available
- **redundant_messages**: Messages restating known info (acknowledgments, summaries)
- **coordination_ratio**: (clarification + redundant) / total messages
- **measurement**: Manual classification of each message post-experiment

### 3. Task Success
- **tests_passing**: X/18 tests passing at completion
- **code_quality**: Reviewer's verdict (pass/fail per file, issues found)
- **completeness**: All 4 code files implemented (boolean)
- **measurement**: Run pytest, count results

### 4. Time to Completion
- **wall_clock_time**: Time from task start to final test pass
- **agent_turns**: Number of conversational turns per agent
- **measurement**: Timestamps from system logs

## Secondary Metrics

### 5. Error Rate
- **bugs_introduced**: Defects found during review/testing
- **bugs_fixed**: Defects resolved before final test run
- **rework_cycles**: Number of review→fix→re-review loops

### 6. Information Flow
- **messages_before_first_code**: How many messages before implementation starts
- **design_phase_tokens**: Tokens spent on design coordination alone
- **idle_waiting**: Time agents spent blocked waiting for info

## Scoring Rubric

### Readability Score (RS) — Applied to Both Groups
Sample 5 messages from each group. Score each on:
- **R (Reconstructability)**: Can a new agent understand the full meaning? (0.0-1.0)
- **S (Scannability)**: Can the key info be extracted in <5 seconds? (0.0-1.0)
- **A (Actionability)**: Does the message make clear what action is needed? (0.0-1.0)
- **RS = 0.5R + 0.3S + 0.2A**
- Target: RS ≥ 0.75 for both groups

### Efficiency Score
- **ES = (1 - tokens_B/tokens_A) × 100** — Percentage token reduction
- **Adjusted ES = ES × (RS_B / RS_A)** — Penalize if readability drops

## Hypotheses

| ID | Hypothesis | Metric | Predicted |
|----|-----------|--------|-----------|
| H1 | AECP reduces total tokens | total_tokens | B < 0.4 × A |
| H2 | AECP reduces message count | message_count | B < 0.5 × A |
| H3 | AECP reduces clarifications | clarification_requests | B < 0.3 × A |
| H4 | Task success is equal | tests_passing | A = B = 18/18 |
| H5 | AECP readability ≥ English | RS score | RS_B ≥ RS_A |
| H6 | AECP reduces time | wall_clock_time | B ≤ 0.8 × A |
| H7 | AECP reduces rework | rework_cycles | B < A |

## Post-Experiment Analysis

1. **Collect all messages** from both groups (system logs)
2. **Classify each message**: informational, request, acknowledgment, decision, verdict
3. **Score RS** on 5-message sample from each group
4. **Compute all metrics** in the tables above
5. **Test hypotheses** H1-H7
6. **Qualitative analysis**: What worked? What broke? Surprising behaviors?
7. **Write final report** to `.flightdeck/shared/ab-test/results.md`

## Fair Test Guarantees

- Same task description given to both groups (task-description.md)
- Same codebase skeleton (same stub files, same docstrings)
- Same agent roles and capabilities
- Same model powering all agents
- Neither group sees the other's work
- Neither group knows they're being compared
- Group A code in `group-a-code/`, Group B code in `group-b-code/`
