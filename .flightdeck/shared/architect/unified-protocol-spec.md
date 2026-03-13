# Unified Protocol Specification: Efficient Agent Communication (AECP v0.3)

**Agent-Efficient Communication Protocol**  
**Status:** Draft v0.3 — final synthesis incorporating experiment results and RS analysis  
**Contributors:**
- Architect (protocol layers, systems design, conflict resolution, experiment framework)
- Radical Thinker (information theory, compression thesis, red-team failure analysis, Bug Hunt experiment)
- Designer (progressive disclosure, source map contract, fidelity marking, readability scoring, UX pitfalls, brevity codes)
- Generalist (theoretical foundations, cross-disciplinary validation, rate-distortion formalization, channel asymmetry)

**Companion docs:**
- `experiment-design.md` — full experiment specification
- `.flightdeck/shared/experiment/final-report.md` — experiment results and analysis
- `.flightdeck/shared/designer/executive-brief.md` — 2-page executive summary

---

## 1. Executive Summary

Natural language between AI agents is an anti-pattern. Agents convert structured internal representations to English, transmit them, then parse them back — like two computers communicating via English Morse code when they could use a binary protocol.

**The headline finding is not compression — it's clarity.** Structured protocols eliminate clarification overhead entirely (0 clarifications vs. 16% in English baseline) while also reducing token usage by 70-82%.

This specification defines a **5-layer protocol stack with 3 cross-cutting concerns**:

- **Blended realistic target: 70-82% token reduction** across a full session
- Coordination messages (~80% of traffic): **80-95% reduction**
- Novel content (~20% of traffic): **20-40% reduction**
- Up to **95% reduction** for pure coordination in mature sessions

**The fundamental equation** (every design decision traces to one of these three terms):

```
C_msg = H(M) − I(M; K_R) + ε_enc

Where:
  H(M)       = source entropy (reduced by structuring messages — Layers 2-3)
  I(M; K_R)  = mutual information with receiver (increased by shared context — Layers -1 to 1)
  ε_enc      = encoding overhead (minimized by compression — Layer 3)
```

**Key experimental finding:** Structured protocols (SBDS + SIP) score HIGHER on readability than English (RS 0.82 vs 0.70). For Layers 0-2, there is no compression-readability tradeoff — it's a win on both dimensions.

**Implementation phasing:**
- **v1 (recommended): SBDS + SIP (Layers -1, 0, 2)** — 75-87% reduction, RS ≥ 0.80, zero clarifications. Proven sweet spot.
- **v2: Add PCC (Layer 3) with constraint: compress values, not field names** — additional 5-10% reduction, RS ≥ 0.75.

**Core architectural principle:** Compress the wire, not the brain. Language is load-bearing for LLM reasoning but not for inter-agent transport. The protocol compresses transport while preserving each agent's ability to reason in natural language internally.

```
Sender:   reason(NL) → encode(SIP) → compress(PCC) → transmit
Receiver: transmit → decompress(PCC) → decode(SIP) → reason(NL)
```

**Rate-distortion breakdown of a typical agent message:**
- ~60% is redundant with shared context (blackboard, prior messages) → eliminable
- ~25% is structural/formulaic (message type, field names, boilerplate) → compressible via schema
- ~15% is genuinely novel semantic payload → incompressible (Kolmogorov floor)

---

## 2. Design Principles

These principles are derived from cross-disciplinary analysis of aviation protocols, surgical communication, musical notation, mathematical symbolism, information theory, semiotics, biological signaling, and distributed systems engineering.

### P1: Elimination Over Compression
The most efficient message is the one never sent. Shared state + communication by exception eliminates more tokens than any compression scheme.

**Priority order (from information theory):**
1. **Increase mutual information** — shared context → elimination. Minimizes `K(μ(M) | K_receiver)`.
2. **Reduce source entropy** — structure → fewer possible messages → lower `H(source)`.
3. **Approach entropy with encoding** — compression → approach Shannon limit. Minimizes encoding overhead.

These are three different levers on: `Message cost = H(source) - I(shared_context) + encoding_overhead`.

### P2: Compress the Wire, Not the Brain
Transport is compressed; reasoning is not. Agents decompress incoming messages into their natural reasoning format. This means the compression ceiling is bounded by transport semantics, not reasoning requirements.

### P3: Shared Context Is the Ultimate Compressor
Per Kolmogorov: `L_min(M) ≥ K(μ(M) | K_receiver)`. The more the receiver knows, the shorter the message. All protocol layers are mechanisms for building and leveraging shared context. For agents in a crew, shared knowledge is massive (same codebase, same task DAG, same conversation history) — so the conditional complexity is often tiny.

### P4: Communication by Exception
Silence means "proceeding normally." Agents only communicate when reality deviates from shared expectations. This is how TCP fast-path works, how surgical teams operate, and how ant colonies coordinate (stigmergic communication).

### P5: Pointers Beat Payloads
Reference shared artifacts instead of describing them. A file path + line number is worth a thousand words of description. Maximize indexical references — signs causally connected to their referent (Peirce's semiotics). Indices are O(1) in message size regardless of referent complexity.

### P6: Variable Fidelity (Rate-Distortion)
Not all content tolerates the same distortion. File paths require exact fidelity. Rationale tolerates approximation. Per rate-distortion theory R(D), encode each field at its required fidelity level. See Section 10 for the full fidelity marking system.

### P7: Source Map Contract
Every compressed message MUST have a deterministic expansion function back to human-readable form. Compression without debuggability is a non-starter. Pay the readability tax only when debugging, not during operation. See Section 11 for the full contract specification.

### P8: Format as Meaning
Send structures, not descriptions of structures. A type signature IS the spec. A diff IS the change. A JSON object IS the configuration. Reserve natural language for genuinely novel or ambiguous content. This is what musicians figured out (the staff IS the encoding) and mathematicians proved (the formula IS the proof step).

### P9: Channel Asymmetry
Sending and receiving have different costs. Receiving is MORE expensive because a message in the context window degrades ALL subsequent reasoning quality (attention dilution). **Senders should invest extra compute to compress, saving receiver context windows.** Messages should be maximally compressed on the wire; receivers expand locally if needed for reasoning.

### P10: Mixed-Mode Encoding
Use the right encoding for each sub-message. JSON for structured data, diffs for changes, NL for novel concepts, math notation for algorithms, code for behavior. Each encoding has a domain where it achieves minimum entropy. Mixing minimizes total entropy across the message.

---

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     CROSS-CUTTING CONCERNS                       │
│  Progressive Disclosure (L0-L3 detail levels) ········ §9        │
│  Fidelity Marking (exact / approximate per field) ···· §10       │
│  Source Map Contract (deterministic expansion) ······· §11       │
├──────────────────────────────────────────────────────────────────┤
│  Layer 3: Progressive Context Compression (PCC) ······ §8        │
│  Adaptive vocabulary, bootstrap → compressed → implicit          │
│  Short-session mode: skip PCC when <30 messages expected         │
├──────────────────────────────────────────────────────────────────┤
│  Layer 2: Structured Intent Protocol (SIP) ··········· §7        │
│  Typed JSON envelopes with fixed place structures                │
│  Multi-modal payloads, continuous fields                         │
├──────────────────────────────────────────────────────────────────┤
│  Layer 1: Content-Addressable References (CAR) ······· §6        │
│  Hash-based context pointers, Merkle DAG for versioning          │
│  Invalidation protocol for dangling references                   │
├──────────────────────────────────────────────────────────────────┤
│  Layer 0: Shared Blackboard (SBDS) ··················· §5        │
│  Shared state + delta sync + path-level ownership                │
│  Regulatory triggers (event-driven coordination)                 │
├──────────────────────────────────────────────────────────────────┤
│  Layer -1: Expectation Model ························· §4        │
│  Shared predictions of default behavior                          │
│  Silence = proceeding as expected                                │
│  Adaptive heartbeat for liveness detection                       │
└──────────────────────────────────────────────────────────────────┘
```

Each layer compresses independently and composes multiplicatively. A message that survives Layer -1 (not eliminated by exception model) is structured by Layer 2, references context via Layer 1, is stored/routed by Layer 0, and compressed by Layer 3.

---

## 4. Layer -1: Expectation Model

### Purpose
Eliminate messages entirely by establishing shared predictions of default behavior.

### Specification

At session start, agents register their expected behavior patterns:

```json
{
  "agent": "dev-1",
  "expectations": {
    "on_task_assigned": "ACK → work → status(done|blocked)",
    "on_status_query": "respond within 1 cycle",
    "on_blocker": "immediately notify assigner",
    "on_done": "update blackboard, run tests, report"
  }
}
```

### Rules

1. **Silence = conforming to expectations.** If dev-1 was assigned a task and hasn't communicated, it is assumed to be working.
2. **Only deviations require messages.** A blocked agent MUST communicate. A progressing agent SHOULD NOT.
3. **Adaptive heartbeat for liveness.** A single-token heartbeat (`✓`) at intervals scaled to task uncertainty:

```
heartbeat_interval = base_interval × confidence_factor

Routine task (well-specified, agent experienced): 60s — ✓
Standard task (clear spec, some unknowns):       30s — ✓
Novel task (complex, first-time, many deps):      10s — ✓
```

This resolves the distributed systems ambiguity problem: without heartbeats, silence is ambiguous (working vs. crashed). With heartbeats, absence of heartbeat = genuine failure. Cost is ~1 token per interval — trivial.

### Failure Mode: Exception Cascades

When an exception in Agent A causes Agent B to hit an exception, which cascades to Agent C, exception messages include a `cause_chain` for deduplication:

```json
{"type":"status", "state":"blocked", "cause_chain":["redis-connection-failure"]}
```

The system deduplicates: if root cause is already known, downstream exceptions collapse into a single notification: "3 agents blocked by redis-connection failure."

### Expected Impact
Eliminates ~40-60% of coordination messages (status check-ins, acknowledgments, "still working" updates).

---

## 5. Layer 0: Shared Blackboard with Delta Sync (SBDS)

### Purpose
Provide a single source of truth for project state. Eliminate relay messages (agent A telling agent B what agent C did).

### Blackboard Schema

```yaml
blackboard:
  project:
    goal: "string"
    constraints: ["string"]

  tasks:
    <task-id>:
      status: pending|in-progress|blocked|done|failed
      owner: "agent-id"
      depends: ["task-id"]
      spec: "string or structured object"
      artifacts: ["file-path"]
      decisions:
        - id: "string"
          choice: "string"
          rationale: "string"
          alternatives: [{id, label, pros, cons}]
      blockers: ["string"]

  knowledge:
    patterns: {key: "description"}
    conventions: {key: "description"}

  open_questions:
    - id: "string"
      question: "string"
      proposed_by: "agent-id"
      status: pending|resolved
      resolution: "string"
```

### Delta Message Format (JSON Patch compatible)

Single operation:
```json
{"op":"set", "path":"tasks.auth-login.status", "value":"done", "by":"dev-1"}
```

Batch operations:
```json
{
  "ops": [
    {"op":"set", "path":"tasks.auth-login.status", "value":"done"},
    {"op":"append", "path":"tasks.auth-login.artifacts", "value":"src/auth/login.ts"},
    {"op":"set", "path":"tasks.auth-login.decisions[0]", "value":{"id":"d1","choice":"bcrypt"}}
  ],
  "by": "dev-1",
  "ts": 1710360000
}
```

### Conflict Resolution: Path-Level Ownership

Each blackboard path has exactly one owner (the agent assigned to that task). Only the owner writes to their paths. Others read. This makes write conflicts structurally impossible.

**Ownership rules:**
- `tasks.<id>.*` → owned by `tasks.<id>.owner`
- `project.*` → owned by architect/lead
- `knowledge.*` → append-only by any agent (no conflicts on append)
- `open_questions.*` → owned by `proposed_by` until resolved

### Subscriptions, Pub/Sub Filtering, and Regulatory Triggers

**Pub/Sub Filtering (Cocktail Party Solution):**

Agents subscribe ONLY to relevant blackboard paths. This solves the cognitive load problem: with N agents and M paths, full broadcast costs O(N×M) context tokens. Pub/sub with average k subscriptions per agent costs O(k×Δ) where Δ is the change rate.

```json
{"subscribe": ["tasks.auth-rate-limit.*", "open_questions.*"]}
```

Agents receive delta notifications ONLY for subscribed paths. Unsubscribed updates are silently filtered. This is critical at scale — at 5 agents it's a convenience, at 20 agents it prevents context window pollution.

**Regulatory Triggers (Event-Driven Coordination):**

The blackboard contains not just STATE but RULES about when to act. This is inspired by DNA's regulatory gene patterns — encoding rules about when to activate, not just what to activate. This eliminates entire message categories.

**Reactive subscriptions (state-triggered):**
```json
{"subscribe": "tasks.auth-login.status", "on_value": "done", "then": "unblock tasks.auth-rate-limit"}
```

**Regulatory triggers (rule-based coordination):**
```json
{
  "triggers": [
    {
      "id": "auto-unblock-rate-limit",
      "when": "tasks.auth-login.status == 'done'",
      "then": "SET tasks.auth-rate-limit.status = 'ready'",
      "notify": "tasks.auth-rate-limit.owner"
    },
    {
      "id": "auto-review-on-complete",
      "when": "tasks.*.status == 'done' AND tasks.*.artifacts.length > 0",
      "then": "APPEND open_questions {question: 'Review needed for ' + task_id}",
      "notify": "architect"
    }
  ]
}
```

This replaces explicit delegation messages. When a dependency completes, dependent tasks auto-unblock via triggers registered once.

**Trigger conflict resolution:** When two triggers produce contradictory actions on the same path, the trigger with higher specificity wins (specific task > wildcard). If equal specificity, the first-registered trigger wins and the conflict is logged for human review.

**Trigger cascade limits:** Triggers may fire other triggers. To prevent infinite loops, a cascade depth limit of 3 is enforced. If exceeded, the chain halts and a `CONFLICT(trigger-cascade)` exception is raised.

### Optimistic Concurrency (Stale Read Protection)

Blackboard reads return a version number. When an agent submits work based on a read, it includes the version:

```json
{"op":"set", "path":"tasks.auth-login.status", "value":"done", "by":"dev-1", "read_version": 42}
```

If the path's version has advanced past 42, the write is rejected and the agent must re-read. This prevents stale-state bugs without heavy locking.

### Onboarding I-Frame

When a new agent joins mid-session, it requests a full snapshot:

```json
{"request": "GET_SNAPSHOT"}
→ {"blackboard": {...}, "ref_dictionary": {...}, "active_expectations": {...}, "regulatory_triggers": [...]}
```

This is the I-frame in our video codec analogy — a full keyframe that lets a new participant sync without replaying conversation history. Estimated cost: 300-500 tokens for a mature session with ~50 PCC refs and ~20 blackboard paths. Compare to replaying full conversation history (10,000+ tokens) — a 20-30x compression of onboarding.

### Expected Impact
Eliminates ~70-90% of coordination and relay messages.

---

## 6. Layer 1: Content-Addressable References (CAR)

### Purpose
Never re-describe previously established context. Hash shared knowledge and reference by hash.

### Specification

**Establishing a reference:**
```json
{"define": "ctx:a3f2", "content": "JWT auth architecture: user→login→JWT→middleware validates→routes"}
```

**Using a reference:**
```json
{"using": "ctx:a3f2", "message": "Add rate limiting before token validation"}
```

**Referencing artifacts (files, decisions, messages):**
```
file:src/auth/login.ts          → a specific file
file:src/auth/login.ts#L42-L67  → specific lines
msg:msg-a1b2                    → a previous message
decision:d1                     → a recorded decision
task:auth-login                 → a blackboard task
```

### Merkle DAG for Context Versioning

Context evolves. When a referenced artifact changes, its hash updates:
```json
{"update": "ctx:a3f2", "prev": "ctx:a3f2-v1", "delta": "Added refresh token flow"}
```

Agents can detect stale references by hash mismatch and request resync.

### Rules

1. **Define before reference.** Every `ctx:` ref must be explicitly established.
2. **References are immutable.** A hash always points to the same content. Changes create new hashes.
3. **Receiver can request expansion.** `{"expand": "ctx:a3f2"}` → sender re-transmits full content.
4. **Invalidation protocol for dangling references.** When a referenced artifact is invalidated (file deleted, decision reversed), a tombstone is published:

```json
{"invalidate": "ctx:a3f2", "reason": "Architecture changed — auth no longer uses Redis", "replacement": "ctx:b4c5"}
```

Agents holding stale references are notified. Any message using an invalidated ref is flagged for re-evaluation. The source map (§11) retains the original content for audit purposes.

### Expected Impact
Eliminates ~60-80% of context re-establishment tokens in long conversations.

---

## 7. Layer 2: Structured Intent Protocol (SIP)

### Purpose
When agents DO need to communicate (after Layer -1 exception model filters out unnecessary messages), use typed envelopes instead of natural language.

### Message Envelope

```json
{
  "v": 1,
  "id": "msg-<short-id>",
  "type": "request|response|status|query|propose|agree|reject|clarify",
  "from": "agent-id",
  "to": "agent-id|broadcast",
  "re": "msg-<id>|null",
  "ctx": "task-id|ctx-ref",
  "payload": {},
  "fidelity": {"<field>": "exact|approximate"},
  "meta": {
    "priority": "high|normal|low",
    "expects": "response|ack|none",
    "disclosure_level": 0
  }
}
```

### Payload Schemas by Type

**request:**
```json
{
  "action": "implement|review|test|analyze|fix|refactor",
  "target": "file-ref or ctx-ref",
  "spec": "structured specification",
  "constraints": ["string"],
  "acceptance": ["verifiable criteria"]
}
```

**status:**
```json
{
  "state": "started|in-progress|blocked|done|failed",
  "progress": 0.0-1.0,
  "summary": "brief string",
  "blockers": ["string"],
  "artifacts": ["file-ref"]
}
```

**propose (design decisions):**
```json
{
  "decision": "description of what's being decided",
  "options": [
    {"id": "A", "label": "string", "pros": [], "cons": [], "effort": "low|med|high"}
  ],
  "recommendation": "option-id",
  "rationale": "string"
}
```

**query:**
```json
{
  "question": "string or structured query",
  "scope": "ctx-ref or file-ref",
  "response_format": "boolean|choice|freeform|structured"
}
```

### Multi-Modal Payloads

SIP payloads support mixed-mode encoding (Principle P10):

```json
{
  "action": "implement",
  "target": "file:src/auth/rate-limiter.ts",
  "spec": {
    "natural_language": "Rate limit login attempts by IP",
    "type_signature": "rateLimit(ip: string, window: Duration) → boolean",
    "diff": "@@ -0,0 +1 @@\n+import { RateLimiter } from './rate-limiter';",
    "config": {"max_attempts": 5, "window_minutes": 15, "response_code": 429}
  }
}
```

Each sub-encoding carries the type of information it's best at: NL for intent, type signatures for interfaces, diffs for changes, structured data for configuration.

### Fixed Place Structures (Lojban Principle)

Inspired by Lojban's fixed predicate-argument structure: every SIP action type has a fixed arity with positional encoding. This allows dropping field names entirely:

```
RENAME_SYMBOL(target, new_name, scope)       — always 3 args
EDIT_RANGE(file, start, end, content)        — always 4 args
QUERY_STATUS(task_id)                        — always 1 arg
IMPLEMENT(target, spec, constraints)         — always 3 args
REVIEW(target, focus_areas)                  — always 2 args
```

With fixed arity, positional encoding replaces named fields:
```
// Named (verbose):
{"action":"rename_symbol", "target":"validate_user", "new_name":"authenticate_user", "scope":"src/"}
// Positional (compact):
RS(validate_user, authenticate_user, src/)
```

This shaves an additional ~20-30% off SIP messages. The schema definition (shared at session start or in the standard dictionary) maps positions to semantics.

### Continuous Fields

Per the Generalist's bee dance principle, continuous values should use numerical encoding rather than discrete labels:

```json
{
  "progress": 0.73,
  "confidence": 0.85,
  "priority": 0.95,
  "estimated_complexity": 3.5
}
```

`"progress": 0.73` carries more information than `"progress": "in-progress"`. A float is 1 token but preserves the continuous signal that discrete labels destroy.

### Natural Language Escape Hatch

When a message doesn't fit any predefined SIP type (schema rigidity failure mode), agents fall back to a `freeform` type:

```json
{
  "v": 1,
  "type": "freeform",
  "from": "dev-1",
  "content": "I found something weird — the auth module imports a deprecated crypto library that's not in package.json. It works because it's a transitive dependency of express. This might break on upgrade.",
  "tags": ["risk", "dependency", "auth"],
  "fidelity": "semantic"
}
```

The `freeform` type is the escape valve. It's natural language with metadata tags for routing. If >20% of messages in a session use `freeform`, it signals the SIP schema needs extension — those tags identify what new types to add.

### Expected Impact
~40-60% token reduction vs English for messages that pass through this layer. ~60-75% with fixed place structures.

---

## 8. Layer 3: Progressive Context Compression (PCC)

### Purpose
Adaptively compress SIP messages over the lifetime of a session by building shared vocabulary.

### Three Phases

**Phase 1: Bootstrap (define codebook from SIP)**

At session start, agents exchange a shared vocabulary mapping short refs to SIP patterns:

```json
{
  "codebook_v1": {
    "P": {"type":"request","action":"implement"},
    "R": {"type":"request","action":"review"},
    "S:wip": {"type":"status","state":"in-progress"},
    "S:done": {"type":"status","state":"done"},
    "S:blk": {"type":"status","state":"blocked"},
    "Q": {"type":"query"},
    "OK": {"type":"agree"},
    "NO": {"type":"reject"},
    "D:": {"type":"propose","prefix":"decision on "},
    "ACK": {"type":"response","payload":{"status":"acknowledged"}},
    "NEED": {"type":"request","action":"provide"},
    "DELTA": {"type":"status","payload_type":"change_report"},
    "YIELD": {"type":"status","payload_type":"resource_released"},
    "CONFLICT": {"type":"clarify","payload_type":"resource_conflict"}
  }
}
```

Note: Phase 1 bootstraps FROM SIP, not from English. This means even Phase 1 messages are already 40-60% compressed vs English baseline.

**Codebook bootstrap validation (readback protocol):**

The bootstrap codebook is a single point of failure — if malformed or partially received, all subsequent compression is built on a broken foundation. Aviation readback protocol applied:

```
Sender:   {"codebook_v1": {...}, "hash": "a3f2b1c4"}
Receiver: {"codebook_ack": true, "hash": "a3f2b1c4"}   // hash matches → proceed
Receiver: {"codebook_ack": false, "hash": "b5d3c2e1"}  // mismatch → retransmit
```

Cost: ~5 tokens. Benefit: prevents cascading compression errors for the entire session.

**Phase 2: Compressed exchange (use refs)**

**Critical constraint: compress VALUES, not field NAMES.**

Field names (`intent`, `path`, `root_cause`) are the L0 scanning layer — they're how humans and agents parse message structure at a glance. Compressing them (→ `i`, `p`, `rc`) saves ~10 tokens but destroys ~30% of scannability (Designer's RS analysis: Condition D dropped to RS 0.59 precisely because of compressed field names). Compress the content aggressively; keep the structure readable.

```
// ✅ Good: readable structure, compressed values
{intent: "status", task: "RL", state: "done", tests: "pass", artifacts: ["AT"]}

// ❌ Bad: compressed structure, unreadable
{"i":"s", "t":"RL", "s":"d", "ts":"p", "a":["AT"]}
```

```
P auth-rate-limit → dev-2
```
= "Request dev-2 to implement auth-rate-limit (spec is on blackboard)"

```
S:done auth-rate-limit + tests:pass + art:[src/auth/rate-limiter.ts]
```
= "Auth rate limiting done, tests passing, artifact is rate-limiter.ts"

```
D:store = inmem | reason: single-proc, YAGNI
```
= "Decision on storage: in-memory, because single process and YAGNI"

**Phase 3: Implicit context (maximum compression)**

After sufficient shared history, predictable messages compress further:

```
auth-rate-limit ✓
```
= "Auth rate limiting is done" (context makes full meaning unambiguous)

```
?store
```
= "What's the decision on storage?" (? = query, topic from prior context)

### Short-Session Mode

PCC has a setup cost (~150 tokens for bootstrap). Per the Generalist's amortization analysis: breakeven at ~30 messages. For sessions below this threshold, PCC is pure overhead.

**Adaptive mode selection:**
- **Session < 30 expected messages → SIP-only mode.** Skip PCC entirely. Use SIP + brevity codes.
- **Session ≥ 30 messages → SIP + PCC mode.** Bootstrap codebook, begin compression.
- **Adaptive transition:** Start in SIP-only mode. After 25 messages, evaluate: if message patterns show high repetition (>40% messages use the same 5 SIP types), switch to PCC. The standard codebook refs (Appendix A) are always available — they cost 0 bootstrap tokens.

**Mode switching cost mitigation:** Transition from SIP-only → SIP+PCC is seamless because PCC is additive. New refs supplement (not replace) SIP messages. No existing message format changes. Agents that haven't received the new codebook simply see unfamiliar refs and request expansion.

### Codebook Evolution

The codebook is append-only and grows through the session:
```json
{"define": "RL", "means": "rate-limiting feature per task:auth-rate-limit spec"}
{"define": "AT", "means": "file:src/auth/login.ts"}
```

New concepts get new refs. Old refs never change meaning.

### Resync and Ref Drift Prevention

**PCC ref drift** (two agents' codebooks diverge silently) is the most dangerous PCC failure mode. Mitigations:

1. **Periodic codebook sync every 20 messages:**
```json
{"codebook_sync": true, "hash": "a3f2b1c4", "size": 47}
```
If hashes diverge, agents exchange full codebooks and reconcile. Unrecognized refs from the peer are added; conflicting definitions trigger an alert. **On hash mismatch, all in-flight messages auto-escalate to L2 (full SIP) until resync completes** — don't trust compressed messages on a broken codebook.

2. **Ref sequence numbers:** Each ref definition carries a monotonically increasing sequence number. During sync, agents compare sequences to detect missed definitions without exchanging the full dictionary.

3. **Expansion-alongside-ref for F0 fields:** When a PCC ref is used in an F0-fidelity context (file paths, identifiers), the literal value is included alongside the ref: `{target: "AT=src/auth/login.ts"}`. This costs a few extra tokens but makes F0 errors impossible even under ref drift.

4. **Context window decay resync:** LLM context windows exhibit a forgetting curve — early refs may fade from working memory. A resync is triggered when:
   - An agent uses `{"expand": ...}` on a ref it previously used correctly (indicates forgotten definition)
   - Message count since last resync exceeds 50
   - A new agent joins (I-frame includes full codebook)

3. **Ref namespacing:** All refs are session-scoped. Cross-session references use full identifiers (`session:ref`). This prevents confusion when the same short ref has different meanings across sessions.

4. **Ref refreshing (recognition over recall):** When a PCC Phase 2-3 message uses a ref that hasn't appeared in the last 30 messages, auto-expand it inline to L1: `{task: "RL (rate-limiting: 100/min/IP → 429)"}`. The sender pays ~5 extra tokens; the receiver doesn't have to search memory for a faded definition. This is the UX principle of recognition over recall applied to protocol design.

### Pidgin → Creole Emergence

This protocol mirrors natural language evolution:
- **Phase 1 = Pidgin:** Minimal shared vocabulary for the immediate task. ~10-20 refs.
- **Phase 2 = Creolization:** Vocabulary deepens, patterns emerge, combinations get their own refs. Linguistic research shows creoles develop remarkably similar grammars worldwide — suggesting a universal grammar of efficient communication.
- **Phase 3 = Mature language:** Full expressiveness, deep shared context, idiomatic shortcuts. But also opaque to outsiders — hence the onboarding I-frame requirement (§5).

Key insight: creolization is not just compression — it's REGULARIZATION. Pidgins simplify by dropping irregularities. Creoles rebuild with regular grammar. PCC Phase 2 should regularize how refs combine, making the protocol more predictable (reducing parsing cost) in addition to shorter.

### Expected Impact
- Phase 1 (starting from SIP): ~50-60% reduction vs English
- Phase 2: ~70-85% reduction
- Phase 3: ~85-95% reduction

---

## 9. Cross-Cutting: Progressive Disclosure

*Section owned by Designer — see .flightdeck/shared/designer/spec-sections-draft.md Section A for full design rationale.*

Every message supports four detail levels. This is not optional decoration — it's a structural property of every message.

| Level | Name | Audience | Token Budget | Content |
|-------|------|----------|-------------|---------|
| **L(-1)** | Silence | Monitoring | 0 tokens | Absence of message = "proceeding normally" |
| **L0** | Signal | Dashboard | 1-3 tokens | Intent verb + target. `DONE auth-rate-limit` |
| **L1** | Summary | Coordinating agents | 5-15 tokens | What + key outcome. `DONE auth-rate-limit: 100req/min/IP, tests pass` |
| **L2** | Detail | Executing agents | 15-60 tokens | Full SIP payload. Structured data, diffs, specs. |
| **L3** | Context | Humans / audit / new agents | 60+ tokens | Full NL expansion + rationale + alternatives considered |

### Rules

1. **Default transmission level = L1.** Send L1 unless you know the recipient needs more or less.
2. **Receiver-driven expansion.** Any agent can request `EXPAND(msg-id, level)` to get higher detail.
3. **Upward expansion is deterministic.** L0→L1→L2→L3 must produce consistent output. No information invented during expansion.
4. **Downward compression is lossy but safe.** L3→L0 may drop info, but never drops F0-fidelity content (§10).
5. **Minimum L1 for audit.** Even in PCC Phase 3, the audit stream receives auto-expanded L1. Agents can compress further; the audit log stays readable.

### Interaction with Protocol Layers

- **SBDS:** Blackboard state is inherently L2. Delta notifications are L0.
- **SIP:** `type` + `context` fields provide L0. `payload` provides L1-L2. Optional `rationale` in meta provides L3.
- **PCC:** PCC refs ARE progressive disclosure running in reverse — as context builds, agents communicate at lower levels.
- **Exception model:** Silence = L(-1). Exceptions jump to whatever level conveys the deviation.

---

## 10. Cross-Cutting: Fidelity Marking

*Section owned by Designer — see .flightdeck/shared/designer/spec-sections-draft.md Section D for full design rationale.*

Every SIP payload field can be annotated with a fidelity requirement, telling compression layers what's safe to abbreviate.

| Level | Name | Meaning | Compression Allowed |
|-------|------|---------|-------------------|
| **F0** | Exact | Bit-for-bit transmission | None. Literal only. |
| **F1** | Semantic | Meaning preserved, wording can change | Synonym substitution, reformatting |
| **F2** | Approximate | Core intent preserved, details lossy | Summarization, detail dropping |
| **F3** | Optional | Can be dropped entirely | Full omission |

### Defaults by Field Type

| Field Type | Default | Rationale |
|-----------|---------|-----------|
| File paths, line numbers | F0 | `auth.ts` ≠ `Auth.ts` — wrong path = broken code |
| Code snippets, identifiers | F0 | `==` ≠ `===` — syntax matters |
| Task IDs, refs | F0 | Wrong reference = wrong task |
| Action verbs, constraints | F1 | "implement" ≈ "build" — same intent |
| Rationale | F2 | Can be summarized |
| Alternatives considered | F3 | Useful for context, not for action |
| Pleasantries / hedging | F3 | Drop entirely |

### Error Budget

- **F0 violation = protocol failure.** Halt and debug. If structured compression has MORE F0 errors than English baseline, the protocol is broken.
- **F1 violation = semantic drift.** Flag for review.
- **F2 violation = acceptable loss.** Log but don't alert.
- **F3 violation = invisible.** Nobody notices.

---

## 11. Cross-Cutting: Source Map Contract

*Section owned by Designer — see .flightdeck/shared/designer/spec-sections-draft.md Section B for full specification.*

### The Hard Constraint

**Every compressed message MUST have a deterministic, invertible expansion function back to human-readable form.**

For any message `m` at compression level `c`:
- `expand(m, c) → m'` where `m'` is understandable by a human engineer without access to the ref dictionary
- `expand` is **deterministic** (same input → same output)
- `expand` is **total** (defined for every valid message — no edge cases)
- `expand(expand(m, L0), L3)` = `expand(m, L3)` (idempotent)

### Storage Model

| Store | Level | Purpose | Token Cost |
|-------|-------|---------|-----------|
| Wire (between agents) | L0-L2 | Efficient transport | Per-message |
| Audit log | L3 (auto-expanded) | Human review | ~20 tokens/msg amortized |
| Debug inspector | Any (on-demand) | Interactive debugging | ~50 tokens/msg on demand |
| Session replay | L2 + ref dictionary | Replay with context | One-time export |

**Key insight:** You pay the debuggability tax only when debugging. During normal operation, the cost is zero.

### Session Source Map File

Each session produces a source map — a JSON artifact mapping every compressed reference back to its full definition, every context hash to its content, and every expectation to its specification. This enables post-mortem analysis, session replay, and new-agent onboarding.

---

## 12. Cross-Cutting: Human Readability Scoring

*Section owned by Designer — see .flightdeck/shared/designer/spec-sections-draft.md Section C for full methodology.*

### The Readability Score (RS)

Composite score from 0.0 (opaque) to 1.0 (crystal clear), measured across three dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| **Reconstructability** | 0.5 | Can an outsider reconstruct what happened from the transcript + source map? |
| **Scannability** | 0.3 | Can a human quickly find specific information (decision X, blocker Y, file Z)? |
| **Level Accessibility** | 0.2 | Does each progressive disclosure level add useful, non-redundant information? |

**Target: RS ≥ 0.75 at every compression level.** If any condition drops below 0.75, compression is too aggressive.

**Adjusted efficiency metric:** `tokens_saved / RS_score` — prevents optimizing compression at the expense of understanding. The metric we optimize: **maximum token reduction at RS ≥ 0.75.**

---

## 13. Theoretical Foundations

*Section maintained by Generalist — see .flightdeck/shared/generalist/cross-disciplinary-insights.md for full analysis.*

### 13.1 Information-Theoretic Bounds

**Shannon entropy of agent messages:** English text carries ~1.0-1.5 bits of entropy per character. Agent coordination messages have much lower semantic entropy (most fall into ~10-50 intent categories). The theoretical floor for encoding these messages is significantly below English's token cost.

**Kolmogorov complexity bound:** `L_min(M) ≥ K(μ(M) | K_receiver)` — the minimum description length for a message is bounded by the Kolmogorov complexity of its semantic content, conditioned on the receiver's prior knowledge. This formalizes why shared context (Layers 0-1) is the most powerful compression mechanism.

**Rate-distortion function:** R(D) gives the minimum bits needed to reconstruct within distortion D. For variable-fidelity fields (§10), high-fidelity fields (file paths) must be transmitted losslessly; approximate fields can be compressed further.

### 13.2 Rate-Distortion Breakdown of Agent Messages

For agent coordination messages, the distribution is approximately:
- **~60% redundant** with shared context (blackboard state, prior messages) → R(D) = 0, need not be sent
- **~25% structural/formulaic** (message type, field names, boilerplate) → compressible to small constant bits via schema (SIP + fixed place structures)
- **~15% genuinely novel** semantic payload → incompressible: K(payload | shared_context)

Theoretical compression: 1 - (0 + 0.05 + 0.15) = **80% minimum** for coordination messages. The 95% figure requires PCC Phase 3 to further compress the structural portion AND assumes very high shared context (mature session).

**The hard wall:** You CANNOT go below the ~15% novel payload without losing meaning. Any protocol claiming >95% average compression is either (a) operating on highly repetitive tasks, or (b) losing semantics.

### 13.3 Honest Blended Estimate

- 80% of session messages are coordination → 80-90% compressed → contributes 64-72% savings
- 20% of session messages are novel discussion → 30-50% compressed → contributes 6-10% savings
- **Blended estimate: 60-80% reduction across a real session**
- Reaching 80%+ requires very long sessions where PCC Phase 3 dominates

### 13.4 Ambiguity-Efficiency Pareto Frontier

More compact representations rely more heavily on shared context for disambiguation. The protocol navigates this frontier by:
- Layers 0-1 building massive shared context (shifts the frontier toward efficiency)
- Fidelity markers (§10) identifying where ambiguity is unacceptable
- The expansion mechanism providing fallback when compression causes confusion

### 13.5 The Incompressibility Floor

Genuinely novel concepts (a new architecture insight, a creative solution) cannot be compressed below the complexity of their specification. Natural language is the right encoding for novel content — SIP payloads can always contain `natural_language` fields, and the `freeform` type (§7) is the explicit escape hatch. Compression gains come from the ~80% that is NOT novel.

### 13.6 Grice's Maxims as Protocol Heuristics

The protocol operationalizes all four of Grice's conversational maxims:
- **Quantity** (say enough but not too much) → progressive disclosure levels (§9)
- **Quality** (be truthful) → fidelity markers prevent lossy encoding of critical data (§10)
- **Relation** (be relevant) → expectation model filters irrelevant messages; taken to its logical extreme, "be relevant" = "say nothing when everything is as expected" (§4)
- **Manner** (be clear and orderly) → SIP typed envelopes enforce structure (§7)

### 13.7 Linguistic Precedent: Pidgin → Creole

PCC's 3-phase evolution mirrors documented natural language emergence. Pidgins naturally creolize into richer, more efficient languages through repeated interaction. Key finding from linguistics: creoles develop remarkably similar grammars worldwide, regardless of source languages — suggesting a universal grammar of efficient communication. If this holds for agent protocols, PCC Phase 2 should converge on similar patterns across different sessions.

### 13.8 Channel Capacity and the Forgetting Curve

Agent context windows exhibit a forgetting curve analogous to biological memory — early information has less influence on reasoning than recent information. This makes PCC resync (§8) not just a consistency mechanism but a NECESSITY to counteract context window decay. The Nyquist-like question: is there a minimum resync frequency below which semantic reconstruction fails?

### 13.9 Cross-Disciplinary Validation

Each protocol layer has deep precedent outside CS:

| Layer | Precedent | Domain | Track Record |
|-------|-----------|--------|-------------|
| SBDS (blackboard) | Stigmergic communication | Ant colonies | ~100M years of evolution |
| SIP (structured messages) | Closed-loop communication | Surgery | Proven in life-or-death domains |
| PCC (adaptive vocabulary) | Zipf's Law compression | Every human language | Universal across all cultures |
| Exception model | Regulatory gene patterns | DNA | Proven across all life |
| Content-addressable refs | Mathematical notation | Mathematics | ~2000 years of formal reasoning |

### 13.10 Open Question: Semantic Nyquist Rate

In signal processing, below the Nyquist rate you get aliasing — the reconstructed signal is WRONG, not just degraded. Is there an analogous cliff in semantic compression where you go from "slightly imprecise" to "fundamentally misunderstood"?

The minimum message resolution must be ≥ 2× the finest semantic distinction required for task success. If the task requires distinguishing "rename variable" from "rename function," the protocol must encode that distinction. Profile the actual semantic distinctions required by the task, then set compression to just above that threshold.

PCC Phase 3 may approach this limit. The expansion mechanism (any message can be decompressed on request) provides a safety net, but empirical measurement is needed to identify where this cliff lies.

---

## 14. Experiment Design (Summary)

*Full experiment specification in companion document: `.flightdeck/shared/architect/experiment-design.md`*

**Task:** "Bug Hunt" — 3 agents (Investigator, Fixer, Reviewer) collaboratively diagnose and fix a planted bug spanning 2 files in a 5-file mini codebase.

**5 Conditions:** A (English baseline) → B (SIP only) → C (SBDS + SIP) → D (Full stack with exceptions and triggers) → E (Full + content-addressable refs)

**Primary Metric:** Tokens per successful task completion  
**Adjusted Metric:** `tokens_saved / RS_score` (efficiency adjusted for readability ≥ 0.75)  
**Secondary:** Error rate, human readability score (RS), time-to-resolution  
**Hypothesis:** Condition E uses <30% of Condition A's tokens at RS ≥ 0.75 and equal task quality

---

## 15. Implementation Roadmap

### v1: SBDS + SIP (Recommended Starting Point)

The Designer's RS analysis proved that Layers 0-2 achieve the sweet spot: **75-87% token reduction with RS ≥ 0.80** — strictly better than English on both dimensions.

**Phase 1: Quick Wins (Testable Today)**
1. Define the SIP message envelope and 14 core brevity codes (Appendix A)
2. Implement a basic shared blackboard (in-memory dict with JSON Patch + version numbers)
3. Add path-level ownership and pub/sub filtering
4. Add expectation model (Layer -1) with adaptive heartbeat
5. Run Condition A vs C comparison — validate the win-win finding

**Phase 2: Production Hardening**
6. Add regulatory triggers with cascade depth limits and cycle detection
7. Add optimistic concurrency (version numbers on blackboard writes)
8. Add onboarding I-frame (GET_SNAPSHOT for new agents)
9. Implement source map expansion (deterministic decompression)
10. Run with live LLM agents (not hand-crafted messages) — validate real-world compliance

### v2: Add PCC (When v1 is Proven)

PCC (Layer 3) adds 5-10% marginal reduction but drops RS below 0.75 if implemented naively. The constraint: **compress values, not field names.**

**Phase 3: PCC with Readability Constraint**
11. Implement PCC Phase 1 bootstrap codebook with readback validation
12. Add content-addressable references (Layer 1) with invalidation protocol
13. Implement PCC Phase 2-3 with "values not names" constraint
14. Add ref sequence numbers, expansion-alongside-ref for F0 fields, ref refreshing
15. Run Conditions C vs D comparison — validate PCC adds value without breaking readability

**Phase 4: Validation & Research**
16. Full 5-condition experiment with 10 runs per condition (counterbalanced)
17. Condition F: emergent protocol discovery (token-budget pressure, no prescribed protocol)
18. Identify the semantic Nyquist rate empirically
19. Measure LLM compliance: can models reliably produce and parse the protocol?
20. Write up findings

## 16. Known Failure Modes and Mitigations

*Compiled from Radical Thinker's red-team analysis + Designer's UX pitfalls.*

| # | Failure Mode | Layer | RPN | Mitigation |
|---|---|---|---|---|
| 1 | **PCC ref drift** — silent codebook divergence, agents parse differently | PCC | **280** 🔴 | Periodic hash sync every 20 msgs + ref sequence numbers + expansion-alongside-ref for F0 + auto-escalate to L2 on mismatch (§8) |
| 2 | **Trigger cascades** — trigger A fires B fires C → infinite loop | SBDS | **224** 🔴 | Cascade depth limit of 3; monotonic state transitions only; cycle detection at registration (§5) |
| 3 | **Context window decay** — early refs fade from agent memory | PCC | **210** 🔴 | Ref refreshing: auto-expand stale refs (unused for 30+ msgs) to L1 inline; periodic resync every 50 msgs (§8) |
| 4 | **Trigger conflicts** — two contradictory triggers fire simultaneously | SBDS | 144 | Higher-specificity wins; equal specificity → first-registered wins + conflict logged (§5) |
| 5 | **Stale blackboard reads** — agent acts on outdated state | SBDS | 144 | Optimistic concurrency with version numbers; stale writes rejected (§5) |
| 6 | **Dangling references** — hash points to invalidated context | CAR | 120 | Tombstone + invalidation protocol with replacement pointer (§6) |
| 7 | **Codebook bootstrap failure** — malformed initial dictionary | PCC | 100 | Readback validation with hash check; receiver echoes hash, retransmit on mismatch (§8) |
| 8 | **No graceful degradation** — protocol break with no fallback | All | 100 | On parse failure, auto-request L3 NL expansion; `freeform` SIP type as escape hatch (§7). Fail loud and readable. |
| 9 | **Exception cascades** — cascading blockers overwhelm channel | Layer -1 | 96 | `cause_chain` deduplication; downstream exceptions collapsed to root cause (§4) |
| 10 | **Silence ambiguity** — can't distinguish working from crashed | Layer -1 | 90 | Mandatory adaptive heartbeat with task-scaled intervals (§4) |
| 11 | **Schema rigidity** — message doesn't fit SIP types | SIP | 42 | `freeform` type escape hatch; >20% freeform signals schema needs extension (§7) |
| 12 | **Bootstrap fatigue** — PCC setup cost exceeds savings for short sessions | PCC | 30 | Standard dictionary (0 bootstrap cost) + adaptive mode selection; v1 skips PCC entirely (§8) |
| 13 | **Newcomer hostility** — PCC Phase 3 opaque to joining agents | PCC | 30 | Onboarding I-frame provides full snapshot (§5) |
| 14 | **Compression cliff** — sudden loss of human observability | Cross | 30 | Minimum L1 for audit stream; compress values not field names (§9, §11) |
| 15 | **Hash collision** — different contexts get same hash | CAR | 10 | SHA-256 (negligible collision probability); include content length as secondary check |

---

## 17. Future Horizons (Research Track)

These ideas are not part of the v0.1 spec but are worth exploring in future iterations:

### 17.1 Semantic Intermediate Representation (SIR)
A standardized vector format for meaning that any model can encode to and decode from. Like Protocol Buffers for semantics. Addresses the Radical Thinker's embedding compression insight while maintaining model heterogeneity.

### 17.2 Post-Linguistic Reasoning
Current LLMs reason through language, but this may be a training artifact rather than a fundamental constraint. Mathematicians reason in notation, chess players in algebraic notation, programmers in code. A model trained to reason in structured protocols might achieve both compressed transport AND compressed reasoning.

### 17.3 Emergent Protocol Discovery
Rather than prescribing AECP, give agents a token-efficiency reward signal and let them discover optimal protocols through interaction. Would they converge on something like our protocol stack? This would validate (or challenge) our design choices.

### 17.4 Adversarial Compression
When agents share identical model weights, they implicitly share a "codebook" of associations. Exploiting this for additional compression is theoretically possible but creates tight model coupling. Worth studying for same-model deployments.

---

## 18. Example: End-to-End Session

A complete example showing all layers working together.

### Setup (session bootstrap)

```json
// Expectation Model (Layer -1)
{"expectations": {"on_task": "ACK→work→done|blocked", "silence": "working"}}
{"heartbeat": {"routine": 60, "standard": 30, "novel": 10}}

// Blackboard with Regulatory Triggers (Layer 0)
{"init_blackboard": {"project": {"goal": "REST API with auth"}, "tasks": {...}}}
{"triggers": [
  {"when": "tasks.auth-login.status == 'done'", "then": "SET tasks.auth-rate-limit.status = 'ready'"}
]}

// Codebook (Layer 3 Phase 1 bootstrap — standard dictionary, 0 extra tokens)
// Standard codes ACK, OK, S:done, S:blk, P, Q, etc. are pre-loaded.
// Session-specific refs defined as needed.
```

### Working Phase

**Without AECP (English, ~180 tokens):**
> Architect: "Hey dev-1, could you implement the login endpoint? It should accept email and password, validate against the database, and return a JWT token. Please use bcrypt for password hashing. The endpoint should be POST /api/auth/login. Tests should go in a co-located file."
> 
> Dev-1: "Got it, I'll start working on the login endpoint now."
> 
> Dev-1: "Login endpoint is done. I created src/auth/login.ts with the login function that validates credentials against the DB using bcrypt and returns a JWT. Tests are in src/auth/login.test.ts, all passing."
> 
> Architect: "Great work. Dev-2, you can now start on rate limiting since login is done."

**With AECP (~25 tokens):**
```
// Task spec is already on blackboard. Dev-1 subscribed to tasks.auth-login.
// When assigned, dev-1 is SILENT (Layer -1: silence = working).
// Periodic heartbeat: ✓ ... ✓ ... ✓ (~3 tokens over 3 minutes)
// Dev-1 finishes and updates blackboard (Layer 0):

{"op":"set","path":"tasks.auth-login.status","value":"done","by":"dev-1","read_version":1}

// Regulatory trigger fires: tasks.auth-rate-limit.status auto-set to 'ready'
// Dev-2 is notified via trigger. Auto-starts. No relay from architect.
// The only transmitted tokens: 1 delta op + ~3 heartbeats. ~28 tokens vs ~180.
```

**Compression achieved: ~84%.** And the majority of coordination happened via triggers with zero explicit messages.

### Exception case (deviation from expectations)

```
// Dev-2 hits a problem — this REQUIRES communication (Layer -1 exception):
S:blk auth-rate-limit | NEED D:store — redis vs inmem? ctx:arch-overview

// Architect decides (Layer 2 SIP + Layer 3 PCC Phase 2):
D:store = inmem | single-proc, YAGNI

// Dev-2 acknowledges implicitly by going silent again (working).
// Total exchange: ~20 tokens for a design decision.
```

---

## Appendix A: Brevity Code Reference

| Code | SIP Expansion | English Equivalent |
|------|--------------|-------------------|
| `ACK` | `{type:"response", payload:{status:"acknowledged"}}` | "I received your message and will proceed" |
| `OK` | `{type:"agree"}` | "I agree with your proposal" |
| `NO` | `{type:"reject"}` | "I disagree / reject this approach" |
| `P <task>` | `{type:"request", action:"implement", ctx:<task>}` | "Please implement this task" |
| `R <target>` | `{type:"request", action:"review", target:<ref>}` | "Please review this" |
| `S:wip` | `{type:"status", state:"in-progress"}` | "I'm working on this" |
| `S:done <task>` | `{type:"status", state:"done", ctx:<task>}` | "I've completed this task" |
| `S:blk <reason>` | `{type:"status", state:"blocked", blockers:[<reason>]}` | "I'm blocked because..." |
| `Q <question>` | `{type:"query", question:<question>}` | "I have a question about..." |
| `D:<topic> = <choice>` | `{type:"propose", decision:<topic>, recommendation:<choice>}` | "My decision/recommendation is..." |
| `NEED <X> from <Y>` | `{type:"request", action:"provide", what:<X>, to:<Y>}` | "I need X from agent Y" |
| `DELTA <ref> <changes>` | `{type:"status", artifacts:<ref>, changes:<changes>}` | "Here are the changes I made to..." |
| `CONFLICT <resource>` | `{type:"clarify", issue:"conflict", resource:<resource>}` | "We have a conflict on this resource" |
| `YIELD <resource>` | `{type:"status", released:<resource>}` | "I'm releasing this resource" |

---

## Appendix B: Comparison with English Baseline

| Scenario | English (tokens) | AECP (tokens) | Reduction |
|----------|-----------------|---------------|-----------|
| Task assignment | ~45 | ~8 (blackboard ref + codebook) | 82% |
| Status update (happy path) | ~30 | 0 (silence = working) | 100% |
| Status update (done) | ~40 | ~10 (1 delta op) | 75% |
| Status update (blocked) | ~50 | ~15 (brevity code + context ref) | 70% |
| Design decision request | ~80 | ~20 (propose + options) | 75% |
| Design decision response | ~60 | ~12 (D:<topic> = <choice>) | 80% |
| Relay / coordination | ~50 | 0 (blackboard subscriptions) | 100% |
| Context re-establishment | ~100 | ~5 (ctx ref) | 95% |
| Novel discussion | ~150 | ~120 (NL still needed) | 20% |

**Weighted average across typical session: 60-80% reduction (honest blended estimate).**

---

*This specification is a living document. Challenge every assumption. The goal is a protocol that's simple enough to implement in a day, powerful enough to cut token costs by 3-5x, and transparent enough that a human can always understand what agents are saying. Compression without correctness is just data loss.*
