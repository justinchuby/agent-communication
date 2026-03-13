# Efficient Agent Communication: Interaction Design & Communication Patterns

**Author:** Designer Agent (@53a180f5)  
**Research Group:** Efficient Agent Communication

---

## 1. How Humans Solved This: Domain Analysis

Humans have already cracked efficient communication in high-stakes, time-critical domains. Every one of these solutions trades natural language expressiveness for **precision, speed, and reduced ambiguity**. Let's dissect them.

### Aviation (Pilots & ATC)

Pilots and air traffic controllers communicate under extreme time pressure with catastrophic failure modes. Their solution:

- **Brevity codes**: Fixed phrases with exact meanings. "Wilco" = "will comply." "Roger" = "received." No ambiguity.
- **Readback protocol**: Receiver repeats critical information back. This is a **built-in error-correction mechanism** — like a checksum for human speech.
- **Structured templates**: Altitude, heading, speed always come in predictable order. The *format* carries information, not just the *content*.
- **Phonetic alphabet**: Alpha, Bravo, Charlie — eliminates acoustic ambiguity. They sacrificed brevity for **channel reliability**.

**Key insight for agents:** When the channel is reliable (it is — we're passing text), we can skip error-correction overhead. But the **structured templates** and **brevity codes** are pure gold. A shared vocabulary of short tokens with precise meanings eliminates parsing ambiguity and reduces token count.

### Surgery (Operating Room Communication)

Surgeons operate in teams where miscommunication kills.

- **Precise anatomical terminology**: "Left anterior descending artery" not "that tube on the left." **Shared ontology** eliminates ambiguity.
- **Closed-loop communication**: "Clamp." → "Clamp." → *action* → "Clamped." Three-phase: request, confirm, complete. This is a **state machine for task handoff.**
- **Role-based addressing**: "Anesthesia, how's the pressure?" — explicit addressing prevents the bystander effect.
- **Silence as signal**: In surgery, silence means "proceeding normally." Deviations from protocol are what get communicated. **Communication by exception.**

**Key insight for agents:** Communication by exception is massively efficient. If agents share a model of "expected behavior," they only need to communicate *deviations*. This is diff-based communication applied to intent.

### Music (Musical Notation)

Music notation is a 1000-year-old DSL for encoding complex temporal and harmonic information.

- **Spatial encoding**: Position on the staff = pitch. Left-to-right = time. The **layout itself is the data structure.**
- **Extreme compression**: A single chord symbol like "Cmaj7" encodes four simultaneous pitches, their relationships, and implied harmonic function. That's ~40 bytes of English compressed to 5 characters.
- **Layered information**: Pitch, rhythm, dynamics, articulation, and expression all coexist in the same visual space without collision. **Multi-channel encoding in a single stream.**
- **Shorthand by convention**: "D.C. al Coda" = "go back to the beginning, play until you see the coda sign, then jump to the coda section." Six words replace a paragraph of instructions because both parties share the protocol.

**Key insight for agents:** Spatial/structural encoding is underused in agent communication. Instead of describing a data structure in words, *send the structure*. A JSON object or a diagram IS the message. Also: layered encoding lets you pack multiple information types into a single message.

### Mathematics (Symbolic Notation)

Mathematics is arguably the most efficient human communication system ever devised.

- **Symbol density**: `∀ε>0, ∃δ>0 : |x-a|<δ ⟹ |f(x)-L|<ε` — this is 43 characters encoding a concept that takes 2-3 sentences in English.
- **Composability**: Symbols compose. `f(g(x))` is immediately parseable. English descriptions of the same nesting become tortured.
- **Unambiguous**: Unlike natural language, mathematical notation has exactly one parse. No pragmatics, no implicature, no context-dependence.
- **Referential**: "By Theorem 3.2" — a pointer to shared knowledge. You don't re-derive; you reference.

**Key insight for agents:** References to shared knowledge are the ultimate compression. If both agents have access to the same codebase/docs, a file path + line number is worth a thousand words of description. **Pointers beat payloads.**

### Military (Tactical Communication)

Military communication is optimized for degraded channels under stress.

- **BREVITY codes**: Standardized across NATO. "Bingo" = fuel critical. "Winchester" = out of ammunition. One word encodes a complex tactical state.
- **SALUTE reports**: Size, Activity, Location, Unit, Time, Equipment. Fixed format means the parser is simple and the producer can't forget a field.
- **Prowords**: "BREAK" = pause between parts of a message. "OUT" = end of transmission. These are **protocol control characters** embedded in natural language.
- **Authentication**: Challenge-response to verify identity. Agents need this too — how do you know you're talking to the right agent?

**Key insight for agents:** Fixed report formats (like SALUTE) are incredibly powerful. When every status update follows the same schema, you eliminate all structural parsing overhead. The receiver knows exactly where to find each piece of information.

---

## 2. Design Principles for Agent Communication

Synthesizing across all domains, I see six core principles:

### Principle 1: Shared Context is the Ultimate Compressor

The single biggest factor in communication efficiency is **how much context the parties share**.

- **High shared context** (two agents working on the same file): `"line 47: s/foo/bar/"` — 20 characters.
- **Low shared context** (new agent joining): Need full file path, purpose, current state, what to change and why — 200+ characters.

**Design implication:** Agent communication protocols should have a **context negotiation phase**. Before communicating, establish what's shared. Then compress against that shared context. This is literally how video codecs work — send keyframes (full context) occasionally, then diffs.

```
Protocol phases:
1. HANDSHAKE: Establish shared context ("I know about repo X, files A,B,C, task T")
2. DELTA: Communicate only what's new/different
3. RESYNC: Periodically re-establish full context (prevent drift)
```

### Principle 2: Format as Meaning (Structure Over Description)

Stop describing structures. **Send the structure.**

Bad (33 tokens):
```
Please create a function called processUser that takes a user object 
with name and email fields and returns a boolean indicating success.
```

Good (12 tokens):
```
processUser(user: {name: str, email: str}) -> bool
```

The type signature IS the specification. The format carries the meaning. This is what musicians figured out — the staff IS the encoding. What mathematicians figured out — the formula IS the proof step.

**Design implication:** Develop format conventions for common communication types. A code change can be a diff. A task can be a structured object. A question can be a query with typed parameters. Reserve natural language for genuinely ambiguous or novel situations.

### Principle 3: Communication by Exception

The surgical principle of "silence means normal" is profound.

If agents share a model of expected behavior, **they only need to communicate when reality deviates from expectation.** This is:

- How TCP works (only ACK/retransmit on anomaly in fast path)
- How monitoring works (alert on threshold breach)
- How good management works (don't micromanage; escalate problems)

**Design implication:** Agent protocols should include an **expectation layer** — a shared model of what "normal" looks like. Messages are then deviations from that model. This dramatically reduces communication volume during normal operation.

### Principle 4: Layered Compression (The Efficiency Spectrum)

Not all messages need the same level of compression. Design a spectrum:

| Layer | When to Use | Example |
|-------|-------------|---------|
| **L0: Raw reference** | Pointing to shared knowledge | `"see file:auth.ts:47"` |
| **L1: Structured shorthand** | Routine operations | `{op: "edit", file: "auth.ts", line: 47, diff: "+validate(token)"}` |
| **L2: Abbreviated natural language** | Coordination with some ambiguity | `"auth.ts needs token validation before DB call"` |
| **L3: Full natural language** | Novel problems, establishing new context | Full paragraph explaining the security concern |
| **L4: Multi-modal** | Complex explanations | Text + code + diagram + examples |

**Design implication:** Let agents dynamically choose compression level based on: (a) shared context, (b) message importance, (c) ambiguity of the content, and (d) whether human readability is needed.

### Principle 5: Brevity Codes (Shared Vocabulary Compression)

Every efficient human domain develops a shared shorthand. Agents should too.

Proposal — a small set of **agent brevity codes**:

| Code | Meaning | Replaces |
|------|---------|----------|
| `ACK` | Received, will act | "I've received your message and will proceed with the requested action" |
| `BLOCK(X)` | I'm blocked on X | "I cannot proceed because I'm waiting for X to be completed" |
| `DONE(task)` | Task complete | "I have completed the task described as..." |
| `NEED(X, from)` | I need X from agent | "Could you please provide me with X when you have a chance" |
| `DELTA(ref, changes)` | Changes to known thing | "I've made the following modifications to the previously discussed..." |
| `QUERY(question)` | Need info, no action | "I have a question that doesn't require you to take action..." |
| `CONFLICT(resource)` | Resource conflict | "I've discovered that we both need to modify the same..." |
| `YIELD(resource)` | Releasing resource | "I'm done with this resource, it's available for others" |

This is the NATO brevity code approach applied to software agents.

### Principle 6: The Debuggability Tax

Here's the hard tradeoff: **every unit of compression reduces human readability.**

`∀ε>0, ∃δ>0 : |x-a|<δ ⟹ |f(x)-L|<ε` is beautiful if you're a mathematician. It's gibberish if you're not.

This is a real tension in agent communication:
- **Maximum efficiency** → agents speak in compressed tokens humans can't read
- **Maximum debuggability** → agents speak in verbose English humans can skim
- **Sweet spot** → structured messages with named fields that are both compact and scannable

**Design implication:** Messages should have two layers:
1. **Machine layer**: Compact, structured, optimized for agent parsing
2. **Human layer**: Optional natural-language gloss that can be generated on demand

Think of it like compiled code + source maps. The agents communicate in the efficient format. When a human needs to inspect, the system can "decompile" any message into readable form. This way you pay the debuggability tax only when debugging.

```
// Machine layer (what agents actually send):
{type: "DELTA", ref: "auth.ts@a3f2", diff: "+L47:validate(tok)"}

// Human layer (generated on demand when inspected):
"Added token validation call at line 47 of auth.ts"
```

---

## 3. Context-Dependent Compression: A Deeper Look

The most interesting design pattern is **adaptive compression based on shared context.** Let me model this more precisely.

### The Context Stack

At any point, two communicating agents share a **context stack**:

```
[global]     Shared codebase, shared tools, shared protocols
[project]    Current repo, current task, team members
[session]    What we've discussed, decisions made, files touched
[immediate]  The current sub-task, the current file, the current line
```

Each layer of shared context enables more compression. A message's optimal encoding depends on which layers are shared:

- **Both agents share all 4 layers**: `"+validate(tok) L47"` — 20 chars
- **Agents share global + project**: `"In auth.ts, add token validation at line 47 before the DB query"` — 65 chars
- **Agents share only global**: Need full explanation of which project, which file, what validation means, why it matters — 300+ chars

### Dynamic Context Establishment

Efficient protocols should let agents **explicitly manage their context stack**:

```
ESTABLISH_CONTEXT {
  project: "talking",
  task: "implement-auth",
  files: ["src/auth.ts", "src/middleware.ts"],
  decisions: ["using JWT", "no refresh tokens for MVP"]
}
```

After this handshake, subsequent messages can be maximally compressed because both agents know what's in scope.

---

## 4. Multi-Modal Encoding: Mixing Formats for Density

Humans naturally mix modalities. A textbook has text + equations + diagrams + code. Each modality is optimal for a different kind of information.

For agents, the modalities are:

| Modality | Best For | Example |
|----------|----------|---------|
| **Natural language** | Intent, rationale, ambiguous situations | "We chose JWT because..." |
| **Structured data (JSON/YAML)** | Configuration, parameters, state | `{port: 3000, env: "prod"}` |
| **Code** | Behavior, algorithms, transformations | `function validate(tok) {...}` |
| **Diffs** | Changes to known state | `@@ -47,0 +47,1 @@ +validate(tok)` |
| **References** | Pointers to shared knowledge | `file:auth.ts#L47`, `RFC 7519` |
| **Diagrams (ASCII/Mermaid)** | Architecture, flow, relationships | `A -> B -> C` |
| **Tables** | Comparisons, structured lists | Markdown tables |

**Design principle:** A single message can (and should) mix modalities. Don't describe in words what a diff shows better. Don't draw a diagram for what a single reference captures.

### Example: Multi-Modal Task Assignment

```
TASK: Add rate limiting to /api/auth endpoint

WHY: Load test showed 10x normal traffic causes cascade failure
     (see: .flightdeck/shared/architect/load-test-results.md)

WHAT: 
  endpoint: POST /api/auth
  limit: 100 req/min/IP
  response_when_limited: 429 {error: "rate_limited", retry_after: <seconds>}

WHERE:
  file: src/middleware/rate-limit.ts (create new)
  integrate: src/routes/auth.ts#L23 (before validateCredentials call)

PATTERN: Follow existing middleware pattern in src/middleware/cors.ts

DONE_WHEN: 
  - [ ] Middleware created and tested
  - [ ] Integration test passes
  - [ ] Load test shows graceful degradation
```

This mixes: natural language (WHY), structured data (WHAT), references (WHERE, PATTERN), and a checklist (DONE_WHEN). Each modality carries the type of information it's best at. Total message is ~40% shorter than a pure natural language version and far less ambiguous.

---

## 5. The Efficiency-Readability Tradeoff: A Design Framework

This is the core design tension. Let me propose a framework for navigating it.

### The Communication Audience Matrix

Every agent message potentially has THREE audiences:

1. **The receiving agent** — needs to parse and act
2. **Human operators** — need to monitor and debug
3. **Future agents** — need to understand history/context

Each audience has different needs:

| Audience | Needs | Optimal Format |
|----------|-------|---------------|
| Receiving agent | Fast parsing, unambiguous | Structured, compressed |
| Human operator | Skimmable, understandable | Natural language, formatted |
| Future agent | Context-rich, self-contained | Hybrid with metadata |

### Resolution: Layered Messages with Progressive Disclosure

Apply the UX principle of **progressive disclosure** to agent messages:

```
Level 0 (headline):  "DELTA auth.ts: +rate-limiting"
Level 1 (summary):   "Added rate limiting middleware (100/min/IP) to auth endpoint"
Level 2 (detail):    Full diff + rationale + test results
Level 3 (context):   Related decisions, alternatives considered, links
```

- Agent dashboards show Level 0 (scannable overview)
- Click to expand to Level 1 (understand what happened)
- Drill down to Level 2 (see the actual changes)
- Deep dive into Level 3 (understand the full context)

Agents communicate at Level 0-1 for routine operations, Level 2-3 for handoffs and complex situations. Humans can inspect at whatever level they need.

---

## 6. Proposed Communication Pattern: "Adaptive Protocol"

Putting it all together, here's my proposed interaction pattern:

### Phase 1: Context Handshake
```
AGENT_A → AGENT_B: HELLO {context_hash: "a3f2b1", capabilities: [...], working_on: "auth"}
AGENT_B → AGENT_A: HELLO {context_hash: "a3f2b1", capabilities: [...], working_on: "api"}
// Context hashes match → both agents share the same context → maximum compression enabled
```

### Phase 2: Compressed Communication
```
AGENT_A → AGENT_B: {op: "need", what: "rate-limit-middleware", where: "auth.ts#L23", spec: {...}}
AGENT_B → AGENT_A: ACK
...
AGENT_B → AGENT_A: DONE {ref: "rate-limit-middleware", files: ["rate-limit.ts"], tests: "pass"}
```

### Phase 3: Exception Handling
```
// Only when something unexpected happens do we expand to natural language:
AGENT_B → AGENT_A: BLOCK {
  what: "rate-limit-middleware",
  reason: "auth.ts uses Express but rate-limit library requires Koa",
  need: "decision: switch library or add adapter?",
  options: [
    {id: "A", desc: "Use express-rate-limit instead", effort: "low", risk: "low"},
    {id: "B", desc: "Write Koa adapter", effort: "high", risk: "medium"}
  ]
}
```

### Phase 4: Context Resync (Periodic)
```
// Every N messages or on timeout, resync to prevent context drift:
AGENT_A → AGENT_B: SYNC {context_hash: "b4c3a2", state: {...}}
```

---

## 7. Key Takeaways

1. **Shared context is the #1 compressor.** Invest in establishing it before communicating.
2. **Structure over description.** Send diffs, schemas, and references — not paragraphs.
3. **Communicate by exception.** Silence = proceeding normally. Only deviate to communicate deviations.
4. **Use brevity codes.** A small shared vocabulary (ACK, BLOCK, DONE, NEED) eliminates boilerplate.
5. **Layer for audiences.** Machine-efficient core + human-readable gloss on demand.
6. **Mix modalities.** Natural language for intent, structured data for specs, code for behavior, diffs for changes.
7. **Adapt compression to context.** High shared context → maximum compression. New context → expand.
8. **Pay the debuggability tax only when debugging.** Compile to efficient format; decompile for humans.

The fundamental insight: **the most efficient message is the one you don't have to send.** Design protocols that maximize shared context and minimize the need for explicit communication. Everything else is optimization.
