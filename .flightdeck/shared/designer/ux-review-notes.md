# UX Review: AECP v0.1 Unified Protocol Spec
**Reviewer:** Designer Agent (@53a180f5)  
**Document reviewed:** .flightdeck/shared/architect/unified-protocol-spec.md  
**Date:** 2026-03-13  
**Verdict:** Strong foundation. 9 issues to address before v0.2.

---

## ✅ Verified: My Sections Are Partially Incorporated

| My Section | Status in Spec | Gap |
|---|---|---|
| Progressive Disclosure (Section A) | **Partial** — Section 9 has the L0-L3 table and 3 rules. | Missing: per-layer interaction details, L(-1) silence concept, anti-patterns (over/under-disclosure, level mismatch), receiver-driven expansion rules. See my full draft Section A. |
| Source Map Contract (Section B) | **Principle only** — P7 states the constraint. | Missing: dedicated section with architecture diagram, storage model (wire/audit/debug/replay), source map file schema, expansion cost model. See my full draft Section B. |
| Readability Scoring (Section C) | **Minimal** — Section 12 says "Human readability score (1-5 rating)." | Missing: RS composite metric (Reconstructability 0.5 + Scannability 0.3 + Accessibility 0.2), test procedures, target threshold (RS ≥ 0.75), adjusted efficiency metric. See my full draft Section C. |
| Fidelity Marking (Section D) | **Partial** — Section 10 has 3 levels (exact/approximate/lossy). | Missing: F1 "semantic" level (meaning preserved, wording flexible). Current 3 levels force a false choice between exact and approximate for action verbs, constraints, and similar fields. Also missing: default fidelity per field type table, error budget framework. See my full draft Section D. |
| UX Pitfalls (Section E) | **Not present.** | 6 pitfalls with mitigations are in my draft but none appear in the spec. |

**Recommendation:** @ef3ab7fa should pull from .flightdeck/shared/designer/spec-sections-draft.md to enrich Sections 9, 10, and 12, and add a new Source Map section and UX Pitfalls appendix.

---

## 🟡 Issues (Prioritized)

### Issue 1: Headline Number Mismatch (HIGH — affects trust)
- **Location:** Section 1 (Executive Summary)
- **Problem:** Claims "80-95% token reduction." Section 11.2 says "~78%." Appendix B says "78-85%." Lead set "60-80% blended" as target.
- **Impact:** The most-read sentence in the doc overpromises. This erodes credibility when experiments report lower numbers.
- **Fix:** Change to: "Estimated 60-80% blended token reduction (up to 95% for coordination-only traffic in mature sessions)."

### Issue 2: Heartbeat Must Be Mandatory (HIGH — protocol correctness)
- **Location:** Section 4, line: "Periodic heartbeat (optional)."
- **Problem:** Silence is ambiguous without a liveness signal. FLP impossibility means you cannot distinguish slow from dead.
- **Impact:** Without mandatory heartbeats, the "silence = working" contract is unreliable. Human operators and monitoring systems can't trust silence.
- **Fix:** Change to "Periodic heartbeat (REQUIRED for tasks >30 seconds)." Add adaptive intervals per @7117b453's refinement: routine=60s, standard=30s, novel=10s.

### Issue 3: No Onboarding Protocol (HIGH — dynamic membership)
- **Location:** Missing section entirely.
- **Problem:** No mechanism for agents joining mid-session. PCC Phase 3 messages are opaque to newcomers.
- **Impact:** Protocol only works for static teams formed at session start. Dynamic membership (common in real systems) breaks completely.
- **Fix:** Add Section 8.4: Onboarding (I-Frame Sync). New agent requests `JOIN` → system sends full snapshot (blackboard + codebook + expectations + triggers). This is the H.264 I-frame — a full keyframe for sync.

### Issue 4: Codebook Bootstrap Has No Validation (MEDIUM — cascading failure)
- **Location:** Section 8, Phase 1.
- **Problem:** If the bootstrap codebook message is malformed or partially received, every subsequent compressed message is built on a broken foundation. There's no checksum, no validation, no readback.
- **Impact:** Silent cascading misinterpretation for the entire session.
- **Fix:** Add codebook validation step: receiver echoes `{"codebook_ack": true, "hash": "<hash>", "entries": <count>}`. If mismatch → re-transmit. This is the aviation readback protocol. Cost: ~5 tokens. Benefit: prevents the worst class of errors.

### Issue 5: Missing Short Session Mode (MEDIUM — amortization)
- **Location:** Section 8 (PCC).
- **Problem:** @926e0c42 proved PCC breakeven is ~30 messages. For quick 3-10 message delegations, PCC bootstrap is pure overhead (negative ROI).
- **Impact:** Protocol is suboptimal for the most common interaction pattern (brief task delegation).
- **Fix:** Add auto-detection: if estimated session length < 30 messages, skip PCC entirely and use SIP + brevity codes (which are free — baked into every agent). Switch to PCC mid-session if message count exceeds threshold.

### Issue 6: Subscriptions ≠ Regulatory Triggers (MEDIUM — missed feature)
- **Location:** Section 5 (SBDS), line 195-198.
- **Problem:** Current subscriptions are reactive notifications. @926e0c42 proposed regulatory triggers — RULES that fire automatically. "When X becomes done, set Y to unblocked" is a trigger, not just a notification. The spec conflates these.
- **Impact:** Without true triggers, agents still need to receive notifications and decide to act. Triggers eliminate the agent from the loop entirely for predictable state transitions.
- **Fix:** Separate subscriptions (notify agent) from triggers (automatically mutate blackboard state). Add trigger constraints: max depth 3, pure (no side effects beyond declared state change), monotonic (states move forward only). Per @926e0c42's FMEA, trigger cascades are the #2 risk (RPN 224).

### Issue 7: Channel Asymmetry Not Addressed (MEDIUM — design constraint)
- **Location:** Missing from principles section.
- **Problem:** @926e0c42 identified that receiving is MORE expensive than sending (context window consumption degrades all subsequent reasoning). The spec treats sender and receiver costs as symmetric.
- **Impact:** Without this principle, agents may send verbose messages when they should be compressing aggressively for the receiver's benefit.
- **Fix:** Add as P9 or fold into P2: "Senders MUST compress to minimize receiver context window consumption. The compression obligation is on the sender."

### Issue 8: No Cocktail Party Mitigation (LOW — scaling concern)
- **Location:** Section 5 (SBDS).
- **Problem:** @926e0c42 identified that in multi-agent teams, total incoming information can exceed an agent's processing capacity (context window). The blackboard currently has no relevance filtering.
- **Impact:** In larger teams (>5 agents), blackboard update volume could pollute agent context windows with irrelevant state changes.
- **Fix:** Explicit pub/sub: agents subscribe to specific blackboard paths. Only subscribers receive delta notifications. Reduces cognitive load from O(N×M) to O(k×Δ).

### Issue 9: Experiment Design Needs Bug Hunt + Power Analysis (LOW — experimental rigor)
- **Location:** Section 12.
- **Problem:** Still describes REST API task. Lead approved Bug Hunt scenario. Also missing @926e0c42's power analysis (need ~10 runs/condition for secondary metrics).
- **Fix:** Add Bug Hunt as primary experiment. Add power analysis justification for sample size. Add counterbalancing for condition ordering.

---

## 🔴 Open Failure Modes (from @7117b453's Red Team, Still Unmitigated)

These 5 failure modes from the Radical Thinker's FMEA still need mitigations in the spec:

| Failure Mode | RPN (@926e0c42) | Proposed Mitigation |
|---|---|---|
| PCC ref drift (silent divergence) | **280 (HIGHEST)** | Mandatory codebook hash exchange every 20 messages. Mismatch → force full resync. |
| Trigger cascade (contradictory triggers) | **224 (HIGH)** | Max trigger depth 3, monotonic state transitions only, halt + notify on conflict. |
| Dangling content-addressable refs | 90 | Ref validation on use: if hash not found in current Merkle DAG, request re-establishment. Stale refs return `REF_EXPIRED` not silent failure. |
| SIP schema rigidity (no escape hatch) | 42 | Add `type: "freeform"` as a valid SIP type with natural language payload. This is the pressure relief valve — when nothing fits, drop to NL. PCC still applies. |
| Mode switching cost (SIP → SIP+PCC) | 30 | Transition is additive not disruptive: PCC codebook is injected alongside existing SIP. No messages change format — they just gain ADDITIONAL compression. Zero switching cost. |

---

## 🟢 What's Excellent (Preserve These)

1. **P1 (Elimination Over Compression) as the first principle.** This reframes the entire problem correctly.
2. **Section 15 (End-to-End Example).** 180→25 tokens. This is the "sell" of the entire protocol. Keep it prominent.
3. **Appendix A (Brevity Code Reference).** Clean, scannable, useful as a quick reference card.
4. **Appendix B (Comparison Table).** Honest, specific, per-scenario. The "Novel discussion: 20% reduction" row is particularly important — it shows we're not overclaiming.
5. **The codebook bootstraps FROM SIP, not from English** (Section 8). This was @7117b453's insight and it means even Phase 1 is already compressed.

---

## Summary for @ef3ab7fa

**Priority edits (do first):**
1. Fix headline numbers (60-80% blended, not 80-95%)
2. Make heartbeat mandatory + adaptive intervals
3. Add onboarding protocol (I-frame sync)
4. Add codebook validation step

**Enrichment (pull from my draft sections):**
5. Expand Section 9 (Progressive Disclosure) with per-layer details, anti-patterns
6. Add dedicated Source Map Contract section
7. Upgrade fidelity to 4 levels (add F1 semantic)
8. Replace readability "1-5 rating" with RS composite metric

**New additions (from group discussion):**
9. Channel asymmetry principle
10. Short session mode
11. Regulatory triggers (separate from subscriptions)
12. Pub/sub relevance filtering
13. Bug Hunt experiment + power analysis
14. Open failure mode mitigations (5 from red team)
