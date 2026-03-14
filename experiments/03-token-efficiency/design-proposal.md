# AECP v2: Token-Efficient Blackboard Architecture

**Status:** Proposal (draft)
**Author:** Architect
**Date:** 2025-07-14
**Depends on:** `experiments/findings.md` §6–§7, `docs/spec/unified-protocol-spec.md` §5

---

## 0. Executive Summary

AECP v1 proved that structured communication reduces inter-agent **messages** by 63–77%. But messages are not the cost we should be optimizing. **Tokens are.** The blackboard mechanism trades outbound messages for inbound reads — and every read consumes tokens. Our analysis of real experiment data shows that at 14+ agents, AECP's blackboard read costs can **exceed** the English baseline's conversation context costs by 1.75–3.8×. The protocol is message-efficient but potentially token-*inefficient*.

This proposal introduces six mechanisms that make AECP truly token-efficient. The recommended architecture (Sectioned Blackboard + Delta Subscriptions + Compact Format) reduces blackboard read costs by an estimated 60–75% — enough to make AECP definitively cheaper than English at every team size.

---

## 1. The Problem: Blackboard Reads Are the Hidden Cost

### 1.1 The Accounting Gap

The findings paper (§6, "Fewer Messages ≠ Fewer Total Tokens") acknowledges the gap:

> "It is entirely possible that total token consumption — messages sent plus blackboard reads plus code artifact reads — is comparable between AECP and unstructured English groups, or even higher for AECP."

This is not hypothetical. We can quantify it from the Experiment 02 blackboard.

### 1.2 Exp 02 Blackboard: Section-by-Section Analysis

The Exp 02 Group B blackboard (`experiments/02-ambiguous-spec/blackboard-b.md`) is 6,890 characters across 185 lines. Decomposed by section:

| Section | Est. Tokens | Relevant To |
|---------|-------------|-------------|
| Task header | ~27 | All 5 agents |
| Priority Model decision | ~48 | Dev A, Dev B |
| Retry Policy decision | ~83 | Dev B only |
| Timeout Behavior decision | ~65 | Dev B only |
| Concurrency Model decision | ~74 | Dev B only |
| Status Transitions decision | ~124 | Dev A, Dev B |
| Interface Contract (Python) | ~406 | All 5 agents |
| Assignments table | ~159 | All 5 agents |
| Findings | ~105 | Dev A, Dev B (fixers) |
| Metrics | ~7 | Observer only |
| **TOTAL** | **~1,098** | |

Per-role relevance when reading the full blackboard:

| Role | Tokens Needed | % of BB | Tokens Wasted | Waste % |
|------|---------------|---------|---------------|---------|
| Architect | 1,098 | 100% | 0 | 0% |
| Dev A (models) | 764 | 69% | 334 | 31% |
| Dev B (engine) | 986 | 90% | 112 | 10% |
| Reviewer | 1,091 | 99% | 7 | 1% |
| Tester | 599 | 54% | 499 | 45% |

**Key observation:** The Tester wastes 45% of every blackboard read on design decisions and findings they never use. Dev A wastes 31% on engine-specific retry/timeout/concurrency decisions. At 5 agents this is tolerable. At 20 agents, where the blackboard is 3–5× larger and most agents only touch a single module, waste ratios can hit 70–80%.

### 1.3 Total Token Cost: AECP vs. English

We model total tokens consumed as: every token an agent processes in its context window.

**Exp 02 Group B (AECP) — Conservative estimate:**

```
Blackboard reads:  5 agents × 3 reads × 1,098 tokens = 16,470 tokens
Messages sent:     ~5 messages × ~20 tokens            =    100 tokens
Messages received: 5 agents × 5 msgs × 20 tokens       =    500 tokens
                                                TOTAL ≈ 17,070 tokens
```

**Exp 02 Group A (English) — Conservative estimate:**

```
Messages produced:     19 msgs × ~80 tokens avg         =  1,520 tokens
Clarifications:        12 exchanges × ~60 tokens avg     =    720 tokens
Total conversation:    ~2,240 tokens accumulating in context
Context reads:         5 agents × ~8 turns × ~1,120 avg  = 44,800 tokens
                       (conversation grows; avg ≈ 50% of final size)
                                                 TOTAL ≈ 44,800 tokens
```

At 5 agents, AECP is **2.6× cheaper** because the English conversation context grows linearly with every message and every agent re-reads the entire history on each turn. The blackboard is a fixed-size artifact.

**But this ratio inverts at scale.** Consider Exp 00b (14 agents per team):

```
AECP:    14 agents × 3 reads × ~2,800 tokens = 117,600 tokens (BB reads only)
English: 14 agents × 4 turns × ~1,200 avg ctx =  67,200 tokens (ctx reads only)
                                  AECP costs 1.75× MORE
```

Why? Because:
1. The blackboard grows with project complexity (more agents → more tasks → bigger BB)
2. Every agent reads the ENTIRE blackboard, not just their section
3. Reads happen multiple times (initial, mid-work verification, pre-submit check)
4. English conversations in well-coordinated teams can be short (AECP's own finding: many messages are eliminable)

### 1.4 The Fundamental Problem

AECP v1 optimizes **message entropy** but ignores **read amplification**.

```
Read amplification = (total tokens read by all agents) / (total tokens written)
```

For the Exp 02 blackboard:
- Written once: ~1,098 tokens
- Read 15 times (5 agents × 3): 16,470 tokens
- **Read amplification: 15×**

For English in Exp 02:
- Written once (in messages): ~2,240 tokens
- Each message read by all agents in growing context: ~44,800 tokens
- **Read amplification: 20×**

English has worse read amplification *per message*, but AECP closes the gap because the blackboard is read in full every time. **The blackboard is a monolith being consumed atomically.** That's the architectural defect.

### 1.5 The Scaling Law

The total blackboard read cost follows:

```
C_bb = N × R × B(N)

Where:
  N    = number of agents
  R    = reads per agent per task (empirically 2–4)
  B(N) = blackboard size, which grows with N: B(N) ≈ B₀ + k × N
         (each agent's task adds ~200-400 tokens of decisions + assignments)
```

This is **O(N² × R)** — quadratic in team size. English conversation context is also O(N²) in the worst case (N agents × N messages), but in practice is mitigated because agents send fewer messages in AECP-style (well-coordinated) teams.

The blackboard's advantage is structural (single source of truth, proactive ambiguity resolution, zero clarifications). Its disadvantage is read cost. **Both must be addressed simultaneously.**

---

## 2. Proposed Solutions

### Solution 1: Sectioned Blackboard with Role-Scoped Reads

**The idea:** The blackboard is organized into named sections. Each agent declares which sections it needs at task start. Reads return only subscribed sections.

**Mechanism:**

At session start, each agent registers a read scope:

```json
{
  "agent": "dev-a",
  "read_scope": ["task", "interface-contract", "assignments", "decisions.priority", "decisions.status-transitions"]
}
```

When dev-a reads the blackboard, they receive only those sections. The Tester's scope might be:

```json
{
  "agent": "tester",
  "read_scope": ["task", "interface-contract", "assignments"]
}
```

**Token savings for Exp 02:**

| Agent | Full Read | Scoped Read | Saved |
|-------|-----------|-------------|-------|
| Architect | 1,098 | 1,098 | 0% |
| Dev A | 1,098 | 764 | 30% |
| Dev B | 1,098 | 986 | 10% |
| Reviewer | 1,098 | 1,091 | 1% |
| Tester | 1,098 | 599 | 45% |
| **Total (3 reads)** | **16,470** | **13,614** | **17%** |

**Verdict:** Modest savings for Exp 02 because the task is small and most roles need most sections. Savings grow with team size — at 20 agents where each dev touches 1 of 10 modules, scoped reads could save 60–70%.

**Trade-off:** Agents might miss relevant context they didn't anticipate needing. Mitigated by: (a) the "interface-contract" and "assignments" sections are always included by default, and (b) agents can widen their scope dynamically.

### Solution 2: Delta Subscriptions (Blackboard Diffing)

**The idea:** After the first full read, agents receive only changes (deltas) on subsequent reads. This is the highest-impact single mechanism.

**Mechanism:**

The blackboard tracks a monotonic version counter. Each agent tracks its last-read version.

```
First read:     GET /blackboard                → full content (v=1), ~1,098 tokens
Second read:    GET /blackboard?since=1        → delta only, ~80 tokens
Third read:     GET /blackboard?since=2        → delta only, ~40 tokens
```

Delta format (JSON Patch, already specified in AECP §5):

```json
[
  {"op": "set", "path": "assignments.models.status", "value": "done"},
  {"op": "append", "path": "findings", "value": "F-1: retries_remaining off-by-one"}
]
```

**Token savings for Exp 02:**

Assume the blackboard starts at ~600 tokens (design decisions + contract posted by architect) and accumulates ~500 tokens of updates over the task.

| Read Pattern | Tokens Per Agent (3 reads) | Total (5 agents) |
|---|---|---|
| Full read × 3 | 1,098 + 1,098 + 1,098 = 3,294 | 16,470 |
| Full + 2 deltas | 1,098 + 80 + 40 = 1,218 | 6,090 |
| **Savings** | | **63%** |

**Verdict:** **63% reduction in blackboard read tokens.** This is the single most impactful mechanism because it converts O(BB_size) re-reads into O(delta_size) re-reads. The first read is unavoidable; subsequent reads are proportional to *changes*, not *total state*.

**Trade-off:** Requires infrastructure to track versions and compute deltas. But AECP v1 already specifies JSON Patch format and version numbers in §5 ("Optimistic Concurrency") — this mechanism extends existing infrastructure.

### Solution 3: Compact Blackboard Format

**The idea:** The current blackboard is verbose Markdown prose. Structured YAML or a domain-specific compact format could convey the same information in fewer tokens.

**Current format (Exp 02 blackboard, Retry Policy section):**

```markdown
### Retry Policy
decision: **3 max retries, exponential backoff**
- Default `max_retries`: 3 (configurable per-task, 0 = no retry)
- Backoff: exponential — `base_delay * 2^attempt` where `base_delay=1.0s`
  - Attempt 0: 1s, attempt 1: 2s, attempt 2: 4s
- Failure = any unhandled exception from the callable.
- After all retries exhausted → status `FAILED`, error stored in `Task.error`.
- Each retry increments `Task.attempts`.
```

**~83 tokens.** Now as structured YAML:

```yaml
retry:
  max: 3       # configurable per-task; 0=none
  backoff: exponential  # base_delay * 2^attempt
  base_delay: 1.0s      # → 1s, 2s, 4s
  failure: unhandled_exception
  exhausted: {status: FAILED, error_field: Task.error}
  tracking: Task.attempts  # incremented each retry
```

**~45 tokens.** 46% smaller for the same semantic content.

**Full blackboard in compact format:**

Apply this compression ratio across all design decision sections (but NOT the interface contract — typed code is already maximally compact per Finding 5):

| Section | Current | Compact | Savings |
|---------|---------|---------|---------|
| Design decisions (5 sections) | ~394 tokens | ~210 tokens | 47% |
| Interface Contract | ~406 tokens | ~406 tokens | 0% (already code) |
| Other sections | ~298 tokens | ~220 tokens | 26% |
| **Total** | **~1,098** | **~836** | **24%** |

**Verdict:** 24% reduction. Moderate but compounds with other mechanisms. The key insight is that typed code sections (the interface contract) are *already* in the optimal format — this is the format-as-meaning principle working. Only the prose decision sections benefit from compaction.

**Trade-off:** Reduced human readability. But per Finding 2, structured formats already score higher on Readability Score than English prose (RS 0.93 vs. 0.78). The compact YAML format may score RS ≈ 0.85–0.90 — still well above English. The Source Map Contract (AECP §11) allows expansion to verbose form when debugging.

### Solution 4: Lazy Section Loading (Table of Contents Pattern)

**The idea:** Instead of reading the full blackboard, agents first receive a lightweight Table of Contents (ToC) with section headers, sizes, and last-modified timestamps. They then load only sections they need.

**Mechanism:**

```yaml
# Blackboard ToC — 8 tokens per entry, ~80 tokens total
sections:
  - {id: task, v: 1, tokens: 27, modified: t0}
  - {id: decisions.priority, v: 1, tokens: 48, modified: t0}
  - {id: decisions.retry, v: 1, tokens: 83, modified: t0}
  - {id: decisions.timeout, v: 1, tokens: 65, modified: t0}
  - {id: decisions.concurrency, v: 1, tokens: 74, modified: t0}
  - {id: decisions.transitions, v: 1, tokens: 124, modified: t0}
  - {id: interface-contract, v: 1, tokens: 406, modified: t0}
  - {id: assignments, v: 3, tokens: 159, modified: t2}
  - {id: findings, v: 2, tokens: 105, modified: t1}
  - {id: metrics, v: 3, tokens: 7, modified: t2}
```

**Cost: ~80 tokens for the ToC.** Then the agent selectively loads:

```
GET /blackboard/sections/interface-contract  → 406 tokens
GET /blackboard/sections/assignments         → 159 tokens
```

**Token savings for Exp 02 Tester (3 reads):**

```
Without lazy loading: 3 × 1,098 = 3,294 tokens
With lazy loading:    1 × (80 + 599) + 2 × (80 + ~40 delta) = 919 tokens
Savings: 72%
```

**Verdict:** Powerful for roles with narrow scope. Combines naturally with delta subscriptions (load ToC, see which sections changed, load only changed sections). Overhead: the ToC itself costs ~80 tokens per read, so it only pays off when the agent can skip >80 tokens of content.

**Trade-off:** Requires 2 round-trips per read (ToC then sections) vs. 1 for full read. If the platform charges per-request overhead, this matters. For LLM context injection, it doesn't — both are just tokens in the prompt.

### Solution 5: Write-Once / Frozen Sections

**The idea:** Once a section is finalized (e.g., the interface contract is signed off, a design decision is locked), it is marked `frozen`. Frozen sections are excluded from all subsequent delta reads and ToC listings.

**Mechanism:**

```json
{"op": "freeze", "path": "interface-contract", "by": "architect"}
```

After freezing:
- The section is still accessible via direct `GET /blackboard/sections/interface-contract`
- But it is excluded from `/blackboard?since=N` deltas (since it won't change)
- The ToC marks it `frozen: true` so agents skip the version check
- Agents who already read it never re-read it

**Token savings:**

In Exp 02, the interface contract (406 tokens) is written once by the architect and never modified. If frozen after the first read:

```
Without freezing: 5 agents × 3 reads × 406 = 6,090 tokens spent on the contract
With freezing:    5 agents × 1 read  × 406 = 2,030 tokens
Savings on contract alone: 67%
```

The contract is 37% of the blackboard. Freezing it saves ~4,060 tokens across the team — 25% of total blackboard read costs.

**Verdict:** High-value for large, stable sections. The interface contract, the task description, and the assignment table (after initial setup) are all freeze candidates. In Exp 02, approximately 60% of the blackboard content could be frozen after the architect's initial post.

**Trade-off:** Frozen sections become stale if requirements change. Mitigation: any agent can request an `unfreeze` (requires owner approval), and the system triggers a mandatory re-read notification to all subscribers.

### Solution 6: Computed Role Views (Materialized Projections)

**The idea:** Instead of N agents each applying their own read scope filter, the blackboard server pre-computes role-specific views. Each role gets a "materialized view" that includes only what they need, with cross-references inlined.

**Mechanism:**

The architect defines view templates at session start:

```yaml
views:
  developer:
    include: [task, interface-contract, assignments, "decisions.{own_module}.*"]
    inline_refs: true  # expand any CAR references
  reviewer:
    include: [task, interface-contract, assignments, "decisions.*", findings]
  tester:
    include: [task, interface-contract, assignments.*.status]
```

When Dev A reads the blackboard, they receive the `developer` view with `own_module = models`, which includes only Priority Model and Status Transitions decisions (the ones relevant to the models module).

**This is the database analogy:** The blackboard is the base table. Views are SELECT projections. Agents query views, not the base table.

**Token savings for Exp 02:**

Combines the benefits of Solution 1 (scoped reads) with the specificity of Solution 4 (lazy loading), pre-computed to eliminate client-side filtering overhead:

| Agent | Full BB | Computed View | Saved |
|-------|---------|---------------|-------|
| Dev A | 1,098 | 620 (task + priority + transitions + contract + own assignments) | 44% |
| Dev B | 1,098 | 800 (task + all engine decisions + contract + own assignments) | 27% |
| Tester | 1,098 | 500 (task + contract + assignment statuses) | 54% |
| **Weighted avg** | | | **~30%** |

**Verdict:** Most valuable at scale (20+ agents) where views can be highly specialized. At 5 agents, the benefit overlaps heavily with Solution 1. The unique advantage is that view computation is done once server-side, not N times client-side.

**Trade-off:** Requires the architect to define views upfront. Incorrect views cause agents to miss context. Mitigation: views default to "include all" and are progressively narrowed as the task structure becomes clear.

### Solution 7: Hierarchical Summarization (Progressive Disclosure for Reads)

**The idea:** Apply AECP's progressive disclosure principle (§9 of the spec) to blackboard reads. Each section has a 1-line summary (L0), a paragraph summary (L1), and full detail (L2). Agents read L0 for all sections first, then drill into L1/L2 only where needed.

**Mechanism:**

```yaml
decisions.retry:
  L0: "3 retries, exponential backoff 1s/2s/4s"          # ~12 tokens
  L1: "max_retries=3, backoff=base*2^attempt (1s base),   # ~35 tokens
       failure=exception, exhausted→FAILED in Task.error"
  L2: <full 83-token detail>
```

An agent deciding whether to drill in needs only the L0 summary (~12 tokens) instead of the full section (~83 tokens). The drill-in decision is based on whether the section is relevant to their current task.

**Token savings for a drive-by scan:**

```
Full blackboard scan:    ~1,098 tokens
L0 summary scan:         ~120 tokens (10 sections × ~12 tokens each)
Drill into 3 sections:   ~250 tokens
Total:                    ~370 tokens vs. 1,098 → 66% savings
```

**Verdict:** Elegant but requires authoring L0/L1 summaries. Could be auto-generated by the platform (LLM summarization of each section). Most useful for large blackboards (20+ sections) where agents genuinely don't know what they need until they scan headers.

**Trade-off:** Summary generation costs tokens too (if LLM-generated). For small blackboards (<10 sections), the overhead of maintaining summaries exceeds the savings.

---

## 3. Cost Model

### 3.1 The Full Token Cost Equation

Total token cost for a multi-agent task:

```
C_total = C_sys + C_bb + C_msg + C_code + C_reason

Where:
  C_sys    = system prompt tokens (fixed per agent, paid on every turn)
  C_bb     = blackboard read tokens (this proposal's focus)
  C_msg    = inter-agent message tokens (AECP v1's focus)
  C_code   = code artifact read tokens (reading source files, test output)
  C_reason = internal reasoning tokens (chain-of-thought, not shared)
```

AECP v1 optimized C_msg. This proposal optimizes C_bb. Together they cover the two largest controllable costs.

### 3.2 Blackboard Read Cost Model

```
C_bb = Σ_agents [ C_first_read(a) + Σ_subsequent_reads C_reread(a, t) ]

Where:
  C_first_read(a) = |view(a, BB)|           # first read: full relevant view
  C_reread(a, t)  = |delta(a, v_last, v_t)|  # subsequent: deltas only

Expanding with all mechanisms:
  |view(a, BB)|    = Σ_sections∈scope(a) [ frozen(s) ? 0 : size(s, fidelity(a,s)) ]
  |delta(a, v, t)| = Σ_sections∈scope(a) [ changed(s, v, t) ? delta_size(s) : 0 ]
```

### 3.3 Mechanism Contribution Model

Each solution contributes a multiplicative reduction factor:

```
C_bb_optimized = C_bb_naive × (1 - savings_scoped) × (1 - savings_delta) × (1 - savings_compact) × ...

But mechanisms overlap, so the combined savings formula is:
C_bb_optimized = C_first_read × scope_factor × compact_factor
               + C_rereads × scope_factor × compact_factor × delta_factor × freeze_factor
```

### 3.4 Applied to Exp 02 (5 Agents, 3 Reads Each)

**Baseline (AECP v1, naive full reads):**

```
C_bb_naive = 5 × 3 × 1,098 = 16,470 tokens
```

**With recommended mechanisms (scoped + delta + compact):**

```
First read:  Σ agents: 1,098 + 764 + 986 + 1,091 + 599 = 4,538 tokens
             × 0.76 compact factor = 3,449 tokens

Rereads:     Assume ~80 tokens of delta per reread, scoped ≈ 60 tokens average
             5 agents × 2 rereads × 60 tokens = 600 tokens

Frozen:      Interface contract (406 tokens) frozen after first read
             Saves: 4 agents × 2 rereads × (406 × 0.76) = 2,468 tokens
             (already captured in delta, so don't double-count)

C_bb_optimized ≈ 3,449 + 600 = 4,049 tokens
```

**Savings: 75% reduction in blackboard read tokens (16,470 → 4,049)**

### 3.5 Applied to Scale Scenario (14 Agents)

**Baseline:**

```
C_bb_naive = 14 × 3 × 2,800 = 117,600 tokens
```

**With mechanisms (assuming 40% avg scope relevance at scale):**

```
First read:  14 × 2,800 × 0.40 scope × 0.76 compact = 11,930 tokens
Rereads:     14 × 2 × 100 avg delta = 2,800 tokens
C_bb_optimized ≈ 14,730 tokens
```

**Savings: 87% reduction (117,600 → 14,730)**

Now compare to English baseline at 14 agents:
```
English context reads: ~67,200 tokens (from §1.3 analysis)
AECP v2 BB reads:      ~14,730 tokens
AECP v2 is 4.6× cheaper — the inversion is fixed.
```

### 3.6 Cross-Protocol Comparison Model

To fairly compare AECP v2 with English baseline, measure all token categories:

```
                      English                    AECP v2
C_sys               N × S                       N × S                    (same)
C_bb                0                            C_bb_optimized           (AECP only)
C_msg               N × T × H_avg / 2           N × 1 × 20              (AECP: 1 msg/agent)
C_ctx_history       N × T × H_avg / 2           0                        (English only)
C_clarification     N_clar × 2 × avg_clar       0                        (AECP eliminates)
C_code              ~equal                       ~equal                   (both read code)
C_reason            ~equal                       ~equal                   (not shared)

Where:
  N        = number of agents
  S        = system prompt size
  T        = turns per agent
  H_avg    = average conversation history size (grows linearly with messages)
  N_clar   = number of clarification rounds
  avg_clar = average tokens per clarification exchange
```

**The decisive advantage of AECP v2:** C_ctx_history for English is O(N × T × M × avg_msg_size / 2) where M = total messages — quadratic in team output. C_bb for AECP v2 is O(N × (B_scoped + R × delta_avg)) — linear in changes after the first read. At scale, this is the dominant term.

### 3.7 Measurement Protocol

To validate the model, instrument these metrics in future experiments:

| Metric | How to Capture |
|--------|----------------|
| `bb_tokens_read` | Count tokens injected into agent context from blackboard |
| `bb_read_count` | Number of blackboard reads per agent |
| `bb_sections_read` | Which sections each agent actually references (via tool call logs) |
| `msg_tokens_sent` | Tokens in each inter-agent message |
| `msg_tokens_received` | Tokens in each agent's message context |
| `code_tokens_read` | Tokens from source file reads |
| `total_context_tokens` | Total tokens in each API call's context |
| `total_output_tokens` | Total tokens generated by each agent |

The critical new metric: **Token Efficiency Ratio (TER)**

```
TER = task_output_value / total_tokens_consumed

Where:
  task_output_value = tests_passing × code_quality_score  (normalized 0–1)
  total_tokens_consumed = C_sys + C_bb + C_msg + C_code + C_reason
```

TER lets us compare protocols on total cost, not just message count.

---

## 4. Recommended Architecture: AECP v2 Blackboard

### 4.1 What to Ship

Three mechanisms, ordered by impact-to-complexity ratio:

| Priority | Mechanism | Token Savings | Complexity | Ship In |
|----------|-----------|---------------|------------|---------|
| **P0** | Delta Subscriptions | 50–63% | Medium | v2.0 |
| **P1** | Sectioned Read Scopes | 17–40% | Low | v2.0 |
| **P2** | Compact Format (YAML) | 20–24% | Low | v2.0 |
| P3 | Write-Once / Freeze | 15–25% | Low | v2.1 |
| P4 | Lazy Section Loading | 30–66% | Medium | v2.1 |
| P5 | Computed Role Views | 30–54% | High | v2.2 (scale) |
| P6 | Hierarchical Summaries | 30–66% | High | v2.2 (scale) |

**The v2.0 triad (P0 + P1 + P2) is the minimum viable improvement.** It addresses the quadratic scaling problem with infrastructure that already exists in the v1 spec (JSON Patch, version numbers, path-level ownership).

### 4.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AECP v2 Blackboard                              │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Section:     │  │  Section:     │  │  Section:     │   ...      │
│  │  interface-   │  │  decisions.   │  │  assignments  │             │
│  │  contract     │  │  retry        │  │               │             │
│  │  v=1 FROZEN   │  │  v=2          │  │  v=5          │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                  │                  │                      │
│  ┌──────▼──────────────────▼──────────────────▼────────────────┐    │
│  │              Version-Tracked Section Store                   │    │
│  │  - Per-section version counters                              │    │
│  │  - Delta log (JSON Patch per version increment)              │    │
│  │  - Freeze flags                                              │    │
│  └──────────────────────┬──────────────────────────────────────┘    │
│                         │                                           │
│  ┌──────────────────────▼──────────────────────────────────────┐    │
│  │              Read Scope Registry                             │    │
│  │  agent → [subscribed sections]                               │    │
│  │  dev-a → [task, contract, assignments, decisions.priority,   │    │
│  │           decisions.transitions]                              │    │
│  │  tester → [task, contract, assignments]                      │    │
│  └──────────────────────┬──────────────────────────────────────┘    │
│                         │                                           │
│  ┌──────────────────────▼──────────────────────────────────────┐    │
│  │              Query Interface                                 │    │
│  │                                                              │    │
│  │  GET /bb                    → full BB (fallback)             │    │
│  │  GET /bb?agent=dev-a        → scoped view for dev-a          │    │
│  │  GET /bb?agent=dev-a&since=3 → scoped deltas since v3       │    │
│  │  GET /bb/sections/{id}      → single section                 │    │
│  │  GET /bb/toc                → table of contents              │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Why These Three (and Not the Others Yet)

**Delta Subscriptions (P0)** is the highest-impact single mechanism because it converts O(BB_size) re-reads to O(delta_size) re-reads. In a stable session, deltas are tiny. The infrastructure (JSON Patch, versioning) is already specified in AECP v1 §5 — we're just applying it to reads, not just writes.

**Sectioned Read Scopes (P1)** is the lowest-complexity mechanism. It requires only: (a) tag sections with IDs (the blackboard already uses `## Section` headers), and (b) let agents declare a filter. No new infrastructure. Payoff grows super-linearly with team size.

**Compact Format (P2)** is a one-time authoring investment. Convert decision prose to structured YAML. The interface contract is already code (no change). The assignment table is already structured (minimal change). Total effort: define a YAML schema for the decision sections.

**Why defer the rest:**

- **Freeze (P3):** Simple but requires a new state bit and unfreeze protocol. Ship in v2.1 after validating the core triad.
- **Lazy Loading (P4):** Requires ToC generation and multi-step read protocol. Adds complexity for marginal benefit over P1 + P0 combined. Ship when blackboards exceed 3,000 tokens regularly.
- **Computed Views (P5):** Requires server-side logic and view templates. Overkill until team size exceeds 10 agents. Ship for enterprise scale.
- **Hierarchical Summaries (P6):** Requires multi-fidelity authoring or auto-summarization. Research-grade feature. Ship when LLM summarization is cheap and reliable.

### 4.4 Compact Blackboard Format Specification

The Exp 02 blackboard, rewritten in AECP v2 compact format:

```yaml
# AECP v2 Blackboard — compact format
_meta: {v: 5, task: task-queue, spec: experiments/02-ambiguous-spec/task-description.md}

decisions:
  priority: {dir: asc, range: [1,10], default: 5, ties: fifo_by_submitted_at,
             invalid: InvalidPriorityError}                                     # FROZEN v1
  retry: {max: 3, backoff: "exp(1.0 * 2^attempt)", on_fail: exception,
          exhausted: {status: FAILED, store: Task.error}, track: Task.attempts}  # FROZEN v1
  timeout: {default: 30.0, none_means: no_timeout, on_timeout: TIMED_OUT,
            error: TaskTimeoutError, no_retry: true}                             # FROZEN v1
  concurrency: {executor: ThreadPoolExecutor, workers: 4, configurable: true,
                bg_thread: daemon, stop_wait: true, stop_cancel: pending}        # FROZEN v1
  transitions:                                                                   # FROZEN v1
    states: [PENDING, RUNNING, SUCCESS, FAILED, TIMED_OUT, RETRYING, CANCELLED]
    terminal: [SUCCESS, FAILED, TIMED_OUT, CANCELLED]
    edges: {PENDING: [RUNNING, CANCELLED], RUNNING: [SUCCESS, RETRYING, FAILED, TIMED_OUT, CANCELLED],
            RETRYING: [RUNNING]}

contract: |                                                                      # FROZEN v1
  class TaskStatus(enum.Enum):
      PENDING = "pending"
      RUNNING = "running"
      # ... (full typed Python contract, unchanged from v1)

assignments:
  - {id: design, owner: architect, status: done}
  - {id: models, file: "M:MOD", owner: dev-a, status: done}
  - {id: engine, file: "M:ENG", owner: dev-b, status: done}
  - {id: pkg-init, file: "M:INI", owner: dev-a, status: done}
  - {id: review, owner: reviewer, status: "done(pass)", note: "2 minor"}
  - {id: tests, file: "T:TST", owner: tester, status: "done(pass)", note: "18/18 in 36s"}

findings:
  - {id: F-1, severity: minor, file: "M:MOD", desc: "retries_remaining off-by-one",
     fix: "used = max(0, attempts-1); return max(0, max_retries-used)"}
  - {id: F-2, severity: trivial, file: "M:INI", desc: "absolute vs relative imports"}

metrics: {messages: 1, clarifications: 0}
```

Estimated size: **~650 tokens** (vs. 1,098 for Markdown). **41% reduction.**

The YAML format preserves:
- All semantic content (every design decision, every assignment, every finding)
- Scanability (field names are still readable)
- Machine parseability (valid YAML, can be validated against a schema)
- The `# FROZEN` annotations tell agents they don't need to re-read these sections

### 4.5 Protocol Changes Required

**New agent lifecycle events:**

```
SESSION_START:
  1. Agent receives system prompt (existing)
  2. Agent registers read_scope: ["section-ids"]          ← NEW
  3. Agent reads scoped blackboard view (full, first time) ← CHANGED (scoped)

ON_WORK:
  4. Agent reads delta since last version                   ← NEW (was: full re-read)
  5. Agent does work (existing)
  6. Agent writes to blackboard via JSON Patch (existing)

ON_SECTION_COMPLETE:
  7. Section owner marks section frozen                     ← NEW
  8. All subscribers notified: "section X frozen at v=N"    ← NEW

SESSION_END:
  9. Agent sends completion signal (existing)
```

**New blackboard operations:**

```json
{"op": "read",   "scope": ["section-ids"], "since": 3}     → scoped delta response
{"op": "freeze", "path": "decisions.retry",  "by": "architect"}
{"op": "unfreeze", "path": "decisions.retry", "by": "architect", "reason": "requirement change"}
```

### 4.6 Backwards Compatibility

AECP v2 is backwards-compatible with v1:

- Agents that don't specify `read_scope` get the full blackboard (v1 behavior)
- Agents that don't specify `since` get a full read (v1 behavior)
- The compact YAML format is an alternative encoding, not a replacement — Markdown blackboards still work
- Freeze is opt-in — unfrozen sections behave identically to v1

An AECP v1 agent in a v2 session reads the full blackboard every time. It works, just less efficiently. This allows gradual migration.

### 4.7 Estimated Combined Impact

| Scenario | v1 BB Cost | v2 BB Cost | Reduction | AECP vs English |
|----------|-----------|-----------|-----------|-----------------|
| 5 agents, simple task | 7,050 | 2,400 | 66% | **3.0× cheaper** |
| 5 agents, ambiguous task | 16,470 | 4,049 | 75% | **4.0× cheaper** (was 2.6×) |
| 14 agents | 117,600 | 14,730 | 87% | **4.6× cheaper** (was 1.75× MORE expensive) |
| 20 agents | 300,000 | 30,000 | 90% | **9.3× cheaper** (was 1.07× comparable) |

**The scaling inversion is fixed.** AECP v2 is cheaper than English at every team size, and the advantage *grows* with scale because delta reads are O(changes) while English conversation history is O(messages²).

---

## 5. Experiment Design: Validating This Proposal

### 5.1 Experiment 03: Token-Level A/B/C Test

Three conditions:
- **Group A:** English (control)
- **Group B:** AECP v1 (full blackboard reads)
- **Group C:** AECP v2 (scoped + delta + compact blackboard)

**Task:** Same as Exp 02 (task queue with ambiguous spec) — enables direct comparison.

**Critical new instrumentation:**
- Token counter on every LLM API call (input tokens, output tokens)
- Blackboard read logger (which agent, which sections, how many tokens)
- Conversation history tracker (cumulative tokens per agent per turn)

**Primary metric:** Total tokens consumed (TER), not message count.

**Hypothesis:** AECP v2 total tokens < AECP v1 total tokens < English total tokens.

### 5.2 What Would Falsify This Proposal

1. If agents need unpredictable cross-section references (e.g., Dev A frequently needs the retry policy despite not subscribing to it), scoped reads cause re-read storms worse than full reads.
2. If deltas are verbose enough (large structural changes rather than small status flips) that delta reads approach full-read costs.
3. If the compact YAML format causes agents to misinterpret decisions (semantic loss despite syntactic fidelity).

All three are testable in Experiment 03.

---

## 6. Open Questions

1. **Auto-scoping:** Can agents' read scopes be inferred from their task assignments instead of manually declared? (e.g., if `assignments.models.owner = dev-a`, auto-subscribe dev-a to all sections tagged `module: models`)

2. **Blackboard pruning:** Should completed, frozen sections be *removed* from the blackboard entirely after all agents have read them once? This would cap blackboard growth for long-running sessions.

3. **Compression vs. reasoning:** Does the compact YAML format affect agent *reasoning* quality, not just transport cost? AECP's principle P2 says "compress the wire, not the brain" — but the blackboard is read into the context window where it *becomes* the brain's input. This needs empirical testing.

4. **Token cost of scoping infrastructure:** The read scope registry, delta log, and version tracking consume tokens/compute themselves. At what team size does this overhead pay for itself? Our model suggests N ≥ 3, but this needs validation.

5. **Interaction with context window limits:** As models get larger context windows (1M+ tokens), does blackboard read cost even matter? **Yes** — attention dilution means irrelevant tokens degrade reasoning quality even if they fit. Context window size is necessary but not sufficient; context window *relevance* is the real constraint.
