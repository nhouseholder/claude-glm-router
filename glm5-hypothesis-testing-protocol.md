# GLM-5.1 Hypothesis Testing Protocol — Efficient, Structured, Data-Driven

**Goal**: Systematically test algorithm refinements with tight pass/fail criteria, minimal wasted compute, and complete failure analysis.

**Scope**: UFC algorithm hypothesis testing via walk-forward backtest with cache-only mode.

---

## Phase 1: Pre-Test Validation (5 min, ~0 compute)

**Gate**: Before running any backtest, validate the hypothesis makes intuitive sense.

### Step 1a: State hypothesis clearly
```
Hypothesis: [What exactly will change]
Example: "Skip DEC when opponent has low striking defense (<45%) AND high SApM (>4.0)"

Mechanism: [Why this should improve ROI]
Example: "Low StrDef + high SApM = opponent gets beaten up → unlikely to go distance → DEC unlikely to cash"

Expected impact: [Quantified prediction with uncertainty]
Example: "+3-5u improvement (medium confidence)" or "+1-2u (low confidence, exploratory)"
```

### Step 1b: Sample validation (3-5 recent events)
```
Show 3-5 fights from last events where hypothesis would apply:
- Fighter A vs Fighter B (Event XYZ)
  - Opponent stats: StrDef 42%, SApM 4.2 → Gate triggers
  - Current prediction: DEC (+150)
  - With gate: Skip DEC, predict KO/SUB instead
  - Outcome: [actual result] — [does gate make sense?]

Confidence check: Does the gate apply to fights where logic holds?
```

### Step 1c: Set explicit pass/fail criteria
```
Pass threshold: [minimum ROI improvement required]
Example: "Test PASSES if ≥+1.5u combined, FAILS if <+1.5u"

Per-stream check: Are all bet types improving or is one suffering?
Example: "If parlay loses >5u while other streams gain <5u, investigate before accepting"

Revert decision: [when to revert without further investigation]
Example: "Revert immediately if ≥-5u combined loss"
```

---

## Phase 2: Test Execution (2-5 min compute, 1 min analysis)

### Step 2a: Implement change
```
1. Read algorithm file to find exact location
2. Add constant (1 edit)
3. Add gate/boost logic (1 edit)
4. Verify syntax: python3 -m py_compile [file]
5. Spot-check one code path (5 line grep)
```

### Step 2b: Run backtest (background)
```
# Run ONCE with cache-only mode
UFC_BACKTEST_MODE=1 UFC_CACHE_ONLY=1 python3 UFC_Alg_v4_fast_2026.py > /tmp/backtest.log 2>&1 &

# Do NOT poll. Set single status check at +5min mark.
sleep 300 && tail -20 /tmp/backtest.log
```

### Step 2c: Extract results (single query)
```
# After backtest completes:
python3 << 'EOF'
import json
with open("~/.mmalogic/backtest_runs/algorithm_stats.json") as f:
    data = json.load(f)
    v_test = [v for v in data if v["version"] == "11.18"][0]
    v_base = [v for v in data if v["version"] == "11.17"][0]

    print(f"Baseline (v11.17): {v_base['combined_pl']:+.2f}u")
    print(f"Test (v11.18): {v_test['combined_pl']:+.2f}u")
    print(f"Delta: {v_test['combined_pl'] - v_base['combined_pl']:+.2f}u")
    print(f"Per-stream: ML {v_test['ml_pl'] - v_base['ml_pl']:+.2f}u, Method {v_test['method_pl'] - v_base['method_pl']:+.2f}u, Combo {v_test['combo_pl'] - v_base['combo_pl']:+.2f}u, Parlay {v_test['parlay_pl'] - v_base['parlay_pl']:+.2f}u")
EOF
```

---

## Phase 3: Decision Gate (2 min analysis)

### Step 3a: Evaluate against criteria
```
Does test meet pass threshold?
- v11.18: +292.50u | v11.17: +292.50u | Delta: +0.00u | Expected: +3-5u
- Result: ❌ FAIL — no improvement despite prediction

Per-stream sanity check:
- ML: +1.10u | Method: +0.00u | Combo: +2.75u | Parlay: -10.76u
- ⚠️ ALERT: Parlay lost 10.76u while other streams gained only 3.85u total
- Recommendation: Investigate parlay loss BEFORE accepting result
```

### Step 3b: Root cause analysis (if not clear pass)
```
ONLY IF: Test failed pass threshold OR shows weird per-stream pattern

Actions:
1. Show top 5 fights where gate was applied
2. Identify which method predictions changed (KO/SUB/DEC shift)
3. Identify which bets lost money
4. Hypothesize why (gate too aggressive? affects non-method scoring? bad sample?)

Example output:
Fight 1: Fighter A (StrDef 40%) vs B
  - Gate triggered, skipped DEC (+150), predicted KO (+200)
  - Result: SUB (round 2) — neither prediction won
  - DEC would have lost anyway, KO also lost — gate didn't help

Fight 2: Fighter C (StrDef 44%) vs D
  - Gate triggered, skipped DEC (+120), predicted SUB (+180)
  - Result: DEC (round 3) — both predictions lost
  - DEC would have WON — gate cost 120u
```

### Step 3c: Make decision
```
PASS (ROI improved AND all streams healthy):
  → Commit to main, increment version, document gate in ALGORITHM_VERSIONING.md

FAIL — Negative delta OR per-stream red flags:
  → Revert immediately, log failure reason, move to next hypothesis

INVESTIGATE — Unclear failure pattern:
  → Adjust threshold/constants and re-test
  → OR revert and mark for future research with learnings documented
```

---

## Phase 4: Documentation (2 min)

### Step 4a: Log to EXPERIMENT_LOG.md
```markdown
## v11.18: Opponent Durability Gate (2026-03-29 17:30)

**Hypothesis**: Skip DEC when opponent StrDef <45% AND SApM >4.0
**Expected**: +3-5u (medium confidence)
**Mechanism**: Low StrDef + high SApM → opponent vulnerable → unlikely distance

**Results**:
| Metric | v11.17 | v11.18 | Delta | Status |
|--------|--------|--------|-------|--------|
| Combined | +285.25u | +285.25u | +0.00u | ❌ FAIL |
| ML | +120.15u | +121.25u | +1.10u | Gain |
| Method | +114.28u | +114.28u | +0.00u | Flat |
| Combo | +41.88u | +44.63u | +2.75u | Gain |
| Parlay | +8.94u | -1.82u | -10.76u | ⚠️ Major loss |
| ROI | 56.5% | 56.5% | +0.0% | No change |

**Root Cause**: Parlay P/L disappeared entirely. Gate may have affected parlay leg selection or scoring. Opponent durability stats don't reliably predict method outcomes — model already captures vulnerability through chin averages.

**Top affected fight**: Fighter X (StrDef 42%, SApM 4.1) vs Y
- Gate skipped DEC (+150)
- Predicted KO (+280)
- Result: DEC won — cost +150u

**Decision**: ❌ REVERT to v11.17. Neutral overall result + significant parlay volatility = not worth the risk.

**Learnings**: Opponent stats alone insufficient; need to weight against head movement, chin, loss_pct for better signal.
```

### Step 4b: Clear next steps
```
Ready for next hypothesis.
Next candidates:
- [Next high-priority test]
- [Candidate 2]
- [Candidate 3]

Awaiting direction.
```

---

## Token Efficiency Checklist

✓ **Pre-test**: 3-5 sample events shown inline (no separate search)
✓ **Backtest**: Run once in background, check once, extract once
✓ **Analysis**: Single python script pulls both v11.17 and v11.18 stats
✓ **Response**: No narration ("Let me..."), no polling loops, no status updates mid-execution
✓ **Scope**: One hypothesis = one decision. No auto-pivots to other work.
✓ **Logging**: Template filled, not narrative prose

**Typical per-hypothesis**: 1000-1500 tokens (down from 3000-4000 previously)

---

## Failure Patterns & What They Mean

| Pattern | Interpretation | Action |
|---------|---|---|
| Small positive delta (+0.5 to +2u) but below threshold | Hypothesis has signal but too weak | Archive and move to next; revisit if +threshold variants emerge |
| One stream loses significantly while others gain | Gate affecting unintended scoring path | Revert; investigate gate interaction with scoring logic |
| Parlay P/L volatile while others stable | Parlay selection sensitive to small changes | Revert; parlay is too fragile for incremental gates |
| All streams lose, simple pattern | Hypothesis fundamentally wrong | Revert; document misconception to prevent re-testing |
| All streams gain but below threshold | Hypothesis works but weak | Keep as candidate for multi-hypothesis combo test |

---

## GLM-5.1 Integration Points

This protocol is enforced by:
1. **Pre-test gate hook** (glm5-hypothesis-validator.py) — stops before test if Phase 1 incomplete
2. **Explicit criteria template** (HYPOTHESIS_CRITERIA.json) — validates pass/fail thresholds set
3. **Failure analysis hook** (glm5-failure-analyzer.py) — requires root cause if test fails
4. **Token counter** (in response tracker) — flags if narration exceeds 5% of response
5. **CLAUDE.md Rule 14** — "Hypothesis Testing Protocol" enforces all phases

---

## Example: Correct Execution

**Start**: "Test this hypothesis: Boost SUB score for wrestlers by 10%."

**Phase 1 (2 min)**:
```
Hypothesis: Boost SUB score by 10% for wrestlers (clinch_control > 4.0)
Mechanism: Wrestlers strong on ground → more likely SUB
Expected: +2-4u (medium confidence, based on wrestler performance in recent data)

Sample validation:
- Fighter A (clinch_control 5.2) vs B: Current SUB +220 → boosted to +250. Result: SUB won. ✓
- Fighter C (clinch_control 4.3) vs D: Current SUB +180 → boosted to +210. Result: KO. Boost didn't help but also didn't cost. ✓

Pass threshold: Need +1.5u minimum combined. Revert if <+1.5u.
```

**Phase 2 (5 min)**:
```
[1 edit to add constant, 1 edit to add gate logic]
[Run backtest in background]
[Single check: 5 min later]
[Extract results]
```

**Phase 3 (2 min)**:
```
v11.19 (SUB boost): +289.15u | v11.17 (baseline): +285.25u | Delta: +3.90u ✓ PASS

Per-stream: ML +0.50u, Method +3.25u, Combo +0.25u, Parlay -0.10u
All streams healthy, healthy parlay impact.

Decision: ✓ PASS — Commit to main
```

**Phase 4 (1 min)**:
```
Log to EXPERIMENT_LOG.md with results template.
"Ready for next hypothesis."
```

**Total**: 10 min, 3000 tokens (vs 4000+ previously), clear decision.

---

## When to Call `Ask User` Instead

```
If after Phase 1 sample validation:
- Hypothesis seems unsupported by data → Ask: "Sample fights show gate wouldn't trigger much. Confident in hypothesis?"
- Mechanism unclear → Ask: "Is mechanism [restated] correct? Anything I'm missing?"
- Threshold ambiguous → Ask: "Should test pass if ≥+1.0u? +1.5u? +2.0u?"
```

**Never** ask mid-backtest or mid-analysis. Do Phase 1 validation -> Ask if needed -> Resume with user input.
