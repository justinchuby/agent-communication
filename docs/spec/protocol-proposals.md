# Protocol Proposals for Efficient Agent Communication

**Author:** Architect Agent  
**Status:** Draft for group discussion  
**Core Thesis:** Natural language between AI agents is an anti-pattern. We're converting structured internal representations → English → structured internal representations. That's like two databases communicating via PDF printouts and OCR. The question isn't "how do we compress English" — it's "what's the right abstraction for machine-to-machine coordination?"

---

## Protocol 1: Structured Intent Protocol (SIP)

### Problem Framing

Most agent-to-agent messages fall into ~10 intent categories: request, respond, delegate, status-update, query, assert, propose, agree, reject, clarify. English buries these intents inside paragraphs. SIP makes intent explicit and machine-parseable.

### Specification

Every message is a typed JSON envelope:

```json
{
  "v": 1,
  "id": "msg-a1b2",
  "type": "request|response|delegate|status|query|assert|propose|agree|reject|clarify",
  "from": "architect",
  "to": "developer-1",
  "re": "msg-x9y8",
  "context": "task-id-or-thread-ref",
  "payload": { },
  "meta": {
    "priority": "high|normal|low",
    "ttl": 300,
    "expects": "response|ack|none"
  }
}
```

### Payload Schemas by Type

**request:**
```json
{
  "action": "implement|review|test|analyze|fix",
  "target": "src/auth/login.ts",
  "spec": "Add rate limiting: max 5 attempts per IP per 15min window",
  "constraints": ["no new dependencies", "must pass existing tests"],
  "acceptance": ["rate limit enforced", "429 response after limit", "reset after window"]
}
```

**status:**
```json
{
  "state": "started|in-progress|blocked|done|failed",
  "progress": 0.7,
  "summary": "Implemented rate limiter, writing tests",
  "blockers": [],
  "artifacts": ["src/auth/rate-limiter.ts"]
}
```

**propose (for design decisions):**
```json
{
  "decision": "Use Redis vs in-memory for rate limiting",
  "options": [
    {"id": "A", "label": "Redis", "pros": ["distributed", "persistent"], "cons": ["new dependency"]},
    {"id": "B", "label": "In-memory Map", "pros": ["zero deps", "simple"], "cons": ["per-process only"]}
  ],
  "recommendation": "B",
  "rationale": "Single-process deployment, YAGNI on distribution"
}
```

### Example Conversation

**English (147 tokens):**
> "Hey, I've been looking at the authentication module and I think we should add rate limiting to the login endpoint. My suggestion would be to implement a simple in-memory rate limiter that tracks failed attempts by IP address. We should limit it to 5 attempts per 15-minute window. After that, return a 429 status code. I considered using Redis but I think that's overkill for our current single-server setup. What do you think?"

**SIP (62 tokens):**
```json
{
  "v":1, "type":"propose", "from":"architect", "to":"dev-1",
  "context":"auth-module",
  "payload":{
    "decision":"Rate limiting strategy for POST /login",
    "options":[
      {"id":"A","label":"Redis counter","cons":["new dep, overkill for single-server"]},
      {"id":"B","label":"In-memory IP map","pros":["zero deps","simple"]}
    ],
    "recommendation":"B",
    "rationale":"Single-process deployment",
    "spec":"Max 5 attempts/IP/15min → 429"
  },
  "meta":{"expects":"response"}
}
```

### Why This Works

- **Parseable by both humans and machines.** An agent can route on `type` and `action` without NLP.
- **Eliminates ambiguity.** "What do you think?" becomes `"expects": "response"`. The recipient knows exactly what's needed.
- **Composable.** You can build workflows: request → status(in-progress) → status(done) → response.
- **Measurable.** Token count reduction is directly quantifiable.

### Estimated Compression

~40-60% token reduction vs English for typical coordination messages. Greater savings for structured content (task specs, status updates); less for open-ended discussion.

### How to Test

1. Take 50 real agent-to-agent messages from a multi-agent session
2. Encode each in SIP format
3. Measure: token count, information preservation (can a receiving agent reconstruct the full intent?), latency to first useful action
4. Run identical multi-agent tasks with English vs SIP, compare total tokens consumed and task completion quality

---

## Protocol 2: Shared Blackboard with Delta Sync (SBDS)

### Problem Framing

Agents constantly re-describe shared state. "I've finished the auth module, it exports three functions: login, logout, and refreshToken, each taking..." — the receiving agent ALREADY has access to the code. Most agent messages are redundant with information that exists in shared artifacts. The real protocol problem isn't message format — it's that agents lack shared state.

### Specification

A **blackboard** is a structured shared document that all agents can read and write to. Communication becomes: (1) mutate the blackboard, (2) notify others of what changed.

**Blackboard Schema:**
```yaml
blackboard:
  project:
    goal: "Build auth system with OAuth2"
    constraints: ["TypeScript", "no new frameworks", "PostgreSQL"]
  
  tasks:
    auth-login:
      status: done
      owner: dev-1
      artifacts: [src/auth/login.ts, src/auth/login.test.ts]
      decisions:
        - id: d1
          choice: "bcrypt for password hashing"
          rationale: "Industry standard, constant-time comparison"
    
    auth-rate-limit:
      status: in-progress
      owner: dev-2
      depends: [auth-login]
      spec: "5 attempts/IP/15min"

  knowledge:
    patterns:
      error-handling: "All services throw typed AppError, caught by middleware"
      testing: "Co-located .test.ts files, vitest"
    
  open-questions:
    - id: q1
      question: "Redis or in-memory for rate limiter?"
      proposed-by: architect
      status: pending
```

**Delta Message Format:**
```json
{
  "op": "patch",
  "path": "tasks.auth-rate-limit.status",
  "value": "done",
  "prev": "in-progress",
  "by": "dev-2",
  "note": "Implemented with in-memory Map, tests passing"
}
```

**Batch Deltas:**
```json
{
  "ops": [
    {"op": "set", "path": "tasks.auth-rate-limit.status", "value": "done"},
    {"op": "set", "path": "tasks.auth-rate-limit.artifacts", "value": ["src/auth/rate-limiter.ts"]},
    {"op": "append", "path": "tasks.auth-rate-limit.decisions", "value": {"id":"d2", "choice":"in-memory Map"}}
  ],
  "by": "dev-2"
}
```

### Example: What This Replaces

**Without blackboard (English, ~200 tokens across 3 messages):**
> Dev-1 → Architect: "I finished the login endpoint. It exports login() which takes email and password, validates against the DB, and returns a JWT. I used bcrypt for hashing. Tests are in login.test.ts."
>
> Architect → Dev-2: "Dev-1 finished login. You can now start on rate limiting. The login endpoint is at src/auth/login.ts. We're using bcrypt for hashing. Please implement rate limiting — 5 attempts per IP per 15 minutes."
>
> Dev-2 → Architect: "Got it, starting on rate limiting now."

**With blackboard (3 delta ops, ~45 tokens):**
```json
{"op":"set","path":"tasks.auth-login.status","value":"done","by":"dev-1"}
```
Dev-2 subscribes to `tasks.auth-rate-limit.depends` — when all deps are `done`, it auto-starts. No relay through architect needed. Dev-2 reads `tasks.auth-rate-limit.spec` directly from the blackboard.

### Why This Works

- **Eliminates relay messages.** The architect doesn't need to re-describe what dev-1 did to dev-2. The blackboard IS the single source of truth.
- **Eliminates re-description.** Agents never describe code that exists in the repo. They reference it: `"artifacts": ["src/auth/login.ts"]`.
- **Enables reactive coordination.** Agents subscribe to paths. When a dependency's status becomes `done`, dependent tasks auto-unblock.
- **Order-of-magnitude reduction** for coordination-heavy workflows where the same information gets relayed through multiple agents.

### Estimated Compression

~70-90% token reduction for coordination messages. The blackboard absorbs most "informational" content. Only novel decisions and questions need explicit messages.

### How to Test

1. Implement a simple in-memory blackboard (a nested dict with JSON Patch support)
2. Run a 3-agent task (architect + 2 devs) building a small feature
3. Condition A: English communication. Condition B: Blackboard + deltas.
4. Measure: total tokens exchanged, messages sent, time to task completion, error rate (misunderstandings)

---

## Protocol 3: Progressive Context Compression (PCC)

### Problem Framing

Even structured protocols are verbose at the start. But over a session, agents build shared context. Human experts do this naturally — two experienced engineers can communicate in shorthand that would be incomprehensible to an outsider. Can we formalize this?

PCC works in three phases, progressively compressing communication as shared context grows.

### Specification

**Phase 1: Bootstrap (full definitions)**

At session start, agents exchange definitions in structured format (like SIP). Each definition gets a short reference code.

```json
{
  "define": [
    {"ref": "P1", "means": {"type":"request","action":"implement","target":"src/auth/"}},
    {"ref": "S:done", "means": {"type":"status","state":"done"}},
    {"ref": "S:wip", "means": {"type":"status","state":"in-progress"}},
    {"ref": "RL", "means": "rate-limiting feature: 5 attempts/IP/15min → 429"},
    {"ref": "T:vt", "means": "run vitest, all tests pass"},
    {"ref": "Q", "means": {"type":"query","expects":"response"}},
    {"ref": "OK", "means": {"type":"agree"}},
    {"ref": "D:", "means": "decision on <topic>"},
    {"ref": "BLK", "means": {"type":"status","state":"blocked"}}
  ]
}
```

**Phase 2: Compressed exchange (using refs)**

```
P1 RL → dev-2
```
Means: "Request dev-2 to implement rate-limiting in src/auth/"

```
S:wip RL
```
Means: "Rate limiting is in progress"

```
D:store = inmem | reason: single-proc, YAGNI
```
Means: "Decision on storage: use in-memory, rationale is single process, YAGNI"

```
S:done RL + T:vt ✓
```
Means: "Rate limiting done, vitest passing"

**Phase 3: Implicit context (maximum compression)**

After enough shared history, even refs become optional for predictable messages:

```
RL ✓
```
(Rate limiting is done — context makes the full meaning unambiguous)

```
?store
```
(What's the decision on storage? — `?` = query, `store` = known topic from earlier)

### Protocol Rules

1. **Define before use.** Every ref must be defined in Phase 1 or explicitly introduced later.
2. **Receiver can request expansion.** If a message is ambiguous: `"expand: RL ✓"` → sender resends in Phase 1 format.
3. **Ref table is append-only.** Once defined, a ref never changes meaning. New concepts get new refs.
4. **Periodic checkpoints.** Every N messages, agents sync their ref tables to prevent drift.

### Example Full Session

```
=== BOOTSTRAP ===
{define: [P1, S:done, S:wip, RL, T:vt, Q, OK, D:, BLK]}

=== WORKING ===  
architect → dev-2: P1 RL
dev-2 → architect: OK. S:wip RL
dev-2 → architect: Q D:store — redis vs inmem?
architect → dev-2: D:store = inmem | single-proc
dev-2 → architect: OK

... (10 minutes later) ...

dev-2 → architect: S:done RL + T:vt ✓ + art:[src/auth/rate-limiter.ts]

=== MAXIMUM COMPRESSION ===
architect → dev-2: looks good. next: P1 session-mgmt
dev-2: OK. wip.
```

### Why This Works

- **Mirrors how human experts communicate.** Surgeons, pilots, military — all use compressed protocols built on shared training.
- **Adaptive compression.** Starts verbose (safe), gets compressed (fast) as context builds.
- **Graceful degradation.** Any message can be expanded on request. No information is permanently lost.
- **Tokenizer-aware.** Short refs like `S:wip` and `RL` are 1-2 tokens each. A well-chosen vocabulary minimizes token count.

### Estimated Compression

- Phase 1: ~30% reduction (overhead of definitions)
- Phase 2: ~60-75% reduction
- Phase 3: ~85-95% reduction for routine coordination

### How to Test

1. Define a ref vocabulary for a standard software dev workflow (~30-50 refs)
2. Run the same multi-agent task three times: English, SIP (Protocol 1), and PCC
3. Measure: tokens per message over time (should decrease for PCC), total session tokens, task completion quality, error rate
4. Key metric: **compression curve** — plot tokens/message over session lifetime. PCC should show a clear downward trend.

---

## Comparison Matrix

| Dimension | SIP | SBDS | PCC |
|---|---|---|---|
| Token reduction (estimated) | 40-60% | 70-90% | 30% → 95% (improves over time) |
| Implementation complexity | Low | Medium | Medium-High |
| Human readability | High | Medium | Low (Phase 3) |
| Requires shared infrastructure | No | Yes (blackboard) | No (but needs ref-table sync) |
| Best for | Structured tasks, clear requests | Multi-agent coordination | Long-running sessions |
| Worst for | Open-ended discussion | Simple 2-agent chats | Short sessions (bootstrap overhead) |
| Failure mode | Still verbose for nuance | Single point of failure (blackboard) | Ref drift, ambiguity in Phase 3 |

## Recommendation: Hybrid Approach

These protocols aren't mutually exclusive. The optimal system combines all three:

1. **SBDS as the foundation** — shared blackboard eliminates most coordination messages entirely
2. **SIP as the message format** — when agents DO need to communicate, use typed structured messages
3. **PCC as an optimization layer** — within a session, progressively compress SIP messages using shared refs

This layered approach could achieve **80-95% token reduction** for typical multi-agent software development workflows while maintaining clarity and correctness.

## Proposed Experiment Design

**Task:** 3 agents collaboratively build a REST API with auth, CRUD, and tests.

**Conditions:**
- A: English only (baseline)
- B: SIP only
- C: SBDS + SIP
- D: SBDS + SIP + PCC (full hybrid)

**Metrics:**
1. Total tokens consumed (input + output across all agents)
2. Messages exchanged
3. Task completion time
4. Task completion quality (test pass rate, code review score)
5. Error rate (misunderstandings requiring clarification)
6. Tokens per coordination action (normalize for task complexity)

**Hypothesis:** Condition D uses <20% of the tokens of Condition A, with equal or better task quality.

---

*Open for discussion. Eager to hear @radical-thinker's first-principles perspective — there may be even more fundamental rethinking possible.*
