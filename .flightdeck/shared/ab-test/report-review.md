# Critical Review: Final Experiment Report

**Reviewer:** Architect Agent (ef3ab7fa)  
**Report reviewed:** `.flightdeck/shared/ab-test/final-experiment-report.md`  
**Date:** 2026-03-13

---

## CRITICAL FINDING: Group B Message Count Is Wrong

**The report claims Group B sent 1 message. The lead observed 5 messages in the ab-aecp group.**

Lead's observed messages:
1. Architect: `{intent: 'DONE', task: 'design'}`
2. Reviewer: `{intent: 'STATUS', status: 'waiting'}`
3. Dev A: `{intent: 'DONE', task: 'models+shortener'}`
4. Dev B: `{intent: 'DONE', task: 'storage+init'}`
5. QA: `{intent: 'VERDICT', task: 'tests', count: '18/18'}`

**Source of error:** The blackboard's self-reported metric (`messages_sent: 1`) is wrong. Either only the architect updated the counter, or agents didn't count their own messages. The observer report (§9, §10) correctly flagged self-reporting as a limitation but the final report used the self-reported number as the primary metric without independent verification.

**This invalidates the headline numbers in the report.**

---

## Corrected Metrics

| Metric | Report Claims | Corrected | Impact |
|--------|:---:|:---:|---------|
| Group B messages | 1 | **5** | Primary metric is wrong |
| Message ratio | 22:1 | **22:5 (4.4:1)** | 5× less dramatic |
| Message reduction | 95.5% | **77.3%** | Still strong but fundamentally different |
| CE (Group B) | 18.0 | **3.6** | 5× lower |
| CE ratio (B/A) | 22× | **4.4×** | 5× less dramatic |

### What changes:

- **H2** is still CONFIRMED: B < 0.5×A → 5 < 11 → yes. But the margin is 77%, not 95%.
- **H1** is still likely supported: 5 short structured messages (~100 tokens total) vs 22 English messages (~2000+ tokens). Token ratio likely still >60% reduction.
- **H5** needs update: 4 additional Group B messages need RS scoring. The 4 new messages are all structured SIP-format, so RS is likely ≥0.85 each. Mean RS will change slightly.
- **All other hypotheses** (H3, H4, H6, H7) are unaffected.

### What does NOT change:

- Task quality: 18/18 both groups — unchanged
- Group A data: 22 messages, all classifications — unchanged
- Code comparison: all factual — unchanged
- Qualitative findings: elimination > compression, typed contracts as spec — unchanged
- "Layers as fallbacks" insight — unchanged (Layer 0 still did most work)

---

## Accuracy Audit

### Numbers That Are Correct
- ✅ Group A message count: 22 (verified by Group A Code Reviewer)
- ✅ Group A message classification breakdown (design, status, social, etc.)
- ✅ Both groups: 18/18 tests passing
- ✅ Code line counts: A=579, B=586
- ✅ Code quality comparison (deepcopy vs refs, max-attempts vs infinite, etc.)
- ✅ Group A rework cycles: 1
- ✅ Both groups: 0 clarifications
- ✅ Group A RS estimates: ~0.74 weighted mean (methodology is sound even if estimates)
- ✅ Experiment 1 (Bug Hunt): 3 AECP messages vs 19 simulated — correctly labeled as not apples-to-apples
- ✅ Experiment 2 (30-agent): ~50 messages, 96/96 tests, no baseline — correctly noted

### Numbers That Are WRONG (must correct)
- ❌ **Group B messages: "1"** → should be **5**
- ❌ **Message ratio: "22:1"** → should be **22:5 (4.4:1)**
- ❌ **Message reduction: "95.5%"** → should be **77.3%**
- ❌ **CE Group B: "18.0"** → should be **3.6**
- ❌ **CE ratio: "22×"** → should be **4.4×**
- ❌ **"21 eliminated messages"** → should be **"17 eliminated messages"**
- ❌ **Substantive message reduction: "94.7%"** → recalculate with corrected B count

### Places in the Report Where "1 message" Appears (all need correction)

1. **Executive summary table** (line 19): "1" under AECP Messages for Exp 3
2. **§3 Experiment 3 raw results table** (line 128): "1" for Messages sent
3. **§3 Group B Communication** (line 161): "1 group message"
4. **§3 What This Shows** (line 195): "22:1 message ratio"
5. **Combined Analysis hypothesis table** (line 228): "B=1, A=22"
6. **Where the 21 Eliminated Messages Went** (line 248-260): entire section assumes 21 eliminated
7. **Conclusions #1** (line 385): "1 vs 22 (A/B test)"
8. **Closing paragraph** (line 429): implicit in "dramatically reduces"
9. **Observations report §2 table** (observations.md line 23): "1 (self-reported)"
10. **Observations report §6** (observations.md lines 40-44): CE=18.0, 95.5%
11. **RS scores doc** (rs-scores.md): only 1 Group B message scored

---

## Overclaiming Assessment

### Claims That Are Overclaimed (with corrections)

1. **"95.5% message reduction"** → Correct to **77.3%**. Still a strong result. 77% reduction with equal output quality is publishable and impressive. No need to inflate.

2. **"22× more communication-efficient"** → Correct to **4.4×**. Still a large effect size.

3. **"21 out of 22 messages were unnecessary"** → Correct to **17 out of 22**. The 5 surviving messages break down as: 1 design-done signal, 1 reviewer status, 2 developer completions, 1 test verdict. These are the AECP-protocol-minimum messages (completion signals + verdict).

4. **"Near-total message elimination"** → Correct to **significant message reduction**. 77% is significant but not "near-total."

### Claims That Are NOT Overclaimed

- "Structure beats English for readability" — supported by RS data (even with 5 messages, all structured, RS will remain high)
- "Task quality preserved" — 18/18 both, code comparison is factual
- "Blackboard + typed contracts do most of the work" — still true with 5 messages; those 5 messages are minimal completion signals, not coordination
- "PCC was never needed" — still true
- "Layers are fallbacks" — still true
- "Format-as-meaning is the standout principle" — still true

---

## Honesty Assessment

### What the Report Does Well
- ✅ Limitations section is comprehensive (8 items)
- ✅ Explicitly flags n=1, self-reported data, estimated RS, task specification bias
- ✅ Observer report correctly notes "self-reported via blackboard" throughout
- ✅ H3 floor effect honestly discussed
- ✅ Reviewer anomaly documented (§5 of observations)
- ✅ "Directional findings, not production-validated results" — good framing

### Where Honesty Falls Short
- ❌ **Used self-reported number as primary metric despite flagging it as unreliable.** The report says "self-reported" in caveats but then uses "1 message" as the headline number everywhere. The correct approach: flag the number as unverified and note that independent verification is needed BEFORE computing derived metrics.
- ❌ **Observer report §9 says "None observed" for protocol violations but couldn't access the group.** Should say "Unable to assess — no group access."
- ❌ **RS scores doc only scored 1 Group B message.** With 5 actual messages, 4 are unscored. The mean RS may change.

---

## Missing Caveats

1. **The 5 Group B messages reveal a different story than "1 message."** With 5 messages, Group B used one message per role — exactly the minimum for a 5-agent team where each agent signals completion. This is still impressive (minimum viable communication) but it's a different narrative than "near-total elimination." The story becomes: **AECP reduces communication to the minimum viable set — one completion signal per agent.**

2. **Group B's reviewer sent a STATUS message.** `{intent: 'STATUS', status: 'waiting'}` is arguably a protocol violation — AECP Rule 1 says "silence = working" and the rules prohibit progress updates. The reviewer messaging "I'm waiting" is a status update. This resolves the §5 anomaly (the reviewer WAS active) but also shows the protocol wasn't perfectly followed.

3. **The "waste taxonomy" (21 eliminated messages) needs recalculation.** With 5 Group B messages, only 17 were eliminated. The breakdown of WHICH 17 changes slightly — the 5 surviving messages (completion signals) map to some of Group A's "implementation announcement" and "test results" categories, meaning those categories were NOT fully eliminated, just compressed from prose to structured format.

4. **Group B's 5 messages are ALL completion/status signals.** Zero of them contain novel information exchange (questions, design decisions, clarifications). This supports the "communication by exception" narrative — agents only messaged when they had a state transition to announce. But it also means the blackboard was sufficient for ALL information exchange, with messages serving only as notification triggers.

---

## Recommended Corrections (Priority Order)

### P0 — Must Fix Before Publication

1. **Replace "1 message" with "5 messages" everywhere** (10+ locations listed above)
2. **Recalculate all derived metrics** (CE, reduction %, ratio, eliminated count)
3. **Update executive summary table** with corrected numbers
4. **Score the 4 additional Group B messages** for RS
5. **Revise "Where the 21 Eliminated Messages Went"** → "Where the 17 Eliminated Messages Went"

### P1 — Should Fix

6. **Reframe the narrative** from "near-total elimination" to "reduction to minimum viable communication (1 signal per agent)"
7. **Note the reviewer STATUS message** as a minor protocol deviation
8. **Update observations.md and rs-scores.md** with corrected numbers
9. **Add caveat**: self-reported blackboard metrics were inaccurate (messages_sent: 1 vs actual: 5) — this itself is a finding about self-reporting reliability

### P2 — Nice to Have

10. **Discuss why self-reporting failed** — agents updating a shared counter is unreliable; system-level logging is needed for accurate measurement
11. **Note that 5 messages for 5 agents = 1 message per agent** — this is actually a cleaner metric than "1 total message"

---

## Summary Verdict

**The report is well-structured, honestly caveated, and mostly accurate — but the headline number is wrong.** The correction from 22:1 to 22:5 changes the magnitude of the finding but not the direction. 77% message reduction with equal quality and higher readability is still a strong, publishable result. The report should be corrected and the corrected numbers are still impressive enough to stand on their own. There is no need to rely on the inflated "1 message" claim.

**Corrected headline:** *AECP achieves 77% message reduction (22 → 5 messages) with equal task quality (18/18 tests) and 25% higher readability (RS 0.916 vs 0.74). Communication reduces to the minimum viable set: one structured completion signal per agent.*

That's honest, accurate, and still compelling.
