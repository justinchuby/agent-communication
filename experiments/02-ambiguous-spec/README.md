# Experiment 02: Ambiguous Spec — Task Queue Library

## Purpose

Follow-up to Experiment 01 (URL Shortener A/B Test). Tests **H3 (clarification reduction)** which was inconclusive in Exp 01 due to a floor effect — both groups had 0 clarifications because the typed interface specs eliminated ambiguity.

## Design

Same 5v5 setup as Exp 01 but with **deliberately vague natural-language requirements**. No typed interfaces. No Python protocol definitions. Ambiguities force agents to coordinate and clarify.

## Hypothesis

- **Group A (English)**: 3-5 clarification requests as agents encounter ambiguities
- **Group B (AECP)**: 0-1 clarifications because the blackboard forces the architect to resolve ambiguities in writing before devs start

## Task

Build a Python **task queue library** with priority scheduling, retry logic, and status tracking. See `task-description.md` for the deliberately ambiguous spec.

## Deliberate Ambiguities (5)

1. **Priority behavior**: "higher priority tasks should run first" — but is priority 1 highest or priority 10 highest?
2. **Retry policy**: "failed tasks should be retried" — how many times? What backoff? What counts as "failed"?
3. **Task timeout**: "tasks shouldn't run forever" — what's the default timeout? What happens on timeout?
4. **Concurrent execution**: "the queue should support running multiple tasks" — thread pool? async? How many workers?
5. **Status transitions**: "tasks go through several stages" — which stages? What transitions are valid?

## Files

- `task-description.md` — The ambiguous spec
- `group-a-rules.md` — English control
- `group-b-rules.md` — AECP treatment
- `blackboard-b.md` — Group B shared state
- `measurement.md` — Metrics with H3 focus
- `execution-playbook.md` — Agent creation instructions
- `group-a-code/` / `group-b-code/` — Identical stubs
