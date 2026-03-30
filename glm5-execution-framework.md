# GLM-5.1 Execution Framework — Deep Investigation, Clear Criteria, Learning Capture

**Scope**: All complex tasks (5+ min, multi-file, experimental, or high-stakes)
**Goal**: Prevent execution inefficiencies and errors by addressing 4 root problems

---

## The 4 Root Problems

| Problem | Manifestation | Root Cause | Fix |
|---------|---|---|---|
| **Success criteria ambiguity** | "Neutral" results accepted; unclear when task is done | No explicit pass/fail thresholds set upfront | Pre-execution gate defining DONE state |
| **Investigation depth** | Failed experiments reverted without root cause analysis | Stopping at symptoms ("didn't improve ROI") instead of understanding why | Mandatory failure analysis protocol |
| **Learning capture** | Same hypotheses re-tested; findings not documented | Incomplete logging prevents learning retention | Template-enforced documentation |
| **Scope creep** | After task fails, auto-pivot to related work instead of stopping | No decision boundary enforcement | Single-task response rule + explicit stop condition |

---

## Framework: 5 Execution Phases

### Phase 1: Success Criteria Definition (2 min)

**Before starting execution, define what "done" explicitly looks like.**

```
TASK: Test algorithm hypothesis

SUCCESS CRITERIA:
- Primary: Combined ROI improves by ≥+1.5u compared to baseline
- Secondary checks:
  - No single bet type loses >5u (stability check)
  - Parlay P/L stays positive (fragility check)
  - ML, Method, Combo all improve (consistency check)

FAILURE CRITERIA:
- Auto-revert if: ≥-5u combined loss (threshold for cost > benefit)
- Investigate if: Neutral result OR mixed per-stream (some gain, some loss)
- Deep-dive if: Parlay behavior changes unexpectedly

DECISION GATE:
- PASS: Meets primary ✓ + secondary checks ✓
- FAIL: Misses primary OR secondary red flag
- INVESTIGATE: Unclear pattern requiring root cause analysis
```

**Why this matters**: Without explicit thresholds, "neutral" feels like a valid result. With criteria, you know immediately whether to proceed, investigate, or revert.

---

### Phase 2: Execution with Checkpoints (variable)

**Execute the task with explicit decision points.**

- **Checkpoint 1**: After setup → Does environment match assumptions?
- **Checkpoint 2**: After initial test → Do results suggest promise or failure?
- **Checkpoint 3**: Before finalizing → Do secondary checks pass?

Each checkpoint outputs: ✓ PASS → proceed | ❌ FAIL → branch to investigation | ❓ UNCLEAR → root cause analysis

---

### Phase 3: Failure Investigation Protocol (2-5 min)

**When a task FAILS or returns UNCLEAR results, investigate deeply.**

#### If FAIL (explicit failure):
```
SYMPTOM: Hypothesis resulted in +0.00u (no improvement)

ROOT CAUSE ANALYSIS:
1. Mechanism check: Did the gate fire as expected?
   - Sample 3-5 fights where gate should apply
   - Show which method predictions changed
   - Show what the actual outcomes were
   - Analyze: Does gate make intuitive sense for these fights?

2. Impact analysis: Where did value get lost/gained?
   - Baseline: ML +120u, Method +115u, Combo +40u, Parlay +11u = +286u
   - Test: ML +121u, Method +115u, Combo +43u, Parlay -11u = +268u
   - Delta: ML +1u, Method 0u, Combo +3u, Parlay -22u
   - Finding: Parlay lost more than other streams gained

3. Hypothesis challenge: Why didn't the mechanism work?
   - Expected: Low StrDef + high SApM → unlikely distance → DEC unlikely
   - Observed: Parlay completely collapsed, suggesting gate affected non-Method scoring
   - Possibility 1: Gate logic leaked into parlay selection
   - Possibility 2: Opponent stats don't reliably predict outcomes
   - Possibility 3: Model already captures this signal via chin/loss_pct

4. Learning capture: What prevents re-testing this?
   - "Opponent durability stats alone insufficient; need weighted factors"
   - "Don't gate Method predictions in ways that affect parlay scoring"
   - "Parlay is fragile; small changes in prediction scoring cause large P/L swings"
```

#### If UNCLEAR (mixed results):
```
SYMPTOM: Some metrics improve, others decline; unclear if net positive

ANALYSIS:
1. Per-stream breakdown: Which streams gained, which lost?
2. Magnitude check: Do gains outweigh losses? (by how much?)
3. Pattern analysis: Is the mixed result expected or surprising?
4. Decision: Should we adjust the hypothesis or abandon it?
```

---

### Phase 4: Learning Capture (2 min)

**Document findings so future tasks learn from this work.**

#### Structured Log Entry
```markdown
## [Task Name] — [Date]

**Objective**: [What were you trying to achieve?]

**Approach**: [What did you do?]

**Success Criteria**:
- Primary: [threshold]
- Secondary: [checks]

**Results**:
| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| [KPI 1] | [X] | [Y] | ✓/❌ |
| [KPI 2] | [X] | [Y] | ✓/❌ |

**Root Cause Analysis** (if FAIL/UNCLEAR):
1. Symptom: [What went wrong?]
2. Mechanism check: [Did gate/change fire as intended?]
3. Impact analysis: [Where was value lost?]
4. Hypothesis challenge: [Why didn't it work?]
5. Learning: [What prevents re-testing?]

**Example Impact**:
- Fight A: [description of what happened with amounts]
- Fight B: [description of what happened with amounts]
- Fight C: [description of what happened with amounts]

**Decision**: ✓ PASS (commit) | ❌ FAIL (revert) | ❓ INVESTIGATE (adjust & retry)

**Learnings for Next Task**:
- [Insight 1] — prevents future mistake
- [Insight 2] — suggests new approach
- [Insight 3] — highlights model limitation
```

---

### Phase 5: Scope Boundary & Stop (1 min)

**Execute ONE task, make ONE decision, stop.**

```
RULE: A single execution cycle ends with a decision, NOT with pivot to related work.

✓ VALID: "Hypothesis FAILED (parlay loss). Reverting to v11.17. Ready for next hypothesis."

❌ INVALID: "Hypothesis FAILED. Let me run a full backtest of v11.17 to see if there's an issue there. Also, let me test 3 more hypotheses while I'm at it."

DECISION BOUNDARY:
- After Phase 3 investigation completes, make a PASS/FAIL/INVESTIGATE decision
- Output decision clearly with reasoning
- Stop at that boundary
- "Ready for next task" = phase cycle complete
```

---

## Integration: How This Applies to Different Task Types

### Hypothesis Testing
```
Phases 1-5 as described above.
Pre-execution: Define pass/fail thresholds explicitly
Investigation: Required if FAIL or mixed results
Learning: Template capture with root cause
```

### Refactoring / Code Changes
```
Phase 1: Success = tests pass, performance improves, no regressions
Phase 2: Execute refactor with test checkpoints
Phase 3: If tests fail, deep investigation (not just "run tests again")
Phase 4: Log: What changed, why, what could break, how tested
Phase 5: Stop at "refactor complete" — don't auto-pivot to optimization
```

### Bug Fixes
```
Phase 1: Success = bug reproduces, fix verified, no side effects
Phase 2: Reproduce bug (checkpoint), apply fix (checkpoint), verify (checkpoint)
Phase 3: If still broken, deep investigation (not just "try again")
Phase 4: Log: Bug, root cause, fix, how to prevent, test case
Phase 5: Stop at "bug verified fixed" — don't refactor surrounding code
```

### Exploration / Research
```
Phase 1: Success = research question answered with confidence level
Phase 2: Research with interim findings (checkpoint after each major finding)
Phase 3: If findings contradict, investigate (not just pick the latest)
Phase 4: Log: Question, findings, confidence, contradictions, sources
Phase 5: Stop at "question answered" — don't pivot to followup questions
```

---

## The 4 Fixes in Action

### Fix 1: Success Criteria Ambiguity → Pre-Execution Gate

**BEFORE**: "Test hypothesis, see if it improves ROI"
- Result: +0.00u (neutral)
- Decision: "Doesn't help, revert"
- Problem: No clear YES/NO threshold

**AFTER**: "Test hypothesis. PASS if ≥+1.5u combined AND parlay P/L stays positive"
- Result: +0.00u combined, parlay -10.76u
- Decision: ❌ FAIL (misses both criteria)
- Confidence: Clear decision with reasoning

---

### Fix 2: Investigation Depth → Mandatory Failure Analysis

**BEFORE**: Parlay lost -10.76u but didn't investigate
- Just reverted without understanding why
- Can't prevent similar issue next time

**AFTER**: Investigate when parlay loss exceeds expectations
1. Did gate fire as expected? (Yes, on 42 events)
2. Where did value get lost? (Parlay only, other streams gained)
3. Why? (Gate may affect non-Method scoring paths)
4. What prevents re-testing? ("Don't gate Method in ways affecting parlay")

---

### Fix 3: Learning Capture → Template Documentation

**BEFORE**: Logged "+0.00u, not effective, reverted"
- No context for future reference
- Next person tests same hypothesis again

**AFTER**: Full entry with:
- Hypothesis + mechanism
- Expected vs actual results
- Root cause analysis with example fights
- Learnings preventing re-testing

---

### Fix 4: Scope Creep → Single-Task Response Boundary

**BEFORE**: After hypothesis failed, pivoted to:
- Repo syncing
- Full v11.17 backtest
- Planning future tests

**AFTER**: Decision at task boundary
- ❌ FAIL: parlay loss, stop
- Decision documented
- "Ready for next hypothesis"
- No auto-pivot to other work

---

## How This Prevents Future Errors

### Error: "I don't know when to stop investigating"
**Fix**: Phase 3 investigation has explicit checkpoints. When all 4 items (mechanism check, impact analysis, hypothesis challenge, learning capture) are complete, you STOP and make a decision.

### Error: "I accepted unclear results and wasted compute"
**Fix**: Phase 1 defines explicit PASS/FAIL/INVESTIGATE criteria. No ambiguity about whether ±0.00u is acceptable.

### Error: "I made the same mistake again in a different project"
**Fix**: Phase 4 learning capture with template forces documentation of root cause and "what prevents re-testing."

### Error: "I pivoted away from the task and never finished the original work"
**Fix**: Phase 5 scope boundary rule: one task = one decision = one stop point.

### Error: "Failure analysis was shallow and missed root cause"
**Fix**: Phase 3 mandatory protocol with 4 required steps (mechanism, impact, hypothesis challenge, learning).

---

## Implementation: Hooks + Rules

### CLAUDE.md Enhancement
Add to Rules section:
```markdown
15. **Execution Framework** (GLM-5.1 deep investigation protocol):
    - **Phase 1**: Before starting complex task, define success criteria explicitly (PASS/FAIL/INVESTIGATE)
    - **Phase 2**: Execute with checkpoints (not just "run and see")
    - **Phase 3**: If FAIL/UNCLEAR, mandatory investigation: mechanism check → impact analysis → hypothesis challenge → learning capture
    - **Phase 4**: Template-enforced logging with root cause + examples
    - **Phase 5**: Single-task scope boundary — one task = one decision, then STOP
```

### Execution Validator Hook
```python
Runs on UserPromptSubmit for complex tasks:
- Detects: "test hypothesis", "refactor", "fix bug", "research"
- Checks: Has user defined success criteria? (Phase 1)
- If NO: Outputs Phase 1 template before proceeding
```

### Failure Investigation Hook
```python
Runs when task result is FAIL or UNCLEAR:
- Checks: Has Phase 3 investigation been completed?
- Required: Mechanism check, impact analysis, hypothesis challenge, learning capture
- If incomplete: Outputs Phase 3 protocol
```

---

## Example: Correct Execution

**Task**: Test algorithm hypothesis

**Phase 1**: ✓ Success criteria defined
```
PASS if: ≥+1.5u combined AND parlay P/L positive AND all streams healthy
FAIL if: <+1.5u combined OR parlay loss >5u
INVESTIGATE if: Mixed results or unclear pattern
```

**Phase 2**: ✓ Execute with checkpoints
```
Checkpoint 1 (setup): Environment ready, baseline known
Checkpoint 2 (after test): Backtest completed, results extracted
Checkpoint 3 (before decision): All metrics calculated
```

**Phase 3**: ✓ Investigation (because result is FAIL)
```
1. Mechanism: Did gate fire on 42 events as expected? ✓
2. Impact: Parlay -10.76u, others +3.85u total → net -6.91u loss
3. Hypothesis: Gate logic leaked into parlay scoring, or opponent stats insufficient
4. Learning: "Don't gate Method predictions in ways affecting parlay", "Parlay is fragile"
```

**Phase 4**: ✓ Structured logging
```
Hypothesis: Skip DEC when opponent StrDef <45% + SApM >4.0
Expected: +3-5u
Actual: +0.00u combined
Root Cause: Parlay loss (-10.76u) exceeded other gains (+3.85u)
Decision: ❌ FAIL
Learning: Gate mechanism flawed; don't modify Method scoring directly
```

**Phase 5**: ✓ Stop at boundary
```
Decision documented. Ready for next hypothesis.
[STOP — no pivot to other work]
```

**Total**: Deep investigation, clear learning, prevents future mistakes.

---

## Success Metrics

When GLM-5.1 executes via this framework:

1. **Error reduction**: Failures are understood, not just reverted → prevents repeat mistakes
2. **Efficiency**: Explicit criteria prevent wasted investigation on unclear results
3. **Learning**: Template capture ensures findings are remembered and applied
4. **Scope discipline**: Single-task boundaries prevent task creep and context loss
5. **Deeper thinking**: Phase 3 investigation uncovers root causes, not symptoms

---

## Reference: When This Applies

✓ Hypothesis testing (any domain, not just UFC)
✓ Algorithm refinement and optimization
✓ Bug fixing and debugging
✓ Refactoring and code changes
✓ Data exploration and research
✓ Experimentation and A/B testing
✓ System design and architecture decisions
✓ Performance tuning and optimization

---

## When This Does NOT Apply

✗ Simple tasks (read file, rename variable, run test)
✗ User-specified approaches with clear steps
✗ Maintenance tasks with known procedures
✗ Routine updates and standard operations

Use **lite planning** (PLAN + SANITY CHECK) for these. Use **full framework** only for complex tasks.
