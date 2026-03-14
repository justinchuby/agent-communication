# Radical Ideas: Beyond the Blackboard

**Author:** Radical Thinker
**Date:** 2025-07-14
**Status:** Provocative draft — ideas ranked by audacity, not just feasibility
**Depends on:** `findings.md`, `design-proposal.md`

---

## 0. The Uncomfortable Question

The design proposal asks: *"How do we make blackboard reads cheaper?"*

I want to ask: *"Why are agents reading at all?"*

AECP v1 discovered that shared state eliminates messages. The design proposal discovers that shared state has its own cost — read amplification. It then proposes seven clever ways to reduce that cost (scoped reads, deltas, compact format, etc.). These are good. They reduce blackboard reads by 60–90%.

But they're optimizing the wrong function. They're making `C_bb` smaller inside the existing equation:

```
C_total = C_sys + C_bb + C_msg + C_code + C_reason
```

What if we could make entire *terms* disappear? What if the right architecture makes `C_bb = 0` not by eliminating the blackboard, but by making reads *free*?

That's not as crazy as it sounds. Here are nine ideas, ordered from "ship this Monday" to "this changes everything if it works."

---

## 1. The Free Lunch: Prompt Caching Makes Reads 90% Cheaper Tomorrow

### The Insight

The design proposal never once mentions **prompt caching** — arguably the single highest-leverage mechanism available *right now* with zero protocol changes.

Anthropic's prompt caching (shipping today, mid-2025): any prefix of the prompt that's been seen recently is cached. Cache hits cost **1/10th** of normal input tokens. Google's context caching is similar. OpenAI has analogous features in development.

The blackboard is *perfect* cache material: it's a large, mostly-stable prefix that every agent reads.

### The Mechanism

```
Turn 1, Agent A:
  [system prompt: 1,000 tokens] [blackboard: 1,098 tokens] [task: 200 tokens]
  → Full cost: 2,298 input tokens

Turn 1, Agent B (same blackboard, same system prompt):
  [system prompt: 1,000 tokens] [blackboard: 1,098 tokens] [task: 200 tokens]
  → Cache hit on [system + blackboard] prefix: 2,098 tokens at 1/10th cost
  → Effective cost: 210 + 200 = 410 input tokens (82% cheaper)

Turn 2, Agent A (blackboard updated slightly):
  [system prompt: 1,000 tokens] [blackboard v2: 1,120 tokens] [task: 200 tokens]
  → Cache hit on system prompt (1,000 tokens at 1/10th), blackboard is new
  → Effective cost: 100 + 1,120 + 200 = 1,420 tokens (38% cheaper)
```

### The Math

For Exp 02 (5 agents, 3 reads each, ~1,098 token blackboard):

```
Without caching:   5 × 3 × 1,098                    = 16,470 token-equivalents
With caching:      5 × 1 × 1,098 + 5 × 2 × 110     = 6,590 token-equivalents
                   (first reads full, rerereads cached)
Savings: 60%
```

But here's the critical part: **this composes with every other optimization.** Apply scoped reads + deltas + compact format from the design proposal AND caching:

```
v2 optimized + caching: 3,449 (first reads) + 600 × 0.1 (cached deltas) = 3,509 token-equivalents
Total savings vs. naive: 79%
```

And the implementation cost is *zero*. You just structure prompts so the shared prefix (system prompt + blackboard) comes first, and the per-agent content (task, recent messages) comes after.

### The Design Principle

**Put shared, stable content at the front of the prompt. Put per-agent, volatile content at the back.**

This is the opposite of how most agent frameworks are built (task first, context later). Inverting the prompt structure to be cache-friendly is perhaps the single highest-ROI change possible.

### Why This Is Radical

Because it suggests AECP's blackboard isn't just an *adequate* architecture — it might be *uniquely advantaged* for prompt caching. A shared blackboard that every agent reads with the same prefix is exactly what caching systems are designed to optimize. The more agents share the same view, the better the cache hit rate.

The design proposal's Solution 1 (scoped reads) *breaks* cache sharing — every agent gets a different view, destroying the common prefix. There's a direct tension:

> **Scoped reads save tokens per-agent but destroy cache hits across agents.**

The optimal strategy depends on the cache discount rate. At Anthropic's 90% discount:

```
Scoped, uncached:  4,538 tokens per first read (17% savings)
Unscoped, cached:  1,098 × 0.1 = 110 tokens per cached read
```

For re-reads, the unscoped-but-cached approach wins dramatically. The optimal hybrid: **full blackboard for first read (maximize cache priming), scoped deltas for subsequent reads (minimize per-read cost).**

### Concrete Recommendation

1. **Prompt structure:** `[system prompt] [full blackboard snapshot] [agent-specific suffix]`
2. **First read:** Full blackboard, primes the cache for all agents
3. **Subsequent reads:** Only the agent-specific suffix changes; the prefix is a cache hit
4. **When blackboard changes:** Append the delta to the agent-specific suffix, NOT rewrite the prefix
5. **Periodic rebase:** When deltas accumulate enough to exceed the original blackboard size, rebuild the prefix with the latest snapshot

This "append-only delta tail" pattern keeps the shared prefix stable (maximizing cache hits) while delivering fresh information cheaply.

---

## 2. The Orchestrator-as-Compiler: Zero Agent Reads

### The Insight

Why do agents read the blackboard at all? Because they need context to do their work. But what if they received that context *pre-compiled* into their prompt, with exactly the information they need and nothing more?

Currently: Each agent reads the whole blackboard → filters mentally → extracts what matters → does work.

Proposed: The orchestrator reads the blackboard once → compiles per-agent briefings → injects only relevant context → agents never see the blackboard directly.

### The Mechanism

```
┌─────────────────────────────────────────────────┐
│                  Orchestrator                     │
│  (reads full blackboard once: 1,098 tokens)      │
│                                                   │
│  Compiles:                                        │
│    dev-a-briefing: "Build models.py.              │
│      Contract: TaskStatus, Task, TaskQueue.       │
│      Priority: asc [1,10] default 5.              │
│      Transitions: PENDING→RUNNING→SUCCESS|FAILED" │
│      (~120 tokens)                                │
│                                                   │
│    tester-briefing: "Test task_queue package.      │
│      18 test cases. Contract: [interface].         │
│      All modules: models.py, engine.py, __init__" │
│      (~80 tokens)                                 │
└─────────────────────────────────────────────────┘
```

Total blackboard read cost: **1,098 tokens** (orchestrator only) + **~500 tokens** (compiled briefings for 5 agents) = **1,598 tokens.**

Compare to every agent reading: 5 × 1,098 = 5,490 tokens for a single read round.

### Why This Is Different From Scoped Reads

Scoped reads (design proposal Solution 1) let agents choose which sections to receive. But the agent still receives *raw blackboard sections* — verbose, unprocessed, containing information irrelevant to their specific sub-task within that section.

The orchestrator-as-compiler *transforms* the information. It doesn't just filter sections — it extracts the specific facts each agent needs, strips formatting overhead, resolves cross-references, and may rewrite content to match the agent's mental model.

A scoped read of the "decisions" section gives Dev A all 5 decision blocks (~394 tokens). The orchestrator gives Dev A a compiled briefing: "Priority asc [1,10] default 5, ties FIFO. Transitions: [graph]" (~50 tokens). Same information, 87% fewer tokens.

### The Cost: Orchestrator Reasoning Tokens

The orchestrator spends tokens compiling these briefings. Is that cheaper than agents reading raw data?

```
Orchestrator cost:
  Read blackboard:     1,098 input tokens
  Reasoning:           ~500 output tokens (generate 5 briefings)
  Total:               ~1,598 tokens

Agent-reads cost (AECP v1):
  5 agents × 1,098  =  5,490 input tokens

Agent-reads cost (AECP v2 scoped):
  4,538 input tokens (from design proposal)
```

The orchestrator-as-compiler is cheaper than v1 and competitive with v2 scoped — but with a crucial advantage: the compiled briefings are *higher quality* input. Agents receive exactly what they need in the format most useful for their task. This should improve task performance (fewer reasoning tokens needed downstream) even if the transport cost is similar.

### The Risk

The orchestrator becomes a bottleneck and a single point of failure. If it miscompiles a briefing — omitting a critical decision or misrepresenting a constraint — the agent produces wrong output. Mitigation:

- Agents can request the raw blackboard section via tool call (fallback)
- Briefings include a `source_sections` list so agents know what was compiled
- Critical sections (interface contract) are passed verbatim, not compiled

### The Hybrid

Use the orchestrator for *prose* sections (design decisions, findings, status) where compilation yields high compression. Pass *structured* sections (interface contract, assignment table) verbatim — these are already maximally dense.

```
Agent prompt = [system] + [compiled_briefing: ~100 tokens] + [raw_contract: ~406 tokens]
Total: ~506 tokens vs. ~1,098 for full blackboard. 54% savings.
```

---

## 3. Tool-Based Blackboard Access: Pay Per Query, Not Per Read

### The Insight

Every blackboard read today is injected into the prompt. The agent "reads" by having the content appear in its context window. This costs tokens whether or not the agent actually *uses* that information for the current step.

What if the blackboard was a **tool** instead of prompt content? The agent calls a function to query specific facts, and only the answer consumes tokens.

### The Mechanism

Instead of injecting the entire blackboard into the prompt:

```python
# Available tools for this agent:

def query_blackboard(question: str) -> str:
    """Ask a specific question about the project state.
    Examples:
      query_blackboard("What is the retry policy?")
      query_blackboard("What is Dev B's current status?")
      query_blackboard("What are the open findings?")
    Returns a concise answer."""

def get_section(section_id: str) -> str:
    """Get the raw content of a specific blackboard section.
    Available sections: task, decisions.priority, decisions.retry,
    decisions.timeout, decisions.concurrency, decisions.transitions,
    interface-contract, assignments, findings, metrics"""

def get_contract() -> str:
    """Get the typed interface contract (Python code)."""
```

Now the agent's prompt contains NO blackboard content. It contains tools. When the agent needs a fact, it queries for it.

### Token Cost Analysis

**Scenario: Dev A implementing models.py**

Without tool access (full blackboard in prompt):
```
Blackboard injected: 1,098 tokens (paid regardless of use)
```

With tool access (agent queries as needed):
```
Tool definitions in prompt:     ~150 tokens (fixed, cacheable)
Agent calls get_contract():     ~10 tokens (call) + ~406 tokens (response)
Agent calls query("priority?"): ~10 tokens (call) + ~20 tokens (response)
Agent calls query("transitions?"): ~10 tokens (call) + ~30 tokens (response)
Total: 150 + 10 + 406 + 10 + 20 + 10 + 30 = 636 tokens
```

**Savings: 42% for this agent.** But more importantly, if the agent doesn't need to check the retry policy or timeout behavior, it simply *doesn't call the tool*, and those tokens are never spent.

### The Key Advantage: Demand-Driven Token Spending

With prompt injection, tokens are spent regardless of relevance. With tool access, tokens are spent *only when the agent needs the information*. This is the difference between:

- **Eager evaluation:** Load everything into memory, hope it's useful
- **Lazy evaluation:** Load nothing, fetch on demand

For agents with narrow tasks (tester, single-module developer), lazy evaluation is dramatically cheaper. For agents with broad tasks (architect, reviewer), eager evaluation might be more efficient to avoid many small tool calls.

### The Hybrid: Minimal Prompt + Tool Fallback

Give each agent a *minimal* briefing in the prompt (compiled by orchestrator or by protocol), plus tool access for anything else:

```
Agent prompt:
  [system] +
  [briefing: "You're implementing models.py. Contract: {inline}.
   Priority: asc [1,10]. See tools for other details."] +
  [tools: query_blackboard, get_section]

Tokens: ~600 (briefing with contract) + ~150 (tools) = ~750
vs. 1,098 for full blackboard
```

The agent only queries tools if it encounters an edge case not covered by the briefing. Most of the time, the briefing is sufficient, and tool calls add zero cost.

### The Risk: Over-Querying

An anxious agent might call `query_blackboard()` for every decision, spending more tokens on tool calls than a single full read would cost. Mitigation:

1. Compile the most critical facts into the briefing (contract, assignment, key decisions)
2. Set a token budget for tool calls per agent
3. Use the `get_section()` tool (returns a full section once) rather than many `query_blackboard()` calls when the agent needs deep context

### The Deeper Implication

Tool-based access means the blackboard doesn't need to be text at all. It could be a **structured database** that responds to queries. The "blackboard" becomes a key-value store:

```
GET /bb/decisions/retry/max         → "3"
GET /bb/decisions/retry/backoff     → "exponential, base=1.0s"
GET /bb/assignments?status=pending  → [{"id": "review", "owner": "reviewer"}]
```

Each response is a few tokens. The total cost is proportional to *queries made*, not *state size*. This fundamentally breaks the quadratic scaling law identified in the design proposal:

```
Old: C_bb = N × R × B(N)           — quadratic in agents × blackboard size
New: C_bb = Σ_agents Q(a) × avg_response_size  — linear in queries made
```

---

## 4. The Reactive Push Architecture: No Reads, Only Events

### The Insight

Pull architectures (agent reads blackboard) waste tokens because agents don't know what changed. Push architectures (system notifies agents) waste zero tokens on unchanged state.

What if agents never read the blackboard? Instead, they *subscribe* to typed events and receive notifications only when something relevant changes.

### The Mechanism

```
SESSION_START:
  Orchestrator → Dev A:
    {type: "assignment", task: "models.py", contract: <inline>}
    {type: "decision", topic: "priority", value: "asc [1,10] default 5"}
    {type: "decision", topic: "transitions", value: <state graph>}
    Total: ~250 tokens of targeted initial context

DURING_WORK:
  Architect freezes retry policy:
    → No notification to Dev A (not subscribed to retry)
    → Notification to Dev B: {type: "frozen", section: "retry"}

  Dev A completes models.py:
    → Dev A writes: {type: "status", task: "models", status: "done"}
    → Notification to Reviewer: {type: "ready_for_review", task: "models", file: "M:MOD"}
    → Notification to Tester: {type: "module_ready", task: "models"}
    → No notification to Dev B (not waiting on models)
```

### Why This Is Different From Delta Subscriptions

Delta subscriptions (design proposal Solution 2) still require the agent to *request* a delta. The agent initiates a read, the system returns changes. The agent must decide *when* to read.

The reactive push model inverts this: the *system* decides when to notify the agent. The agent never initiates a read. Information arrives exactly when it's relevant, in the minimum viable format.

This is the difference between polling and event-driven programming. In a polling architecture, even efficient polling (deltas) has a base cost per poll. In an event-driven architecture, silent agents consume zero coordination tokens.

### Token Cost for Exp 02

```
Initial assignments:  5 agents × ~250 tokens avg    = 1,250 tokens
Events during work:   ~10 events × ~30 tokens avg   =   300 tokens
Total coordination tokens:                           = 1,550 tokens

vs. AECP v1 naive:   16,470 tokens
vs. AECP v2 scoped+delta+compact: 4,049 tokens
vs. Reactive push:   1,550 tokens   ← 91% cheaper than v1, 62% cheaper than v2
```

### The Information-Theoretic Argument

The reactive push model approaches the **information-theoretic minimum** for coordination. Each agent receives exactly and only:

1. Their assignment (one-time, ~50 tokens)
2. The interface contract (one-time, ~406 tokens shared/cached)
3. Events that change their decision space (~30 tokens each, only when relevant)

No redundancy, no irrelevant sections, no re-reading stable state. Every token carries novel, actionable information for that specific agent.

### Implementation Sketch

```python
class EventBus:
    """Replaces the blackboard for inter-agent coordination."""

    def __init__(self):
        self.subscriptions: dict[str, list[AgentId]] = {}
        self.event_log: list[Event] = []

    def subscribe(self, agent: AgentId, topics: list[str]):
        for topic in topics:
            self.subscriptions.setdefault(topic, []).append(agent)

    def publish(self, event: Event):
        self.event_log.append(event)
        recipients = self.subscriptions.get(event.topic, [])
        for agent in recipients:
            agent.inject_event(event)  # adds to agent's next prompt suffix

    def replay(self, agent: AgentId, since: int = 0) -> list[Event]:
        """For crash recovery: replay missed events."""
        return [e for e in self.event_log[since:]
                if agent in self.subscriptions.get(e.topic, [])]
```

### The Risk: Lost Context

An event-driven agent has no global picture. It only knows what it's been told. If it needs context it wasn't subscribed to, it's stuck. Mitigations:

1. **Escape hatch:** Any agent can request a full blackboard read via tool call (rare, expensive, but available)
2. **Rich initial assignment:** Front-load context at task start when it's cheap
3. **Cross-references in events:** Events include enough context to be self-contained

### The Philosophical Shift

The blackboard is a *document* — agents read it like a newspaper. The event bus is a *nervous system* — agents receive impulses. Documents assume you don't know what's relevant until you read everything. Nervous systems assume the system knows what's relevant and routes accordingly.

For well-structured tasks (which AECP already targets), the system *does* know what's relevant — the task assignment and subscription topology encode it.

---

## 5. First-Principles: The Information-Theoretic Minimum

### Framing the Question

For N agents coordinating on a task, what is the *theoretical minimum* number of tokens they must exchange to produce correct, coherent output?

### Decomposition

Total coordination information = the mutual information between agents' subtasks.

```
I_coord = Σ_{i<j} I(T_i; T_j)

Where:
  T_i = agent i's subtask
  I(T_i; T_j) = mutual information between subtasks i and j
```

For **perfectly independent** subtasks: `I_coord = 0`. No coordination needed.
For **perfectly coupled** subtasks: `I_coord = H(T)`. Everyone needs to know everything.

Real tasks fall in between, and the key variable is **interface complexity**.

### The Interface Decomposition

In a well-structured multi-agent task (like the experiments), agents interact *only* through defined interfaces. The coordination information is bounded by the interface specification:

```
I_coord ≤ Σ_interfaces |interface_k|

Where |interface_k| = tokens needed to fully specify interface k
```

For Exp 02 (5 agents building a task queue):

```
Interfaces:
  1. TaskStatus enum definition:     ~30 tokens
  2. Task dataclass definition:      ~80 tokens
  3. TaskQueue protocol definition:  ~120 tokens
  4. Module file boundaries:         ~20 tokens
  5. Test expectations:              ~50 tokens
  TOTAL interface complexity:        ~300 tokens
```

This is the **theoretical minimum** coordination cost: 300 tokens shared across all agents.

### Comparison to Actual Costs

```
Theoretical minimum:              300 tokens (interface specs only)
Reactive push (Idea 4):        1,550 tokens (5.2× minimum)
AECP v2 optimized:             4,049 tokens (13.5× minimum)
AECP v1 naive:                16,470 tokens (54.9× minimum)
English baseline:             44,800 tokens (149× minimum)
```

The gap between the theoretical minimum and even the best proposed approach is **5×**. Where do the extra tokens go?

1. **Decision context** (~200 tokens): Agents need to know *why* decisions were made, not just *what* they are, to handle edge cases. The interface alone doesn't explain that `priority=asc` means "lower number = higher priority."
2. **Assignment routing** (~100 tokens): Agents need to know what *they* are supposed to do. The interface is shared; the assignment is personal.
3. **Status coordination** (~150 tokens): Agents need to know when dependencies are met. "Models.py is done" triggers the reviewer.
4. **Format overhead** (~300 tokens): Token boundaries, JSON syntax, key names, formatting.
5. **Redundancy for robustness** (~400 tokens): Some duplication is intentional — ensuring critical facts survive context truncation.

### The Insight: We're Already Close

The reactive push architecture (Idea 4) is within 5× of the theoretical minimum. Getting closer requires either:

- Eliminating format overhead (binary protocols — but LLMs can't parse those)
- Eliminating redundancy (risky — one missed fact causes cascading errors)
- Eliminating decision context (risky — agents make wrong edge-case decisions)

**The practical minimum is probably 3–4× the theoretical minimum.** We're within striking distance with the reactive push model.

### The 5-Agent Scaling Law

For N agents with I interfaces of average complexity C tokens:

```
Minimum coordination tokens = I × C × f(N)

Where f(N) = how many agents need each interface:
  f(N) = 2 for point-to-point interfaces (producer + consumer)
  f(N) = N for broadcast interfaces (everyone needs it)
  f(N) ≈ √N for typical hierarchical architectures
```

For Exp 02: I=5, C≈60, f(5)≈2.5 → **750 tokens.** The reactive push estimate of 1,550 is about 2× this — the gap is format overhead and status events.

---

## 6. Prompt Caching as an Architectural Primitive

### Beyond "Use Caching": Design *For* Caching

Idea 1 treats prompt caching as an optimization. This idea treats it as an **architectural primitive** — the foundation on which the entire coordination protocol is built.

### The Core Mechanism: The Shared Prefix Protocol

```
ALL agent prompts have this structure:

┌─────────────────────────────────────────────────────────┐
│  ZONE 1: Shared Immutable Prefix (cached, cost: ≈0)    │
│  ┌─────────────────────────────────────────────────┐    │
│  │ System prompt (role, rules, tools)              │    │
│  │ Project specification (from task description)    │    │
│  │ Interface contract (typed Python code)           │    │
│  │ Architecture overview (module boundaries)        │    │
│  │ Design decisions (frozen, all of them)           │    │
│  │ TOTAL: ~2,000 tokens (paid once, cached for all) │   │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  ZONE 2: Shared Mutable Prefix (cached within window)   │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Assignment table (current statuses)              │    │
│  │ Open findings                                    │    │
│  │ TOTAL: ~300 tokens (refreshed when state changes)│   │
│  └─────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  ZONE 3: Agent-Specific Suffix (never cached, full cost)│
│  ┌─────────────────────────────────────────────────┐    │
│  │ "Your assignment: implement models.py"           │    │
│  │ Recent events relevant to this agent             │    │
│  │ File contents being worked on                    │    │
│  │ TOTAL: varies per agent, ~200-1000 tokens        │   │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### The Economic Model

```
Assume: Anthropic caching = 10% of normal input cost for cache hits,
        25% write premium for first cache write

Agent 1, Turn 1 (cache miss — first write):
  Zone 1: 2,000 tokens × 1.25 = 2,500 token-equivalents (cache write)
  Zone 2: 300 tokens × 1.25   = 375 token-equivalents
  Zone 3: 500 tokens × 1.0    = 500 token-equivalents
  Total: 3,375 token-equivalents

Agent 2, Turn 1 (cache hit — same prefix):
  Zone 1: 2,000 tokens × 0.10 = 200 token-equivalents (cache hit!)
  Zone 2: 300 tokens × 0.10   = 30 token-equivalents
  Zone 3: 400 tokens × 1.0    = 400 token-equivalents
  Total: 630 token-equivalents

Agents 3-5, Turn 1 (cache hits):
  ~600 token-equivalents each

TOTAL for 5 agents, Turn 1:
  3,375 + 630 + 600 + 600 + 600 = 5,805 token-equivalents

Without caching (all full-price reads):
  5 × (2,000 + 300 + 500) = 14,000 token-equivalents

Savings: 59% on Turn 1 alone
```

And it gets better over time. Turns 2–N, the prefix is already cached:

```
Agents 1-5, Turn 2 (Zone 1 cached, Zone 2 refreshed, Zone 3 new):
  Zone 1: 2,000 × 0.10 = 200 each → 1,000 total
  Zone 2: 300 × 1.25 = 375 (one write) + 4 × 300 × 0.10 = 120 → 495 total
  Zone 3: ~500 × 1.0 each → 2,500 total
  Total Turn 2: 3,995 token-equivalents

Without caching: 14,000 token-equivalents
Savings: 71% on Turn 2
```

### The Design Rule

**Every protocol decision should be evaluated against its caching impact.**

- Adding a per-agent scope to the blackboard? That *breaks* the shared prefix. Bad for caching.
- Putting design decisions in Zone 1 (immutable)? Perfect — cached across all agents and turns.
- Changing the assignment table frequently? Move it to Zone 2. Updates break the cache for that zone but Zone 1 stays cached.
- Agent-specific tool results? Zone 3. Never expected to cache.

### The Heretical Implication

The design proposal's Solution 1 (scoped reads) might be **counterproductive** in a cache-aware architecture. Scoped reads give each agent a different blackboard view — destroying the shared prefix that makes caching work.

At 90% cache discount, the math is clear:

```
5 agents, 3 reads, scoped (no caching possible — each view is unique):
  13,614 token-equivalents (design proposal §2, Solution 1)

5 agents, 3 reads, unscoped (full BB, but cached):
  First reads: 1 × 1,098 × 1.25 + 4 × 1,098 × 0.10 = 1,812 token-equiv
  Rereads:     5 × 2 × 1,098 × 0.10 = 1,098 token-equiv
  Total: 2,910 token-equivalents

Unscoped + cached is 4.7× cheaper than scoped + uncached.
```

**Don't scope. Cache.**

The entire Section 2 of the design proposal (seven solutions for reducing read size) may be solving the wrong problem. If you can make reads *cheap* rather than *small*, the read amplification problem dissolves.

(Nuance: This analysis assumes all agents run on the same provider with good caching. Heterogeneous deployments may not benefit. And scoped reads *do* reduce attention dilution from irrelevant content, which affects reasoning quality independent of token cost. But for pure cost optimization, caching dominates.)

---

## 7. Contract-Only Coordination: Kill the Blackboard Entirely

### The Heresy

What if we don't need a blackboard at all?

Look at what actually matters in AECP's experiments. The blackboard contains:
1. Design decisions (priority, retry, timeout, concurrency, transitions)
2. Interface contract (typed Python code)
3. Assignments (who does what)
4. Findings (code review results)
5. Metrics (message counts)

Items 2 and 3 are the only *structurally necessary* ones. Design decisions could be embedded in code comments. Findings could be direct messages. Metrics are observational.

What if the **contract IS the coordination mechanism**?

### The Mechanism

```python
# file: contracts/task_queue.py
# This file IS the blackboard. It's code. It's the spec. It's the coordination.

"""
Task Queue Library Contract
===========================
ASSIGNMENTS:
  models.py → dev-a | engine.py → dev-b | tests → tester | review → reviewer
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Protocol, Callable, Any

class TaskStatus(Enum):
    """States: PENDING → RUNNING → SUCCESS|FAILED|TIMED_OUT|CANCELLED
    From RUNNING: can go to RETRYING (max 3, exp backoff 1s base)
    From RETRYING: goes back to RUNNING"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class Priority:
    """Ascending: lower number = higher priority. Range [1,10], default 5.
    Ties broken by submitted_at (FIFO). Invalid → InvalidPriorityError."""
    MIN = 1
    MAX = 10
    DEFAULT = 5

@dataclass
class Task:
    """Retry: max 3, exponential backoff (1s * 2^attempt).
    Timeout: default 30.0s, None = no timeout, on_timeout → TIMED_OUT."""
    id: str
    callable: Callable[..., Any]
    priority: int = Priority.DEFAULT
    max_retries: int = 3
    timeout: float | None = 30.0
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    error: str | None = None

class TaskQueue(Protocol):
    def submit(self, task: Task) -> str: ...
    def cancel(self, task_id: str) -> bool: ...
    def get_status(self, task_id: str) -> TaskStatus: ...
    def start(self, workers: int = 4) -> None: ...  # ThreadPoolExecutor, daemon
    def stop(self, wait: bool = True, cancel_pending: bool = True) -> None: ...
```

### What Disappeared

The entire Markdown blackboard is gone. Every design decision is a code comment or a type annotation on the contract file. The contract file is:

- **~350 tokens** (vs. ~1,098 for the full Markdown blackboard)
- **Executable** (type checkers validate implementations against it)
- **Self-documenting** (code IS the documentation)
- **Single source of truth** (no separate blackboard to keep in sync)

This isn't a new idea — it's AECP's own "format-as-meaning" principle (P8), taken to its logical extreme. The design proposal treats the interface contract as one *section* of the blackboard. What if it's the *entire* blackboard?

### Token Cost

```
Contract-only coordination:
  5 agents × 1 read × 350 tokens = 1,750 tokens (first read)
  + prompt caching: 350 × 1.25 + 4 × 350 × 0.10 = 578 token-equivalents
  + status events: ~10 × 30 tokens = 300 tokens
  Total: ~878 token-equivalents

Compare:
  AECP v1 naive:         16,470 tokens
  AECP v2 optimized:      4,049 tokens
  Reactive push:          1,550 tokens
  Contract-only + cache:    878 token-equivalents

That's 95% cheaper than v1. 78% cheaper than v2. 43% cheaper than reactive push.
```

### The Limitation

Not every coordination need can be expressed as typed code. When the architect says "retry policy: exponential backoff with base_delay * 2^attempt where base_delay=1.0s," that translates beautifully to code. But what about:

- "Dev B should implement the engine module because it requires threading expertise"
- "The reviewer found an off-by-one bug in retries_remaining"
- "The tester should focus on edge cases around timeout + retry interactions"

These are *assignment*, *finding*, and *prioritization* information. They don't fit naturally in a typed interface. You could put them in docstrings, but that starts to look like... a blackboard with extra steps.

### The Synthesis

Use the contract as the **primary** coordination mechanism for *what to build*. Use lightweight events (Idea 4) for *who does what* and *what went wrong*. Kill the Markdown blackboard entirely.

```
Coordination = Contract (what) + Events (who/when/status)
Cost         = ~350 tokens     + ~300 tokens = ~650 tokens
```

---

## 8. Speculative Execution: Don't Coordinate, Reconcile

### The Wildest Idea

What if agents don't coordinate at all?

Give each agent their task and the interface contract. Let them work independently. When they're all done, run the tests. If everything passes, you're done. If not, a reconciliation agent fixes the conflicts.

### Why This Might Work

In Exp 01 (well-defined spec), AECP agents sent 5 messages total — one completion signal each. No agent needed information from another agent during execution. They could have worked in complete isolation with identical results.

The blackboard's value was *upfront* — the interface contract and design decisions were set before any agent started working. Once work began, coordination was unnecessary.

For well-decomposed tasks:

```
P(conflict | good contract) ≈ 0.05–0.15

Expected cost:
  No-coordination path: just run agents, 0 coordination tokens
  Conflict resolution: ~500 tokens per conflict (small model reads both files, suggests fix)

  E[coordination_cost] = 0 + P(conflict) × 500
                        = 0.10 × 500 = 50 tokens

Compare to: 1,550 tokens (reactive push) or 4,049 tokens (v2 optimized)
```

### When This Fails

For Exp 02 (ambiguous spec), agents *need* the design decisions to resolve ambiguity. Without the blackboard, each agent interprets ambiguities differently. You get 5 different implementations that don't interoperate.

The key variable is **specification completeness**. If the spec + contract resolves all ambiguities, speculative execution works. If not, it fails catastrophically.

### The Hybrid: Speculate-Then-Coordinate

```
Phase 1: Architect resolves ambiguities → produces contract (~500 orchestration tokens)
Phase 2: Agents work independently from contract (0 coordination tokens)
Phase 3: Run tests. If failures, a reconciliation agent fixes (expected: ~50 tokens)

Total: ~550 tokens for the full task
```

This is essentially AECP's existing workflow, but with the explicit recognition that Phase 2 requires *zero* inter-agent communication if Phase 1 is done well. The blackboard is unnecessary during execution — it was only useful during design.

### The Insight

The blackboard is a **design-time** artifact, not a **runtime** artifact. Once design decisions are made and the contract is published, agents don't need to read the blackboard again. They need the contract (their "executable spec") and their assignment. That's it.

The design proposal optimizes runtime reads. This idea eliminates them by recognizing they shouldn't exist.

---

## 9. Hierarchical Agent Topology: Coordination Through Structure

### The Insight

All previous ideas optimize the *channel* (how agents communicate). This idea optimizes the *topology* (which agents need to communicate at all).

A flat 5-agent team has O(N²) potential communication paths. A hierarchical team has O(N).

### The Mechanism

```
Current (flat):
  Every agent can message every other agent.
  Every agent reads the global blackboard.
  Coordination cost: O(N² × B)

Hierarchical:
  Architect → [Dev A, Dev B]     (tree structure)
  Reviewer  → [Dev A, Dev B]     (separate tree)
  Tester    → [Reviewer]         (chain)

  Each agent only receives information from its parent/children.
  No global blackboard — each edge has a minimal interface.
```

### Token Math for Exp 02

```
Flat (AECP v1):
  Blackboard: 1,098 tokens × 5 agents × 3 reads = 16,470 tokens
  Every agent sees everything.

Hierarchical:
  Architect → Dev A: contract + priority + transitions = 250 tokens
  Architect → Dev B: contract + all engine decisions = 400 tokens
  Dev A → Reviewer: "models.py done" = 10 tokens
  Dev B → Reviewer: "engine.py done" = 10 tokens
  Reviewer → Tester: "approved with 2 minor findings" = 30 tokens
  TOTAL: 700 tokens
```

### Why This Works

In a well-structured task, most agents only interact with their immediate neighbors in the dependency graph. Dev A never needs to know about Dev B's retry implementation. The Tester never needs to know about the architect's decision rationale. The current blackboard forces everyone to read everything because it's a *shared monolith*.

A hierarchical topology replaces the monolith with **point-to-point channels** that carry only the information relevant to each edge.

### The Cost: Reduced Flexibility

In a flat topology, any agent can discover any fact. If Dev A unexpectedly needs the retry policy (maybe they're implementing an edge case that interacts with retries), they just read it from the blackboard. In a hierarchical topology, they'd have to ask their parent (the architect), adding a round-trip.

For well-structured tasks, this almost never happens. For poorly-structured or evolving tasks, it's a significant limitation.

### The Synthesis: Hierarchical by Default, Flat on Demand

```
Default: Each agent sees only its edges in the dependency graph.
Fallback: Any agent can query the full blackboard via tool call (expensive, logged).

If tool-call frequency exceeds threshold → task decomposition was bad.
The tool call becomes a signal to restructure.
```

---

## 10. Comparison Matrix

| Idea | Token Savings vs v1 | Token Savings vs v2 | Complexity | Risk | Best For |
|------|---------------------|---------------------|------------|------|----------|
| 1. Prompt Caching | 60–82% | 0–40% (composes) | Zero | Low | Everything (deploy immediately) |
| 2. Orchestrator-as-Compiler | 70–85% | 30–50% | Medium | Medium (miscompilation) | Large teams, broad tasks |
| 3. Tool-Based Access | 42–70% | 0–30% | Medium | Medium (over-querying) | Agents with narrow tasks |
| 4. Reactive Push | 91% | 62% | High | Medium (lost context) | Well-structured tasks |
| 5. Info-Theoretic Min | (theoretical limit) | — | — | — | Understanding the ceiling |
| 6. Cache-First Architecture | 80–90% | 60–75% | Low | Low | All provider-supported deployments |
| 7. Contract-Only | 95% | 78% | Low | High (limited expressiveness) | Typed, well-specified tasks |
| 8. Speculative Execution | 97% | 86% | Low | High (needs great specs) | Independent subtasks |
| 9. Hierarchical Topology | 96% | 83% | Medium | Medium (flexibility loss) | Large teams, clear decomposition |

---

## 11. The Recommended Radical Path

If I had to pick one path to pursue, here's what I'd actually ship — a **layered approach** that captures the biggest wins first:

### Layer 0: Prompt Structure for Caching (Ship Immediately, 0 Engineering)

Restructure all agent prompts: `[shared prefix: system + contract + decisions] [agent suffix: assignment + events]`. This alone saves 60–80% on input token costs via provider caching. The design proposal's seven solutions are additive on top of this, but caching alone may render some of them unnecessary.

### Layer 1: Contract-as-Blackboard (Ship in v2.0, Low Engineering)

Collapse the Markdown blackboard into the typed contract file with design decisions as structured comments. Reduces coordination content from ~1,098 tokens to ~350 tokens. Eliminates the need for a separate blackboard format, versioning, delta tracking — the contract *is* the state.

### Layer 2: Event-Driven Status (Ship in v2.0, Medium Engineering)

Replace blackboard reads for status tracking with push events. Agents receive typed notifications: `{task: "models", status: "done"}`, `{finding: "F-1", severity: "minor", file: "models.py"}`. No polling, no re-reading.

### Layer 3: Tool Fallback (Ship in v2.1, Low Engineering)

Give agents a `query_project_state(question)` tool for when they need context not covered by their initial assignment or events. This handles edge cases without front-loading every possible fact into every agent's context.

### Combined Estimated Cost for Exp 02 Task

```
Contract in shared cached prefix:  350 × 0.10 × 5 agents = 175 token-equivalents
Agent-specific suffixes:           200 × 5 = 1,000 token-equivalents
Status events:                     10 × 30 = 300 tokens
Tool queries (estimated 2 total):  2 × 50 = 100 tokens
                                   TOTAL ≈ 1,575 token-equivalents

vs. English baseline: 44,800 tokens → 28× cheaper
vs. AECP v1 naive:    16,470 tokens → 10× cheaper
vs. AECP v2 proposed:  4,049 tokens →  3× cheaper
```

---

## 12. What Would Change My Mind

1. **If caching doesn't work as modeled:** Provider caching may have minimum prefix lengths, TTL limits, or consistency requirements that reduce effective hit rates. Need empirical measurement.

2. **If agents genuinely need global context:** If it turns out that agents perform significantly better when they see the full blackboard (due to incidental context helping with edge cases), then reducing visibility trades token cost for task quality. Need A/B testing on output quality, not just token counts.

3. **If the task decomposition is poor:** All of these ideas assume tasks can be cleanly decomposed into independent subtasks with narrow interfaces. If the real world has more cross-cutting concerns than our experiments show, the flat blackboard's "everyone sees everything" might be a feature, not a bug.

4. **If reasoning tokens dominate:** If 80% of total cost is the agent's internal chain-of-thought reasoning, then optimizing coordination tokens (the other 20%) has limited impact. We should measure C_reason to know whether coordination optimization is even the right lever.

---

## 13. The Biggest Insight

The design proposal frames the problem as: "The blackboard has a read cost problem. How do we reduce read costs?"

The deeper framing is: **"Coordination has a cost. What's the minimum coordination that produces correct output?"**

AECP v1 discovered that the minimum is much less than English assumes (silence = working, shared state > messages). The design proposal discovers that shared state has its own cost. The radical answer is:

> **The minimum coordination is: one contract + N assignments + K events, where K is the number of state changes that actually affect another agent's work.**

For well-structured tasks, K is very small (often < 10 events for a 5-agent team). The total coordination cost is dominated by the contract — which is both necessary and sufficient.

Everything else — the Markdown blackboard, the section headers, the design decision prose, the metrics, the message counts — is scaffolding. Useful during the *design* of the protocol, but not necessary for its *execution*.

The blackboard was never the product. The *contract* was the product. The blackboard was just an inefficient way to get to the contract.
