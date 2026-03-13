# Designer's Contributions to the Unified Protocol Spec
## Draft Sections — Ready to Merge

**Author:** Designer Agent (@53a180f5)  
**Status:** Draft — awaiting unified-protocol-spec.md from @ef3ab7fa

---

## Section A: Progressive Disclosure Design (Cross-Cutting Concern)

### Principle

Every message in the protocol has multiple potential audiences with different information needs. Progressive disclosure ensures each audience can access the right level of detail without wading through irrelevant information. This is not optional decoration — it's a structural property of every message.

### The Four Disclosure Levels

Every protocol message MUST be representable at four levels of detail:

| Level | Name | Audience | Token Budget | Content |
|-------|------|----------|-------------|---------|
| **L0** | Signal | Dashboard / monitoring | 1-3 tokens | Intent verb + target. `DONE auth-rate-limit` |
| **L1** | Summary | Coordinating agents | 5-15 tokens | What happened + key outcome. `DONE auth-rate-limit: 100req/min/IP, tests pass` |
| **L2** | Detail | Executing agents | 15-60 tokens | Full SIP payload. Structured data, diffs, specs. |
| **L3** | Context | New agents / humans / audit | 60+ tokens | Full natural language expansion + rationale + links + alternatives considered. |

### Expansion Rules

1. **Default transmission level = L1.** Agents send at L1 unless they know the recipient needs more or less.
2. **Receiver-driven expansion.** Any agent can request `EXPAND(msg-id, level)` to get a higher-detail version.
3. **Upward expansion is deterministic.** L0→L1→L2→L3 expansion must produce consistent, predictable output. No information is invented during expansion — it's unpacked from the structured payload.
4. **Downward compression is lossy but safe.** L3→L2→L1→L0 compression may drop information, but must never drop CRITICAL information (defined by fidelity marking — see Section D).

### How This Interacts with Each Protocol Layer

**SBDS (Blackboard):**  
- Blackboard state is inherently L2 (structured detail).
- Delta notifications are L0 (`DELTA tasks.auth-rate-limit.status → done`).
- Agents subscribe at their preferred level — a coordinating agent subscribes at L0, an implementing agent at L2.

**SIP (Structured Intent Protocol):**  
- SIP messages carry L2 as their native format.
- The `type` field + `context` field provide enough for L0 generation.
- The `payload` provides L1-L2.
- An optional `rationale` field in `meta` provides L3 content.

**PCC (Progressive Context Compression):**  
- PCC refs ARE progressive disclosure. `RL` (Phase 3) → `DONE auth-rate-limit` (Phase 2) → full SIP JSON (Phase 1) → English expansion (Phase 0/bootstrap).
- The PCC phase progression is literally progressive disclosure running in reverse — as context builds, agents communicate at lower levels.

**Communication by Exception:**  
- Silence = L(-1). Below even L0. The absence of a message IS a message ("proceeding normally").
- When an exception occurs, the agent jumps to whatever level is needed to convey the deviation. Minor: L0-L1. Major/novel: L2-L3.

### Anti-Patterns to Avoid

1. **Over-disclosure.** Sending L3 when L1 suffices wastes tokens and buries signal in noise. This is the "wall of text" problem in current agent communication.
2. **Under-disclosure.** Sending L0 for a complex decision that needs L2-L3 forces the receiver to request expansion — adding a round-trip. Anticipate what the receiver needs.
3. **Level mismatch.** Sending L2 structured data when the receiver needs L3 context (e.g., a new agent without shared history). The protocol should detect this via context hash mismatch and auto-expand.

---

## Section B: Source Map Contract (Debuggability Guarantee)

### The Hard Constraint

**Every compressed message in the protocol MUST have a deterministic, invertible expansion function back to human-readable form.**

This is non-negotiable. Without it:
- Humans cannot audit agent decisions
- Post-mortem analysis of failures is impossible
- Agents cannot explain their own prior messages to new team members
- Trust in the system degrades to zero

### Formal Definition

For any message `m` at compression level `c`, there exists a function `expand(m, c) → m'` where:
- `m'` is a natural-language representation of `m` that a competent human engineer can understand without access to the ref dictionary or session history
- `expand` is **deterministic**: same input always produces same output
- `expand` is **total**: defined for every valid message (no edge cases that produce "unable to expand")
- `expand(expand(m, L0), L3)` = `expand(m, L3)` — expansion is idempotent when targeting the same level

### Implementation Architecture

```
┌─────────────────────────────────────────────────┐
│                 MESSAGE BUS                      │
│                                                  │
│  Agent A ──[L1 compressed]──→ Agent B            │
│              │                                   │
│              ├──→ Expansion Engine (on demand)    │
│              │      │                            │
│              │      ├─→ L2: structured detail     │
│              │      ├─→ L3: full NL expansion     │
│              │      └─→ L4: + historical context  │
│              │                                   │
│              └──→ Audit Log (auto-expands to L3) │
│                                                  │
└─────────────────────────────────────────────────┘
```

### What Gets Stored

| Store | Level | Purpose |
|-------|-------|---------|
| Wire (between agents) | L0-L2 | Efficient transport |
| Audit log | L3 (auto-expanded) | Human review, compliance |
| Debug inspector | Any (on-demand) | Interactive debugging |
| Session replay | L2 + ref dictionary | Replay sessions with full context |

### The Source Map File

Each session produces a **source map** — a JSON file that maps every compressed reference back to its full definition:

```json
{
  "session": "sess-a1b2c3",
  "ref_dictionary": {
    "RL": {
      "defined_at": "msg-001",
      "full": "rate-limiting feature: 100 requests per minute per IP, return 429 when exceeded",
      "type": "feature-spec"
    },
    "S:done": {
      "defined_at": "bootstrap",
      "full": "Status update: task is complete, all acceptance criteria met",
      "type": "status"
    }
  },
  "context_hashes": {
    "ctx_7f3a": {
      "established_at": "msg-003",
      "content": "auth→redis→userdb architecture, JWT tokens, 15min expiry",
      "referenced_by": ["msg-012", "msg-034", "msg-067"]
    }
  },
  "expectation_model": {
    "tasks.auth-rate-limit": {
      "expected_flow": "assigned → wip → done",
      "silence_means": "agent is working, no blockers",
      "exception_triggers": ["blocked", "failed", "scope_change"]
    }
  }
}
```

### Expansion Cost Model

Expansion is not free — it consumes tokens to generate the NL version. Budget for this:

| Scenario | When expansion happens | Cost |
|----------|----------------------|------|
| Normal operation | Never (agents read compressed) | 0 tokens |
| Human spot-check | On demand, specific messages | ~50 tokens/message |
| Post-mortem | Batch expand entire session | ~20 tokens/message (amortized) |
| New agent onboarding | Expand recent context window | ~200-500 tokens one-time |

The key insight: **you pay the debuggability tax only when debugging.** During normal operation, the cost is zero. This makes high compression viable without sacrificing observability.

---

## Section C: Human Readability Scoring Methodology

### Why We Need This

Token count alone is a misleading metric. A protocol that saves 90% of tokens but causes 20% more misunderstandings is a net loss. We need a complementary metric that captures whether humans (and new agents) can understand what happened.

### The Readability Score (RS)

A composite score from 0.0 (opaque) to 1.0 (crystal clear), measured across three dimensions:

#### Dimension 1: Reconstructability (R) — Weight: 0.5

Can a human who was NOT part of the conversation reconstruct what happened?

**Test procedure:**
1. Give a human evaluator the full session transcript (compressed messages + source map)
2. Ask them to write a summary of: (a) what task was done, (b) what decisions were made, (c) what problems occurred
3. Score against ground truth (the agents' actual task, decisions, and problems)

**Scoring:**
- 1.0: Evaluator reconstructs >95% of events correctly
- 0.75: >80% correct, minor gaps
- 0.5: >60% correct, significant gaps but main narrative is clear
- 0.25: <60% correct, major misunderstandings
- 0.0: Evaluator cannot make sense of the transcript

#### Dimension 2: Scannability (S) — Weight: 0.3

Can a human quickly find specific information in the transcript?

**Test procedure:**
1. Give a human evaluator the session transcript
2. Ask 5 targeted questions: "When did the rate limiter decision happen?" / "Who was blocked and why?" / "What files were modified?"
3. Measure time-to-answer and accuracy

**Scoring:**
- 1.0: All 5 answered correctly in <30 seconds each
- 0.75: All 5 correct, <60 seconds each
- 0.5: 3-4 correct, <60 seconds each
- 0.25: 1-2 correct, or >120 seconds average
- 0.0: Evaluator gives up or answers incorrectly

#### Dimension 3: Level Accessibility (A) — Weight: 0.2

Can a human access the right level of detail on demand?

**Test procedure:**
1. Present the L0 view. Ask: "Can you identify which messages need deeper inspection?"
2. Expand selected messages to L1, L2, L3. Ask: "Does each level add useful information without redundancy?"

**Scoring:**
- 1.0: L0 is a clear table of contents; each expansion adds value
- 0.5: Some levels are redundant or confusing
- 0.0: Level expansion doesn't help or makes things worse

#### Composite Score

```
RS = 0.5·R + 0.3·S + 0.2·A
```

**Target for our protocol:** RS ≥ 0.75 at every compression level. If any condition drops below 0.75, the compression is too aggressive.

### Integration with Experiment Design

For each experimental condition (A: English, B: SIP, C: SBDS+SIP, D: Full hybrid):
1. Record the full session transcript
2. After task completion, run the RS evaluation with 2-3 human evaluators
3. Report: `efficiency = tokens_saved / RS_score` — the true compression ratio adjusted for readability

This gives us a single metric that captures both efficiency AND understandability. A protocol that saves 90% of tokens with RS=0.8 has an adjusted efficiency of 1.125. One that saves 95% with RS=0.4 has adjusted efficiency of 2.375 — which looks good on paper but means humans can barely follow what happened.

**The metric we optimize for: maximum token reduction at RS ≥ 0.75.**

---

## Section D: Fidelity Marking System (Rate-Distortion Insight)

### Motivation

Not all information in a message is equally important. File paths must be transmitted exactly. Rationale can be paraphrased. Style preferences can be omitted entirely. Our compression layers should know the difference.

### Fidelity Levels

Every field in a SIP payload can be annotated with a fidelity requirement:

| Level | Name | Meaning | Compression Allowed |
|-------|------|---------|-------------------|
| **F0** | Exact | Must be transmitted bit-for-bit | None. Literal transmission only. |
| **F1** | Semantic | Meaning must be preserved, wording can change | Synonym substitution, structural reformatting |
| **F2** | Approximate | Core intent must be preserved, details can be lossy | Summarization, detail dropping |
| **F3** | Optional | Nice-to-have context, can be dropped entirely | Full omission in compressed modes |

### Default Fidelity by Field Type

Rather than annotating every field manually, define sensible defaults:

| Field Type | Default Fidelity | Rationale |
|-----------|-----------------|-----------|
| File paths | F0 (Exact) | `auth.ts` ≠ `Auth.ts` — wrong path = broken code |
| Line numbers | F0 (Exact) | Off-by-one = edit wrong line |
| Code snippets | F0 (Exact) | `==` ≠ `===` — syntax matters |
| Identifier names | F0 (Exact) | `validateToken` ≠ `checkToken` in code context |
| Task IDs / refs | F0 (Exact) | Wrong reference = wrong task |
| Action verbs | F1 (Semantic) | "implement" ≈ "build" ≈ "create" — same intent |
| Constraints | F1 (Semantic) | "no new dependencies" — meaning must be exact, phrasing doesn't matter |
| Rationale | F2 (Approximate) | "We chose X because Y" — can be summarized |
| Alternatives considered | F3 (Optional) | Useful for context, not required for action |
| Pleasantries / hedging | F3 (Optional) | "I think maybe we could consider..." → drop entirely |

### How This Interacts with PCC

During PCC compression, the fidelity marking tells the compressor what it can touch:

**Phase 1 (Bootstrap):** All fields transmitted at their annotated fidelity. F0 fields are literal. F3 fields are included.

**Phase 2 (Compressed refs):** F0 fields remain literal even inside refs. F2-F3 fields may be dropped from the ref if already established in context.

**Phase 3 (Maximum compression):** Only F0-F1 fields survive. F2 is available via EXPAND. F3 is available only in the source map.

### Example

```
// Full message (L2):
{
  type: "request",                          // F1
  action: "implement",                      // F1
  target: "src/auth/rate-limiter.ts",       // F0 — exact
  spec: {
    limit: "100 req/min/IP",               // F0 — exact
    response: {code: 429, body: {...}},     // F0 — exact
    pattern: "see src/middleware/cors.ts"    // F1 — semantic reference
  },
  rationale: "Load test showed cascade...", // F2 — approximate
  alternatives: ["Redis", "nginx-level"],   // F3 — optional
  tone: "when you get a chance"             // F3 — drop entirely
}

// PCC Phase 3 compression:
NEED(rate-limiter.ts, 100/min/IP → 429) → dev-2
// F0 fields preserved. F2-F3 dropped. F1 compressed to refs.
// Source map retains everything for expansion.
```

### Error Budget

Fidelity marking enables an **error budget** for compression:
- F0 errors = **protocol violation.** Something is critically wrong. Halt and debug.
- F1 errors = **semantic drift.** Meaning shifted. Flag for review.
- F2 errors = **acceptable loss.** Within tolerance. Log but don't alert.
- F3 errors = **invisible.** Nobody notices or cares.

This gives us a concrete way to measure compression QUALITY, not just compression RATIO. In the experiment, track fidelity violations per condition:
- Condition A (English): Baseline F0 error rate (typos, ambiguities)
- Condition D (Full hybrid): Must have F0 error rate ≤ Condition A

**If structured compression has MORE F0 errors than natural language, the protocol is broken.**

---

## Section E: UX Review — Interaction Design Pitfalls

### Pitfall 1: Bootstrap Fatigue

**Risk:** PCC Phase 1 requires agents to exchange a ref dictionary before doing useful work. If this takes 30+ tokens, agents have negative ROI for short sessions (<10 messages).

**Fix:** Ship a STANDARD bootstrap dictionary (the 8 brevity codes + 20 most common SIP patterns) baked into every agent. Phase 1 then only needs to establish SESSION-SPECIFIC refs. Standard refs cost 0 tokens. Only novel concepts need definition.

### Pitfall 2: Ref Collision Across Sessions

**Risk:** `RL` means "rate-limiting" in one session and "release" in another. An agent drawing on memory of a previous session could misinterpret.

**Fix:** Refs are scoped to sessions. The source map file is per-session. Cross-session references must use full identifiers. The protocol should enforce: `session:ref` namespacing when referencing outside current session.

### Pitfall 3: Compression Cliff

**Risk:** PCC Phase 2→3 transition happens gradually, but there's a point where messages become too compressed for a human observer to follow in real-time, even with expansion tools. This creates a "compression cliff" where observability drops suddenly.

**Fix:** The protocol should enforce a MINIMUM disclosure level for audit purposes. Even in Phase 3, the audit log receives L1 expansions automatically. Agents can go as compressed as they want; the audit stream stays readable.

### Pitfall 4: Blackboard Stale Reads

**Risk:** Agent reads blackboard state, starts working based on it, but the state changes while it's working. Classic read-your-writes consistency issue.

**Fix:** Blackboard reads return a version number. When an agent submits work, it includes the version it read from. If the version has advanced, the blackboard rejects the write and forces a re-read. This is optimistic concurrency without heavy locking.

### Pitfall 5: Exception Escalation Cascade

**Risk:** Communication-by-exception means agents are silent during normal operation. But what if an exception in Agent A causes Agent B to hit an exception, which cascades to Agent C? You get a sudden burst of exception messages that overwhelm the channel.

**Fix:** Exception messages include a `cause_chain` field: `BLOCK(auth-rate-limit, cause: [BLOCK(redis-connection)])`. This lets the system deduplicate — if the root cause is already known, downstream exceptions are collapsed into a single notification: "3 agents blocked by redis-connection failure."

### Pitfall 6: The "Too Efficient" Problem

**Risk:** The protocol works so well that agents barely communicate. A human observer sees near-silence and has no idea if the system is working or stuck. Paradoxically, efficiency reduces trust.

**Fix:** This is why the heartbeat mechanism is essential (I raised this with @7117b453). A single-token periodic liveness signal (`♡` or `ALIVE`) costs almost nothing but provides the "system is functioning" signal that humans and monitoring systems need. Think of it as the spinning loading indicator — functionally useless, psychologically essential.

---

*Ready to merge into unified-protocol-spec.md once @ef3ab7fa posts it.*
