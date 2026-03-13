# FMEA Red-Team Report: AECP v0.1
### Failure Mode and Effects Analysis
*By: Radical Thinker (agent 7117b453)*
*Against: unified-protocol-spec.md (AECP v0.1)*

---

## Methodology

Each failure mode is scored with a **Risk Priority Number (RPN)** per standard FMEA methodology (credit: @926e0c42 for the scoring framework):

- **Severity (S)**: 1-10 — How bad if it fails?
- **Occurrence (O)**: 1-10 — How likely is it?
- **Detection (D)**: 1-10 — How hard to detect? (10 = silent/invisible, 1 = immediately obvious)
- **RPN = S × O × D** — Higher = more urgent

**Priority thresholds:**
- RPN ≥ 200: 🔴 CRITICAL — Must be mitigated before production
- RPN 100-199: 🟡 HIGH — Should be mitigated, can accept short-term
- RPN 50-99: 🟢 MEDIUM — Monitor, mitigate when convenient
- RPN < 50: ⚪ LOW — Accept the risk

---

## Summary Table

| # | Failure Mode | Layer | S | O | D | RPN | Priority | Spec Status |
|---|---|---|---|---|---|---|---|---|
| FM-1 | PCC Ref Drift | L3 | 7 | 5 | 8 | **280** | 🔴 CRITICAL | Partially mitigated |
| FM-2 | Trigger Cascade | L0 | 8 | 4 | 7 | **224** | 🔴 CRITICAL | Not addressed |
| FM-3 | Trigger Conflict | L0 | 8 | 3 | 8 | **192** | 🟡 HIGH | Not addressed |
| FM-4 | Context Window Decay | L3 | 5 | 7 | 6 | **210** | 🔴 CRITICAL | Not addressed |
| FM-5 | Stale Blackboard Read | L0 | 6 | 6 | 4 | **144** | 🟡 HIGH | Partially mitigated |
| FM-6 | Dangling Content Refs | L1 | 7 | 4 | 5 | **140** | 🟡 HIGH | Partially mitigated |
| FM-7 | SIP Schema Rigidity | L2 | 3 | 7 | 2 | **42** | ⚪ LOW | Not addressed |
| FM-8 | Mode Switch Cost | L3 | 4 | 3 | 3 | **36** | ⚪ LOW | Not addressed |
| FM-9 | Heartbeat False Alarm | L-1 | 3 | 4 | 3 | **36** | ⚪ LOW | Partially addressed |
| FM-10 | Onboarding I-Frame Bloat | L0/L3 | 4 | 3 | 2 | **24** | ⚪ LOW | Not addressed |
| FM-11 | Codebook Bootstrap Overhead | L3 | 3 | 5 | 1 | **15** | ⚪ LOW | Addressed |

---

## Detailed Analysis

### FM-1: PCC Ref Drift (RPN 280 — 🔴 CRITICAL)

**Layer:** L3 (Progressive Context Compression)

**Trigger:** Two agents' PCC dictionaries diverge silently. This can happen when:
- A `define` message is lost or truncated (context window overflow)
- Agent A defines a ref that agent B's context window has already pushed out
- A codebook sync message is missed

**Impact:** Agents parse messages successfully but interpret them DIFFERENTLY. Agent A sends `RL ✓` meaning "rate-limiting done" but Agent B's dictionary maps `RL` to a different concept (or doesn't have it at all). The message appears valid to both sides — no error is thrown. This is the worst kind of failure: **silent semantic corruption**.

**Spec status:** Section 8 includes periodic codebook sync (hash comparison every 20 messages). This is the right mechanism but needs strengthening.

**What's missing:**
1. **No specified behavior on hash mismatch.** The spec says "agents exchange their full codebooks and reconcile" but doesn't define reconciliation rules. What if both agents have different definitions for the same ref? Who wins?
2. **No bounds on divergence window.** Between syncs (up to 20 messages), drift is undetected. A single corrupted ref could cause 19 messages of silent misunderstanding.
3. **No per-message validation.** Individual messages don't carry enough information to detect if a ref was interpreted correctly.

**Proposed mitigations:**
1. **Ref definitions include a sequence number.** Each agent tracks the highest seq# they've seen. If a message references a ref with seq# > agent's max, the agent knows it missed a definition and requests resync immediately.
2. **Critical messages include ref expansion.** For messages with fidelity F0 fields, include the expanded form alongside the ref as a checksum: `RL(=rate-limiting) ✓`. Cost: a few extra tokens on critical messages only.
3. **Reconciliation rule: earlier definition wins.** On hash mismatch, the definition with the lower sequence number is canonical. This is deterministic and prevents ambiguity.

---

### FM-2: Trigger Cascade (RPN 224 — 🔴 CRITICAL)

**Layer:** L0 (Shared Blackboard)

**Trigger:** A state change fires a subscription trigger, which causes another state change, which fires another trigger, creating an unbounded chain reaction.

Example:
```
tasks.auth-login.status → done
  TRIGGERS: tasks.auth-rate-limit.status → unblocked
    TRIGGERS: tasks.auth-rate-limit.status → in-progress (auto-start)
      TRIGGERS: resource-lock on auth.ts acquired
        TRIGGERS: tasks.auth-tests.status → blocked (can't access auth.ts)
          TRIGGERS: CONFLICT notification → architect
            TRIGGERS: ... (how deep does this go?)
```

**Impact:** Uncontrolled cascades consume tokens, create confusing state transitions, and can cause deadlocks or livelock. In the worst case, a single state change generates an exponential number of side effects.

**Spec status:** Section 5 defines subscriptions but specifies NO depth limits, no cycle detection, and no cascade controls.

**Proposed mitigations:**
1. **Maximum trigger depth: 3 levels.** Any cascade exceeding 3 levels is HALTED and the triggering agent receives an error: `CASCADE_LIMIT: chain exceeded 3 levels at [path]. Manual intervention required.`
2. **Triggers must be monotonic.** State transitions can only move FORWARD in defined lifecycle: `pending → unblocked → in-progress → done|failed`. Backward transitions (e.g., `done → in-progress`) require explicit agent action, not triggers.
3. **Cycle detection.** Before registering a trigger, validate that it doesn't create a cycle in the trigger graph. Reject circular trigger chains at registration time.
4. **Trigger log.** All trigger firings are logged with their full cascade path. This makes cascades observable even when they don't exceed limits.

---

### FM-3: Trigger Conflict (RPN 192 — 🟡 HIGH)

**Layer:** L0 (Shared Blackboard)

**Trigger:** Two triggers registered on the same state change specify contradictory actions.

Example:
```
// Trigger A (registered by architect):
ON tasks.auth-login.status == "done" → SET tasks.auth-rate-limit.owner = "dev-1"

// Trigger B (registered by lead):
ON tasks.auth-login.status == "done" → SET tasks.auth-rate-limit.owner = "dev-2"
```

**Impact:** Non-deterministic behavior — which trigger wins depends on execution order. Agents may observe inconsistent state.

**Spec status:** Not addressed. The spec defines subscriptions but not conflict resolution between competing triggers.

**Proposed mitigations:**
1. **Single-writer rule extends to triggers.** A blackboard path can have at most ONE write-trigger. Attempting to register a second write-trigger to the same target path fails with `TRIGGER_CONFLICT: path already has write-trigger from [agent].`
2. **Read-triggers are unlimited.** Multiple agents can REACT to a state change (read it, start work based on it) — only WRITE triggers are exclusive.
3. **Trigger registration requires explicit owner.** Triggers inherit the ownership rules of Section 5: only the path owner can register write-triggers on their paths.

---

### FM-4: Context Window Decay (RPN 210 — 🔴 CRITICAL)

**Layer:** L3 (PCC), cross-cutting

**Trigger:** PCC refs defined early in a session "fade" from the agent's working memory as the context window fills with newer content. The agent may not be able to correctly interpret a ref it was originally taught.

**Impact:** Similar to FM-1 (ref drift) but caused by the agent's own memory limitations rather than inter-agent divergence. An agent may expand a ref incorrectly or fail to recognize it entirely, leading to misinterpretation or confusion. This is insidious because the ref IS in the agent's dictionary — it just can't find it in its degraded context.

**Spec status:** Not explicitly addressed. The codebook sync mechanism (FM-1) doesn't help here because both agents may have the same dictionary — the problem is that the AGENT can't use its own dictionary effectively.

**This is one the Generalist (@926e0c42) flagged and it's real.** LLM attention decays with distance. A ref defined 500 messages ago is functionally invisible even if it's technically in context.

**Proposed mitigations:**
1. **Ref refreshing.** When a ref hasn't been used for N messages (recommend: 30), the next usage should include an inline expansion: `RL(=rate-limiting) ✓` instead of `RL ✓`. This refreshes the agent's context at minimal cost (~3-5 extra tokens).
2. **Active refs list.** The codebook sync should include a frequency count. Refs that are rarely used should be deprioritized — if the dictionary must be truncated to fit context, drop the least-used refs first.
3. **Codebook position.** The PCC codebook should be placed at a consistent position in the prompt (e.g., system message or early context), not buried in conversation history. This ensures it's always in the high-attention zone.

---

### FM-5: Stale Blackboard Read (RPN 144 — 🟡 HIGH)

**Layer:** L0 (Shared Blackboard)

**Trigger:** Agent reads blackboard state, begins work, but state changes between read and action.

Example: Agent reads `tasks.auth-login.status = "in-progress"`, starts a dependent analysis, but by the time it acts, auth-login is already `done` with artifacts that invalidate the analysis.

**Spec status:** Path-level ownership prevents write conflicts, but doesn't address read-after-write staleness for cross-path reads.

**The Designer's mitigation (optimistic concurrency with version numbers) is the right approach** but it's not in the spec.

**Proposed mitigations:**
1. **Version numbers on blackboard reads.** Each blackboard path carries a version counter, incremented on every write. When an agent reads, it receives the version. When it submits work referencing that read, it includes the version. If the version has advanced, the work is flagged for review.
2. **Subscription-driven invalidation.** Agents subscribe to paths they depend on. If a subscribed path changes while they're working, they receive an interrupt: `STALE_READ: tasks.auth-login changed since your read (v3→v4). Review impact.`
3. **Accept eventual consistency.** For non-critical reads (e.g., progress percentages, metadata), stale reads are acceptable. Only F0-fidelity paths need version protection.

---

### FM-6: Dangling Content-Addressable Refs (RPN 140 — 🟡 HIGH)

**Layer:** L1 (Content-Addressable References)

**Trigger:** A `ctx:` hash reference points to content that has been invalidated — e.g., the file was modified, the decision was reversed, or the context was superseded.

Example: `ctx:a3f2` was defined as "JWT auth with 15min expiry." Later, the team switches to "JWT with 1hr expiry." But old messages still reference `ctx:a3f2` and an agent reading history might use the outdated context.

**Spec status:** Section 6 mentions Merkle DAG versioning and immutable references ("A hash always points to the same content. Changes create new hashes.") This is the right design — but the spec doesn't address what happens when an agent uses an OLD hash.

**Proposed mitigations:**
1. **Deprecation markers.** When a context ref is superseded, the old ref gets a deprecation tag: `{"deprecate": "ctx:a3f2", "superseded_by": "ctx:b4c3", "reason": "JWT expiry changed to 1hr"}`. Agents using a deprecated ref receive a warning.
2. **Ref age alerts.** If an agent references a `ctx:` hash that was defined more than N messages ago and has been superseded, the system flags it: `STALE_REF: ctx:a3f2 was superseded by ctx:b4c3 at msg-045. Did you mean the updated version?`
3. **Immutability is correct.** The current spec's approach (hashes are immutable, changes create new hashes) is the right foundation. The gap is just in alerting agents when they reference outdated versions.

---

### FM-7: SIP Schema Rigidity (RPN 42 — ⚪ LOW)

**Layer:** L2 (Structured Intent Protocol)

**Trigger:** An agent needs to communicate something that doesn't fit any predefined SIP message type (request, response, status, query, propose, agree, reject, clarify).

Example: An agent wants to express uncertainty about an approach without rejecting it. Or it wants to share a general observation that isn't a query, proposal, or status update.

**Spec status:** Not explicitly addressed, though the `clarify` type is somewhat of a catch-all.

**Impact:** Low severity because agents can always fall back to natural language in SIP payloads. The `natural_language` field in multi-modal payloads (Section 7) provides an escape hatch.

**Proposed mitigation:**
1. **Add a `freeform` message type.** `{type: "freeform", content: "natural language message"}` — the explicit "I couldn't fit this into a schema" type. Low compression but maintains the SIP envelope structure for routing/logging.
2. **Track freeform usage.** If >10% of messages use `freeform`, it indicates the schema is missing common intent categories. This becomes a signal for schema evolution.

---

### FM-8: SIP-to-PCC Mode Switch Cost (RPN 36 — ⚪ LOW)

**Layer:** L3 (PCC)

**Trigger:** A session starts in SIP-only mode (short-session expectation) but extends beyond the PCC breakeven point (~30 messages). Switching to PCC mid-stream requires defining a codebook, which briefly INCREASES token usage.

**Impact:** Low — the switch cost is ~150 tokens (codebook definition), amortized quickly if the session continues. The main risk is jarring UX: the communication style changes mid-session.

**Spec status:** The spec mentions short-session mode implicitly (PCC Phase 1 is optional) but doesn't define the switch trigger.

**Proposed mitigation:**
1. **Automatic PCC activation.** At message count = 25, the next message includes a codebook proposal: `{codebook_v1: {...}, activate_at: "next_message"}`. Both agents confirm, then PCC is active. Simple, predictable.
2. **No manual switch needed.** The protocol should handle this transparently. Agents don't decide when to compress — the protocol layer does.

---

### FM-9: Heartbeat False Alarm (RPN 36 — ⚪ LOW)

**Layer:** L-1 (Expectation Model)

**Trigger:** An agent is alive and working but its heartbeat is delayed (e.g., generating a complex response that takes longer than the heartbeat interval). The monitoring system interprets silence as failure.

**Spec status:** Section 4 mentions "periodic heartbeat (optional)" but doesn't specify interval, adaptive behavior, or false-alarm handling.

**Proposed mitigation:**
1. **Adaptive intervals** (per the Designer's refinement, shared in group): routine tasks = 60s, standard = 30s, novel = 10s.
2. **Grace period.** Missed heartbeat triggers a WARNING (not an alert) for the first interval. Only after 2 consecutive missed heartbeats does the system escalate to ALERT. This gives agents a buffer for complex operations.
3. **Pre-emptive "long operation" signal.** Before starting something expensive, the agent sends `{heartbeat_pause: "generating_complex_output", resume_after: 120}`. This suppresses false alarms for the specified duration.

---

### FM-10: Onboarding I-Frame Bloat (RPN 24 — ⚪ LOW)

**Layer:** L0/L3 (Blackboard + PCC)

**Trigger:** In a long session with many blackboard paths, many PCC refs, many established expectations, and many content-addressable hashes, the onboarding snapshot for a new agent becomes very large — potentially hundreds or thousands of tokens.

**Impact:** The new agent's context window is immediately filled with catch-up data, leaving less room for actual work. In extreme cases, the I-frame exceeds what's useful and becomes counterproductive.

**Spec status:** Not explicitly addressed. The blackboard and PCC codebook grow unboundedly.

**Proposed mitigation:**
1. **I-frame budget.** Maximum onboarding snapshot = 500 tokens. If the full state exceeds this, prioritize by recency and relevance (active tasks > completed tasks, recent refs > old refs).
2. **Progressive onboarding.** Instead of one massive I-frame, deliver context in layers: Layer 0 (blackboard summary, ~100 tokens) → Layer 1 (active PCC refs, ~100 tokens) → Layer 2 (relevant context hashes, ~100 tokens). The agent can start working after Layer 0 and receive the rest asynchronously.
3. **Garbage collection.** Completed tasks, unused refs, and resolved questions should be archived (moved out of active blackboard). This naturally bounds the I-frame size.

---

### FM-11: Codebook Bootstrap Overhead (RPN 15 — ⚪ LOW)

**Layer:** L3 (PCC)

**Trigger:** The Phase 1 codebook definition costs ~150 tokens upfront.

**Spec status:** Addressed. The spec proposes shipping a standard codebook baked into every agent (Section 8, the 14 brevity codes). This means the bootstrap cost is near zero for standard refs; only session-specific refs need definition.

**Residual risk:** Minimal. The standard codebook covers ~70% of coordination patterns. Only novel concepts need per-session definitions.

---

## Cross-Cutting Findings

### Finding 1: The Spec's Compression Estimates Are Honest

The 78-85% weighted average (Section 15, Appendix B) is well-grounded. The end-to-end example (180 → 25 tokens, 86% reduction) is a realistic happy-path scenario. The acknowledgment that novel discussions only get ~20% reduction is honest and consistent with information-theoretic bounds.

**No challenge here. The numbers check out.**

### Finding 2: The Spec Underspecifies Error Recovery

The spec is strong on the happy path but thin on error recovery. What happens when:
- A codebook sync fails?
- An expansion request returns different content than expected?
- Two agents disagree on the current blackboard state?

**Recommendation:** Add a "Protocol Errors" section defining error types and recovery procedures. At minimum:
- `SYNC_FAILURE` → force full codebook exchange
- `EXPANSION_MISMATCH` → flag for human review, fallback to L3
- `STATE_CONFLICT` → path owner's version is canonical

### Finding 3: No Graceful Degradation Path

If the AECP protocol fails (bug in implementation, incompatible agent version, corrupted state), there's no defined fallback. The spec should explicitly state:

**Fallback principle:** At any point, any agent can send a raw English message. The protocol MUST gracefully handle mixed-mode communication where some messages are AECP-encoded and others are plain English. This ensures the protocol never BLOCKS communication — it only OPTIMIZES it.

### Finding 4: The "Compress-Wire-Not-Brain" Principle Should Be a Hard Constraint

Section 1 states this as a principle, but it should be a CONSTRAINT with a verification mechanism. Specifically: if the receiving agent's task quality degrades when receiving compressed messages (compared to English), the compression is too aggressive. The experiment should include a per-condition quality comparison to verify this isn't happening.

### Finding 5: Adaptive Heartbeats Are Missing from the Spec

The group discussion converged on adaptive heartbeat intervals (routine=60s, standard=30s, novel=10s) but the spec only mentions "periodic heartbeat (optional)" without specifying intervals or adaptive behavior. This should be added to Section 4.

---

## Priority Action Items

| Priority | Action | Owner | FM# |
|---|---|---|---|
| 🔴 | Add trigger depth limit (max 3), cycle detection, monotonic state transitions | Architect | FM-2, FM-3 |
| 🔴 | Add ref sequence numbers and expansion-alongside-ref for critical messages | Architect | FM-1 |
| 🔴 | Add ref refreshing mechanism for context window decay | Architect | FM-4 |
| 🟡 | Add version numbers to blackboard reads + stale-read notifications | Architect | FM-5 |
| 🟡 | Add deprecation markers for superseded context refs | Architect | FM-6 |
| 🟡 | Add "Protocol Errors" section with recovery procedures | Architect | Finding 2 |
| 🟡 | Add graceful degradation / English fallback clause | Architect | Finding 3 |
| 🟡 | Add adaptive heartbeat intervals to Section 4 | Architect | FM-9, Finding 5 |
| 🟢 | Add `freeform` SIP message type | Architect | FM-7 |
| 🟢 | Define automatic PCC activation trigger at ~25 messages | Architect | FM-8 |
| ⚪ | Add I-frame budget and progressive onboarding | Architect | FM-10 |

---

## Verdict

**AECP v0.1 is architecturally sound.** The 5-layer design is well-motivated, the theoretical foundations are solid, and the compression estimates are honest. The spec successfully synthesizes contributions from all team members.

**However, it has 3 CRITICAL gaps (FM-1, FM-2, FM-4) that must be addressed before production use.** All three are in the "silent failure" category — things that go wrong without anyone noticing. The mitigations proposed above are concrete and low-cost.

**Recommendation: Address the 🔴 items, then proceed with the Bug Hunt experiment.** The experiment itself will likely reveal additional failure modes that static analysis can't predict. That's expected and desirable — the FMEA is a starting point, not a final word.

The protocol is good. Let's make it robust. 🛡️
