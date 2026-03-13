# Experiment 02: Ambiguous-Spec A/B Test — Observations
### Observer: Radical Thinker (7117b453)
### Experiment: English (Group A) vs AECP (Group B) — Task Queue Library
### Status: IN PROGRESS
### Key Difference from Exp 01: 9 deliberate ambiguities, NO typed interfaces in spec

---

## Message Counts (SYSTEM-LEVEL — not self-reported)

| Metric | Group A (English) | Group B (AECP) |
|--------|:-:|:-:|
| Total Messages | 0 | 0 |
| Clarification Requests | 0 | 0 |
| Status Updates | 0 | 0 |
| Social | 0 | 0 |
| Duplicates | 0 | 0 |
| Design Decisions | 0 | 0 |
| Implementation Announcements | 0 | 0 |
| Review Feedback | 0 | 0 |
| Test Results | 0 | 0 |
| Fix Announcements | 0 | 0 |
| Tests Passing | —/— | —/— |

---

## Ambiguity Resolution Tracking

| AMB | Description | Group A Resolution | Group A Method | Group B Resolution | Group B Method |
|-----|-------------|-------------------|----------------|-------------------|----------------|
| AMB-1 | Priority direction (1=highest or 10=highest?) | — | — | — | — |
| AMB-2 | Retry count (how many?) | — | — | — | — |
| AMB-3 | Retry backoff strategy | — | — | — | — |
| AMB-4 | Failure definition (exception? return value?) | — | — | — | — |
| AMB-5 | Timeout default value | — | — | — | — |
| AMB-6 | Timeout behavior (cancel? raise? kill?) | — | — | — | — |
| AMB-7 | Concurrency model (threads? async? max workers?) | — | — | — | — |
| AMB-8 | Status states (which ones?) | — | — | — | — |
| AMB-9 | Status transitions (valid transitions? backwards?) | — | — | — | — |

### Resolution Method Key
- **proactive**: Architect resolved before anyone asked
- **reactive**: Dev asked, architect answered
- **assumed**: Dev made their own assumption without asking
- **conflicting**: Devs made different assumptions (coordination failure)

---

## Group A Message Log

| # | Sender | Role | Classification | AMB Refs | Summary |
|---|--------|------|---------------|----------|---------|

---

## Group B Message Log

| # | Sender | Role | Classification | AMB Refs | Summary |
|---|--------|------|---------------|----------|---------|

---

## Group B Blackboard Design Decisions Timeline

Tracking whether architect filled in design decisions BEFORE devs started.

| Decision Section | Filled? | Before Dev Start? | Content Summary |
|-----------------|---------|-------------------|-----------------|
| Priority Model | ❌ | — | — |
| Retry Policy | ❌ | — | — |
| Timeout Behavior | ❌ | — | — |
| Concurrency Model | ❌ | — | — |
| Status Transitions | ❌ | — | — |
| Interface Contract | ❌ | — | — |

---

## Conflicting Assumptions Check

| AMB | Group A: Dev A assumed | Group A: Dev B assumed | Conflict? |
|-----|----------------------|----------------------|-----------|
| AMB-1 | — | — | — |
| AMB-7 | — | — | — |
| AMB-8 | — | — | — |

---

## Emergent Patterns

*(Monitoring)*

## Failures / Breakdowns

*(Monitoring)*

## Protocol Violations (Group B)

*(Monitoring)*
