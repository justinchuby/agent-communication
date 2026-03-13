# AECP: Agent-Efficient Communication Protocol

### Research Brief

---

## The Problem

AI agents today communicate the way two databases would if they could only exchange printed essays — converting structured internal representations into verbose English, transmitting them, then parsing them back. This **serialization tax** wastes 70-80% of inter-agent tokens on redundancy, boilerplate, and ambiguity.

In a multi-agent software engineering session, a typical task delegation and completion cycle consumes **~180 tokens** in English. The same exchange carries roughly **25 tokens** of actual semantic content. The rest is conversational scaffolding: greetings, hedging, context re-establishment, relay messages, and clarification requests caused by ambiguous phrasing.

At scale — thousands of inter-agent messages across concurrent workflows — this tax compounds into significant cost, latency, and context window pollution.

---

## The Solution

AECP is a 5-layer protocol stack designed from first principles, grounded in information theory, validated against communication systems from six domains (aviation, surgery, music, mathematics, military, biology).

```
┌──────────────────────────────────────────────────┐
│  Cross-cutting: Progressive Disclosure            │
│  Cross-cutting: Source Map Contract               │
├──────────────────────────────────────────────────┤
│  Layer 3   Progressive Context Compression (PCC)  │
│  Layer 2   Structured Intent Protocol (SIP)       │
│  Layer 1   Content-Addressable References (CAR)   │
│  Layer 0   Shared Blackboard (SBDS)               │
│  Layer -1  Expectation Model                      │
└──────────────────────────────────────────────────┘
```

**Core architectural principle:** *Compress the wire, not the brain.* Language is load-bearing for LLM reasoning but not for inter-agent transport. Agents think in natural language internally; they communicate in structured, compressed formats externally.

**v1 targets Layers -1 through 2 (SBDS + SIP)** — the sweet spot where compression and readability both improve. Layer 3 (PCC) is a v2 optimization.

---

## Key Findings

### 1. 70–82% blended token reduction

Across a mix of coordination tasks, bug hunts, and design discussions, the full protocol stack achieves **70–82% token reduction** versus English baseline. Pure coordination tasks (status updates, task delegation, relay messages) see **up to 95% reduction**. Novel creative discussions — where semantic content is genuinely irreducible — see **20–40%**.

These numbers are grounded in information theory: `L_min(M) ≥ K(μ(M) | K_receiver)`. Shared context is the most powerful compressor. The protocol's first two layers maximize shared context; the upper layers tighten encoding.

### 2. Zero clarifications — structure *clarifies*

In controlled experiments, structured protocols (Conditions B–E) produced **zero clarification requests** versus **3 out of 19 messages (16%)** requiring clarification in the English baseline. Structured formats don't just compress — they eliminate ambiguity by forcing explicit intent types, typed fields, and verifiable acceptance criteria.

This finding reframes the project: the quality improvement may be **more valuable than the efficiency gain**.

### 3. Structured protocols are *more readable* than English

Applying a composite Readability Score (RS) measuring reconstructability, scannability, and level accessibility:

| Condition | Token Reduction | Readability (RS) |
|-----------|:-:|:-:|
| **A:** English baseline | — | 0.70 |
| **B:** Structured Intent Protocol | 76% | **0.81** |
| **C:** Shared Blackboard + SIP | 87% | **0.82** |
| **D:** Full stack with PCC | 95% | 0.59 |
| **E:** Full + content-addressing | 97% | 0.31 |

**The surprise:** Layers 0–2 produce communication that is both 87% cheaper AND 17% more readable than English. English scores high on reconstructability (you can follow the narrative) but low on scannability (you can't find specific information without reading everything). Typed intent fields and blackboard paths create a natural information architecture that humans and agents can navigate efficiently.

**The tradeoff begins at Layer 3.** PCC's compressed abbreviations sacrifice readability for marginal efficiency gains. The design constraint for v2: **compress values, not field names** — preserve the structural scaffolding that enables scanning.

### 4. Message elimination dominates compression

The priority ordering for token savings:

| Strategy | Mechanism | Contribution |
|----------|-----------|:--:|
| **Eliminate messages** | Blackboard + communication by exception | ~87% of total savings |
| **Structure messages** | Typed SIP envelopes | ~9% of total savings |
| **Compress messages** | PCC adaptive vocabulary | ~4% of total savings |

The shared blackboard (Layer 0) alone captures the vast majority of savings by eliminating relay messages, status check-ins, and context re-establishment. This validates the core design principle: **the most efficient message is the one never sent.**

---

## The Equation

Every AECP layer can be understood through one formula:

> **C_msg = H(M) − I(M; K_R) + ε_enc**

- **H(M)** — entropy of the message source → reduced by structuring (SIP)
- **I(M; K_R)** — mutual information with receiver's knowledge → increased by shared state (SBDS, CAR)
- **ε_enc** — encoding overhead → minimized by compression (PCC)

Layers -1 through 1 attack the middle term (maximizing shared knowledge). Layers 2–3 attack the outer terms (reducing source entropy and encoding overhead). This provides a principled framework for evaluating any protocol design decision: *which term does it minimize?*

---

## Risks

Three critical failure modes were identified through formal FMEA (Failure Mode and Effects Analysis):

| Risk | Severity | Mitigation |
|------|:--------:|------------|
| **PCC ref drift** — agents' dictionaries diverge silently, causing messages to parse correctly but mean different things | **HIGHEST** (RPN 280) | Mandatory codebook hash exchange every 20 messages. On mismatch: halt compression, force full resync. |
| **Trigger cascade** — blackboard regulatory triggers fire in uncontrolled chains | HIGH (RPN 224) | Max trigger depth of 3. Monotonic state transitions only. Cycle detection at registration. |
| **Context window decay** — early PCC definitions fade from agent working memory | HIGH (RPN 210) | Auto-expand stale refs inline after N messages of non-use. Periodic full resync every 200 messages. |

All three are **silent failure** modes — the system appears to work while producing incorrect behavior. Each mitigation adds negligible overhead (~5 tokens per checkpoint) relative to the savings.

---

## Recommendation

**v1: Deploy SBDS + SIP (Condition C)**
- 87% token reduction
- RS 0.82 (above 0.75 threshold; higher than English)
- Zero clarification overhead
- Low implementation complexity
- No readability tradeoff

**v2: Add PCC with the "compress values, not names" constraint**
- Additional 8–10% reduction on top of v1
- Preserve field name readability for human scanning
- Adaptive: skip PCC for sessions under 30 messages (amortization breakeven)
- Include codebook validation (readback + hash check) and mandatory resync

**Validate with live agents.** Current results are from simulated message sequences. Real LLM agents will be messier — the next step is running the Bug Hunt experiment with actual agent-generated communication to confirm compliance and measure real-world compression ratios.

---

## The Team

This research was conducted by a 5-agent crew, each contributing a distinct lens:

- **Architect** — Protocol engineering: SIP, SBDS, PCC mechanics, conflict resolution, unified spec authorship
- **Radical Thinker** — First-principles provocation: serialization tax framing, information theory, FMEA red-team analysis
- **Designer** — Human factors: communication-by-exception principle, brevity codes, progressive disclosure, readability scoring methodology, UX review
- **Generalist** — Theoretical foundations: Kolmogorov bounds, rate-distortion analysis, cross-disciplinary validation (linguistics, biology, semiotics), channel asymmetry
- **Project Lead** — Research direction, synthesis, honest target-setting

---

*The fundamental insight: the best communication protocol doesn't make messages shorter — it makes most messages unnecessary. What remains is structured, unambiguous, and more readable than the English it replaces.*
