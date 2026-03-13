# RS (Readability Score) — A/B Test Raw Scores

**Scorer:** Designer Agent (@53a180f5)  
**Rubric:** measurement.md §RS — R (Reconstructability 0.5) + S (Scannability 0.3) + A (Actionability 0.2)  
**Date:** 2026-03-13

---

## Methodology

Scored every available message from both groups. Where exact message text is unavailable (Group A messages not captured to file), I note this explicitly and score based on observed evidence from the observer's log and execution playbook context.

**Scoring approach:** Each message scored on:
- **R (0.0–1.0):** Can a new agent understand the full meaning without prior context?
- **S (0.0–1.0):** Can the key info be extracted in <5 seconds?
- **A (0.0–1.0):** Does the message make clear what action is needed?
- **RS = 0.5R + 0.3S + 0.2A**

---

## Group B: ab-aecp (AECP Treatment)

### Available Messages

**Data source:** ~~Blackboard self-reported 1 message.~~ **CORRECTED:** Lead observed **5 messages** in ab-aecp group. Self-reported blackboard metric was inaccurate. Messages verified by lead (source: `.flightdeck/shared/ab-test/report-review.md`).

**⚠️ CORRECTION (2026-03-13): Group B sent 5 messages, not 1. All metrics below updated accordingly.**

#### Message B1 (Architect → all)
**Content:** `{intent: 'DONE', task: 'design'}`

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R (Reconstructability) | 0.90 | Clear: design task is complete, contract is on the blackboard. A new agent knows exactly what happened and where to look. Minor deduction: doesn't say WHAT was designed — requires blackboard lookup for specifics. |
| S (Scannability) | 0.95 | `intent: DONE` + `task: design` extractable in <2 seconds. Structured format is instantly parseable. |
| A (Actionability) | 0.85 | Implicitly tells developers "start implementing" (their prompts say to check for design=done). Slightly indirect — doesn't explicitly say "dev-a, dev-b: begin." But the blackboard dependency chain makes this unambiguous. |
| **RS** | **0.905** | |

#### Message B2 (Reviewer → all)
**Content:** `{intent: 'STATUS', status: 'waiting'}`

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.85 | Clear that the reviewer is waiting. Minor deduction: doesn't say what they're waiting FOR (implementation completion implied by role). |
| S | 0.95 | Two fields, instantly extractable. |
| A | 0.50 | Low actionability — this is a status update, not a request. No one needs to do anything differently. Similar to Group A's acknowledgments, but at least structured. |
| **RS** | **0.81** | |

#### Message B3 (Dev A → all)
**Content:** `{intent: 'DONE', task: 'models+shortener'}`

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.90 | Clear which files are complete. Task ref maps directly to blackboard assignments. |
| S | 0.95 | `intent: DONE` + specific task extractable in <2 seconds. |
| A | 0.85 | Signals reviewer can begin reviewing these files. Triggers next step in dependency chain. |
| **RS** | **0.905** | |

#### Message B4 (Dev B → all)
**Content:** `{intent: 'DONE', task: 'storage+init'}`

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.90 | Same structure as B3. Clear which files are complete. |
| S | 0.95 | Identical format to B3 — consistent, instantly parseable. |
| A | 0.85 | Together with B3, signals all implementation is complete and review can proceed. |
| **RS** | **0.905** | |

#### Message B5 (QA → all)
**Content:** `{intent: 'VERDICT', task: 'tests', count: '18/18'}`

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.95 | Unambiguous: all 18 tests pass. The `VERDICT` intent and count are self-explanatory. |
| S | 0.95 | Key number (18/18) immediately visible. Structured format. |
| A | 0.90 | Signals project completion. If failures, would trigger fix cycle. 18/18 means "done." |
| **RS** | **0.94** | |

#### Blackboard Entries (scored as communication artifacts)

The blackboard IS the primary communication medium for Group B. Scoring the key entries:

**B-BB1: Interface Contract (on blackboard)**

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.95 | Typed Python interfaces with full signatures. Any developer can understand exactly what to implement. Self-documenting. |
| S | 0.95 | Organized by class, each method has explicit signature. Scannable by eye or grep. |
| A | 1.00 | The contract IS the action spec. Each developer's task is fully defined by the types. No interpretation needed. |
| **RS** | **0.96** | |

**B-BB2: Assignment Table (on blackboard)**

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.95 | Task ID, file ref, owner, status, notes — complete picture in tabular format. |
| S | 0.90 | Tabular format is instantly scannable. File ref codes (M:MOD, M:SHR) require legend lookup. |
| A | 0.90 | Status column tells each agent exactly where things stand. "blocked(tests)" is clear. |
| **RS** | **0.93** | |

**B-BB3: Findings (on blackboard)**

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.90 | Each finding clearly states file, issue, and severity assessment ("non-blocking"). |
| S | 0.85 | Bulleted list, scannable. File refs require lookup. |
| A | 0.80 | "non-blocking" and "acceptable for scope" make it clear no action is needed. |
| **RS** | **0.87** | |

### Group B Summary

| Artifact | RS | Type |
|----------|:--:|------|
| B1: Architect DONE message | 0.905 | Group message |
| B2: Reviewer STATUS message | 0.810 | Group message |
| B3: Dev A DONE message | 0.905 | Group message |
| B4: Dev B DONE message | 0.905 | Group message |
| B5: QA VERDICT message | 0.940 | Group message |
| B-BB1: Interface Contract | 0.960 | Blackboard entry |
| B-BB2: Assignment Table | 0.930 | Blackboard entry |
| B-BB3: Findings | 0.870 | Blackboard entry |
| **Group B Mean (messages only)** | **0.893** | 5 messages |
| **Group B Mean (all artifacts)** | **0.903** | 5 msgs + 3 BB entries |

**Note:** B2 (Reviewer STATUS=waiting) is the weakest Group B message at RS=0.81 — it's a status update, similar to Group A's acknowledgments but structured. It drags the mean slightly below 0.90. All other messages score ≥0.87. The interface contract (B-BB1) remains the highest-scoring artifact at RS=0.96.

---

## Group A: ab-english (English Control)

### Available Messages

**Data source:** Group A message count and classification verified by Group A Code Reviewer (be7cf32e). Full log at `.flightdeck/shared/ab-test/group-a-message-count.md`. **22 messages total**, classified as: design (1), implementation-announcement (2), status-update (6), social (2), review-feedback (3), fix-announcement (2), test-results (3), duplicate/redundant (3), question/clarification (0).

**CAVEAT: Scores below are still ESTIMATED per message type** — I have message counts and classifications but not exact message text. RS scores are based on typical English patterns for each message type. Frequency counts are now verified.

#### Message Types (verified counts, estimated RS per type)

**A1-est: Architect Design Post (Architect → all)**
Expected: English prose describing URLRecord fields, StorageBackend methods, URLShortener API, error types.

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.95 | English prose is maximally reconstructable. A new agent can follow the full narrative. |
| S | 0.50 | Design description in prose requires reading the full message to find specific details (e.g., "what are the StorageBackend methods?"). No structured index. |
| A | 0.75 | Implicitly says "implement this" but the boundary between what's dev-a's vs dev-b's responsibility requires reading carefully. |
| **RS** | **0.78** | |

**A2-est: Developer Acknowledgment (Dev A → all)**
Expected: "Got it, I'll start on models.py and shortener.py."

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.85 | Clear what the developer is doing. |
| S | 0.80 | Short message, key info (files, action) extractable quickly. |
| A | 0.30 | This message requires NO action from anyone. It's a status update that adds zero information (silence = working in any protocol). |
| **RS** | **0.67** | |

**A3-est: Developer Question (Dev → Architect)**
Expected: "Quick question — should StorageBackend.get_by_url return None if not found, or raise an exception?"

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.90 | Clear question about a specific design point. |
| S | 0.75 | Requires reading the sentence to extract the actual question. |
| A | 0.90 | Clear action needed: architect must decide and respond. |
| **RS** | **0.86** | |

**A4-est: Developer Completion (Dev → all)**
Expected: "I've finished models.py and shortener.py. Here's a summary of what I implemented: [2-3 paragraphs describing the implementation]."

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.90 | Full English description is understandable. |
| S | 0.45 | Multi-paragraph summary requires reading to find specific details. "Does shortener handle expiration?" requires scanning. |
| A | 0.70 | Implicitly tells reviewer to start, but doesn't explicitly trigger the next step. |
| **RS** | **0.73** | |

**A5-est: Review Feedback (Reviewer → Dev)**
Expected: "I reviewed storage.py. Overall looks good. A few issues: [list of 3-4 points in prose]. Please fix the thread safety issue in save() and the missing type hint on line 42."

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.90 | Clear what was reviewed and what issues were found. |
| S | 0.65 | Mix of praise + issues in prose. Have to read through to find actionable items. |
| A | 0.85 | Specific fixes requested, though mixed with non-actionable commentary. |
| **RS** | **0.82** | |

**A6-est: Test Results (Tester → all)**
Expected: "Ran all 18 tests. 16 passed, 2 failed. Failures: test_resolve_expired — the expiration check isn't working, looks like the datetime comparison is wrong in shortener.py line 48. test_stats_click_count — click_count isn't being incremented."

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.95 | Detailed, specific, includes file/line references. |
| S | 0.70 | Key numbers (16/18) at the start is good. But failure details require reading. |
| A | 0.90 | Clear what's broken and where. Developer knows exactly what to fix. |
| **RS** | **0.87** | |

**A7-est: Acknowledgment/Coordination (various)**
Expected: "Thanks!", "Sounds good", "I'll fix that now", "Ready for re-review"

| Dimension | Score | Rationale |
|-----------|:-----:|-----------|
| R | 0.70 | Understandable but trivial. |
| S | 0.90 | Short, instantly extractable. |
| A | 0.20 | Zero actionable content. Pure social protocol / noise. |
| **RS** | **0.66** | |

### Group A Summary (Verified Counts, Estimated RS)

| Message Type | RS | Actual Count | Category |
|-------------|:--:|:--:|-----------|
| A1: Design post | 0.78 | 1 | design |
| A2: Acknowledgments/status | 0.67 | 6 | status-update |
| A3: Clarification questions | 0.86 | 0 | question/clarification |
| A4: Completion/implementation | 0.73 | 2+2=4 | impl-announcement + fix-announcement |
| A5: Review feedback | 0.82 | 3 | review-feedback |
| A6: Test results | 0.87 | 3 | test-results |
| A7: Coordination noise | 0.66 | 2+3=5 | social + duplicate |
| **Total** | | **22** | |
| **Group A Weighted Mean RS** | **~0.73** | | |

**Note:** Weighted mean = (0.78×1 + 0.67×6 + 0.73×4 + 0.82×3 + 0.87×3 + 0.66×5) / 22 = 16.03 / 22 ≈ 0.73. The mean is dragged down by status updates (6 at RS=0.67) and social/duplicate noise (5 at RS=0.66), which together account for 50% of all messages. These message types add near-zero information value.

---

## Comparative Summary (Raw Data)

**⚠️ CORRECTED 2026-03-13: Group B = 5 messages (was incorrectly reported as 1 from self-reported blackboard data).**

| Metric | Group A (English) | Group B (AECP) |
|--------|:-:|:-:|
| Messages sent | 22 (verified) | 5 (verified by lead) |
| Mean RS (messages only) | ~0.73 (est. per type) | 0.893 |
| Mean RS (all artifacts) | ~0.73 (est. per type) | 0.903 |
| RS ≥ 0.75 threshold | Below | Well above |
| Lowest RS artifact | ~0.66 (social/duplicate) | 0.81 (reviewer STATUS) |
| Highest RS artifact | ~0.87 (test results) | 0.96 (interface contract) |
| **RS delta** | | **+0.173 (24% higher)** |
| **Message ratio** | | **22:5 (4.4:1)** |
| **Message reduction** | | **77.3%** |
| **CE (task_success / msgs)** | 0.82 | 3.6 |
| **CE ratio** | | **4.4×** |
| **CR (clarifications / tasks)** | 0.00 | 0.00 |

### Corrected vs Original Metrics

| Metric | Original (self-reported) | Corrected (lead-verified) |
|--------|:-:|:-:|
| Group B messages | 1 | **5** |
| Message ratio | 22:1 | **22:5 (4.4:1)** |
| Message reduction | 95.5% | **77.3%** |
| CE (Group B) | 18.0 | **3.6** |
| CE ratio | 22× | **4.4×** |
| Group B mean RS (msgs) | 0.905 | **0.893** |
| Group B mean RS (all) | 0.916 | **0.903** |

**Meta-finding: Self-reported blackboard metrics are unreliable.** The blackboard claimed 1 message when 5 were actually sent. Future experiments need system-level logging, not self-reporting.

---

## Scoring Notes & Caveats

1. **Group A message count is now VERIFIED (22 messages).** RS scores per message type are still estimated — I have classifications but not exact message text. Scores should be refined when actual transcripts become available.

2. **Group B blackboard entries are scored as communication artifacts.** In AECP, the blackboard IS the communication medium. Excluding them would be like scoring English communication but ignoring half the messages.

3. **Actionability (A) penalizes acknowledgments heavily.** Messages like "Got it" and "Thanks" score A=0.2-0.3 because they require zero action. This is by design — the RS rubric measures communication utility, not social niceness.

4. **The interface contract (B-BB1) scores highest of any artifact in either group (RS=0.96).** Typed Python signatures are the ultimate format-as-meaning: maximally reconstructable, instantly scannable, and perfectly actionable. This validates P8 as the strongest single design principle.

5. **Hard to score: Group B "silence."** Communication by exception means the ABSENCE of messages is meaningful (silence = working). RS can't score a non-message, but the information value is real. This is a methodological gap in the RS framework — noted for future refinement.
