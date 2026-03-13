# AECP: Agent-Efficient Communication Protocol

**Structured communication protocols reduce inter-agent token usage by 70–97% while improving task success rates and eliminating clarification overhead.**

This repository contains the complete research output from a multi-agent investigation into efficient agent-to-agent communication. The core finding: natural language between AI agents is an anti-pattern — like two databases communicating via PDF printouts and OCR. AECP defines a layered protocol stack that replaces free-form English with structured intent envelopes, shared blackboards, progressive compression, and content-addressable references.

---

## Key Results

| Condition | Protocol Layers | Tokens | Messages | Clarifications | Savings |
|-----------|----------------|--------|----------|----------------|---------|
| A | Baseline English | 1,168 | 19 | 3 | — |
| B | SIP only | 280 | 9 | 0 | **76%** |
| C | SBDS + SIP | 151 | 5 | 0 | **87%** |
| D | Full stack (SBDS+SIP+PCC+exceptions) | 59 | 4 | 0 | **95%** |
| E | Full + content-addressing | 31 | 3 | 0 | **97%** |

All conditions achieved task success on the same bug-hunt scenario. See [Final Report](research/final-report.md) for full analysis.

---

## Documentation

### Specification

| Document | Description |
|----------|-------------|
| [Unified Protocol Spec](spec/unified-protocol-spec.md) | The complete AECP v0.3 specification — 5-layer protocol stack with SIP, SBDS, PCC, communication-by-exception, and content-addressable references |
| [Experiment Design](spec/experiment-design.md) | Experimental methodology for comparing 5 communication conditions across the bug-hunt task scenario |
| [Protocol Proposals](spec/protocol-proposals.md) | Initial protocol design proposals and the core thesis against natural language inter-agent communication |

### Research

| Document | Description |
|----------|-------------|
| [Final Report](research/final-report.md) | Complete research findings, experimental results, and conclusions from the AECP investigation |
| [Executive Brief](research/executive-brief.md) | One-page summary of AECP for stakeholders — key findings, protocol overview, and recommendations |
| [Theoretical Foundations](research/theoretical-foundations.md) | Information-theoretic grounding — rate-distortion bounds, Kolmogorov complexity, and Shannon entropy analysis of agent communication |
| [Cross-Disciplinary Insights](research/cross-disciplinary-insights.md) | What linguistics, biology, semiotics, and distributed systems teach us about efficient information transfer |

### Analysis

| Document | Description |
|----------|-------------|
| [FMEA Report](analysis/fmea-report.md) | Failure Mode and Effects Analysis — red-team assessment of AECP v0.1 identifying risks, failure modes, and mitigations |
| [Communication Patterns](analysis/communication-patterns.md) | Interaction design analysis — UX patterns, progressive disclosure, and human-readability considerations |
| [Initial Ideas](analysis/initial-ideas.md) | First-principles radical analysis — "The Absurdity of Agents Speaking English" and alternative paradigms |

### Design

| Document | Description |
|----------|-------------|
| [Spec Sections Draft](design/spec-sections-draft.md) | Designer's contributions to the unified spec — progressive disclosure, source maps, fidelity marking |
| [UX Review Notes](design/ux-review-notes.md) | UX review of AECP v0.1 with 9 actionable findings for human debuggability and developer experience |

### Experiment

| Path | Description |
|------|-------------|
| [run_experiment.py](experiment/run_experiment.py) | Experiment runner — loads condition logs and produces comparison tables |
| [measure.py](experiment/measure.py) | Measurement framework — token estimation, clarification detection, multi-condition analysis |
| [bug-hunt-codebase/](experiment/bug-hunt-codebase/) | Mini Python project with a planted cross-file bug (dict/list type mismatch) used as the experiment task |
| [conditions/](experiment/conditions/) | Message logs for all 5 experimental conditions showing realistic agent communication |

---

## Running the Experiment

```bash
# View the comparison table
python docs/experiment/run_experiment.py --brief

# See detailed per-message breakdown
python docs/experiment/run_experiment.py

# Run the bug-hunt tests (5 of 13 should fail)
cd docs/experiment/bug-hunt-codebase && python -m pytest test_pipeline.py -v
```

---

## Protocol Stack (AECP v0.3)

```
Layer  Name                          Purpose
─────  ────────────────────────────  ────────────────────────────────────
  -1   Expectation Model             Communication by exception only
   0   Shared Blackboard (SBDS)      Persistent shared state, path-level ownership
   1   Content-Addressable Refs      Hash-based context references
   2   Structured Intent (SIP)       JSON message envelopes with intent codes
   3   Progressive Compression (PCC) Learned abbreviations bootstrapped from SIP
```

---

## Contributors

This research was produced by a multi-agent team: Project Lead, Architect, Designer, Radical Thinker, Generalist, and Developer — coordinating via the very communication patterns they were studying.

> *"This session itself is Condition A of our own experiment. Next time, let's dogfood AECP v1."* — Architect
