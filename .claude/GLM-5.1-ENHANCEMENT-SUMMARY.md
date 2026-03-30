# GLM-5.1 Enhancement Strategy — Performance Improvements Based on Backtesting Task Analysis

**Date**: 2026-03-29
**Session**: Evaluation + Implementation of Hypothesis Testing Gaps
**Target**: Address 7 identified inefficiencies from backtesting task to improve GLM-5.1 hypothesis testing workflow

---

## Problem Statement

Analysis of GLM's backtesting hypothesis test (opponent durability gate) identified 7 critical gaps:

1. **No pre-test data validation** — jumped to code without validating hypothesis makes intuitive sense
2. **Vague pass/fail criteria** — expected "+3-5u" but accepted "+0.00u" as "neutral"
3. **Lazy on failure analysis** — parlay lost -10.76u but just reverted without investigating
4. **Inefficient status polling** — checked backtest status 5+ times with repeated "still running" messages
5. **Narration bloat** — ~30% of response was filler ("Let me...", "Let me check...", "Still running...")
6. **Task creep** — pivoted to repo sync, v11.17 backtest, future hypotheses instead of stopping at decision
7. **Incomplete documentation** — logged +0.00u result but didn't document affected fights or root cause

**Impact**: Wasted compute, confusing results, incomplete learnings, prevents systematic testing.

---

## Solution Architecture

### 1. **CLAUDE.md Rule 14: Hypothesis Testing Protocol**

Added to global rules enforcing 4-phase workflow:

```markdown
14. **Hypothesis Testing Protocol** (GLM-5.1 enhanced):
    - **Pre-test gate**: Before running backtest, ALWAYS sample 3-5 recent events
    - **Explicit criteria**: Set pass/fail threshold PRE-TEST (e.g., "Need +1.5u minimum")
    - **Batch operations**: Run backtest once, check once, report once. NO polling loops.
    - **Failure analysis**: When test returns negative/neutral, MUST analyze affected fights
    - **Single response scope**: One hypothesis test = one decision (PASS/FAIL/INVESTIGATE)
    - **Template logging**: Every experiment → EXPERIMENT_LOG.md with structured format
    - **Token efficiency**: Backtest status → single async run. Max 5 tool calls per test.
```

### 2. **glm5-hypothesis-testing-protocol.md** (344 lines)

Comprehensive protocol document with 5 phases + token efficiency checklist:

**Phase 1: Pre-Test Validation (5 min)**
- State hypothesis clearly
- Show mechanism (why it should work)
- Sample 3-5 recent events validating hypothesis applies
- Set explicit pass/fail thresholds
- Validate intuition before compute

**Phase 2: Test Execution (2-5 min compute)**
- Implement change (read, edit, verify syntax)
- Run backtest ONCE in background
- Single status check at +5 min
- Extract results with single query

**Phase 3: Decision Gate (2 min)**
- Compare against pre-set pass/fail criteria
- If unclear: Run root cause analysis
- Decision: PASS / FAIL / INVESTIGATE

**Phase 4: Documentation (2 min)**
- Log to EXPERIMENT_LOG.md with structured template
- Include hypothesis, expected, actual, delta, pass/fail, root cause, example fights

**Phase 5: Clear Next Steps**
- Ready for next hypothesis
- No auto-pivots to other work

**Token Efficiency**:
- Per-hypothesis budget: 1000-1500 tokens (vs 3000-4000 previously)
- Breakdown: Phase 1 (300-400), Phase 2 (50), Phase 3 (200-300), Phase 4 (400-500), Phase 5 (50)

### 3. **hypothesis-criteria-template.json** (200 lines)

Structured template with ALL required fields for hypothesis testing:

```json
{
  "Phase 1 PreTest": {
    "hypothesis_statement": "Must be specific and testable",
    "mechanism": "Must explain why, not just what changes",
    "expected_impact": "Quantified prediction with confidence level",
    "sample_validation_fights": "3-5 recent fights showing gate applies, with judgment",
    "pass_threshold": "Specific number (e.g., '+1.5u combined minimum')",
    "fail_threshold": "Revert decision point (e.g., '-5.0u = auto-revert')"
  },
  "Phase 3 Results": {
    "baseline_pl": "v11.17 P/L",
    "test_pl": "v11.18 P/L",
    "delta": "test_pl - baseline_pl",
    "per_stream_breakdown": "ML/Method/Combo/Parlay deltas",
    "pass_fail_decision": "✓ PASS / ❌ FAIL / ❓ INVESTIGATE"
  },
  "Phase 4 RootCauseAnalysis": {
    "required_if": "FAIL or INVESTIGATE",
    "root_cause": "Why did test fail?",
    "top_affected_fights": "3+ specific fights with amounts",
    "learnings": "What prevents re-testing this?"
  }
}
```

### 4. **glm5-hypothesis-pre-flight.py** Hook

Runs on UserPromptSubmit to detect hypothesis testing requests and validate Phase 1:

```python
Triggers on: "test hypothesis", "run backtest", "try this change", etc.
Checks: All Phase 1 elements present (hypothesis, mechanism, expected, sample, threshold)
If incomplete: Outputs Phase 1 reminder with template
If complete: Proceeds to execution
```

Integrated into settings.json UserPromptSubmit hooks (first in chain).

### 5. **glm5-experiment-validator.py** Hook (Pre-commit)

Validates before commits that v11.18+ algorithm changes are documented:

```python
Checks:
- ALG_VERSION v11.18+ detected in UFC_Alg_v4_fast_2026.py
- EXPERIMENT_LOG.md has entry for this version
- Entry includes: Hypothesis, Expected, Actual, Delta, Decision
- If FAIL/INVESTIGATE: Root cause and example fights documented

Result: ✓ PASS or ❌ FAIL with clear guidance on what's missing
```

---

## Implementation Summary

### Files Created

1. **glm5-hypothesis-testing-protocol.md** (344 lines)
   - 5-phase workflow with detailed instructions
   - Token efficiency checklist
   - Failure pattern interpretation guide
   - Example: Correct execution (10 min, 3000 tokens)

2. **hypothesis-criteria-template.json** (200 lines)
   - Structured template for ALL hypothesis testing
   - Phase-by-phase requirements
   - Token budget breakdown
   - Prohibitions list

3. **glm5-hypothesis-pre-flight.py** (Hook, ~70 lines)
   - UserPromptSubmit hook validating Phase 1 before execution
   - Detects hypothesis keywords
   - Checks for required elements
   - Outputs reminder if incomplete

4. **glm5-experiment-validator.py** (Hook, ~100 lines)
   - Pre-commit hook ensuring v11.18+ documented
   - Validates EXPERIMENT_LOG.md completeness
   - Prevents commits without proper logging

### Files Modified

1. **CLAUDE.md** — Added Rule 14: Hypothesis Testing Protocol
   - 7 enforcement points addressing each gap
   - Pre-test gate, explicit criteria, batch operations, failure analysis, single scope, template logging, token efficiency

2. **settings.json** — Added glm5-hypothesis-pre-flight.py to UserPromptSubmit
   - First in chain to catch hypothesis requests early
   - Validates Phase 1 before other processing

---

## Gap Resolution Matrix

| Gap | Root Cause | Solution | Enforcement |
|-----|-----------|----------|------------|
| No pre-test validation | Jumped to code | Phase 1 sampling + intuition check | hypothesis-pre-flight.py hook |
| Vague pass/fail criteria | No threshold set | Explicit "+X u" pass threshold pre-test | hypothesis-criteria-template.json |
| Lazy failure analysis | Just reverted | Mandatory root cause analysis | glm5-hypothesis-testing-protocol.md Phase 3 |
| Inefficient polling | Checked 5+ times | Single async run, one status check | CLAUDE.md Rule 14 "batch operations" |
| Narration bloat | Process narration | Zero narration, results-only focus | glm5-hypothesis-testing-protocol.md token budget |
| Task creep | No scope boundary | One hypothesis = one response | CLAUDE.md Rule 14 "single response scope" |
| Incomplete logging | Vague documentation | Template-enforced structured logging | experiment-validator.py pre-commit hook |

---

## Expected Improvements

### Token Efficiency
- **Before**: 3000-4000 tokens per hypothesis (50% narration, polling, pivot work)
- **After**: 1000-1500 tokens per hypothesis (results-focused, batched operations)
- **Savings**: ~60% reduction in tokens per test, enabling more hypothesis iterations

### Decision Clarity
- **Before**: Vague results ("neutral", "doesn't help", "maybe try again")
- **After**: Clear PASS/FAIL with documented reasoning and learnings

### Learning Retention
- **Before**: Log said "+0.00u" with no context on affected fights
- **After**: Log includes hypothesis, expected, actual, delta, root cause, 3+ example fights, decision

### Systematic Testing
- **Before**: Ad-hoc hypothesis testing with gaps
- **After**: 5-phase protocol ensuring every test is complete and documented

### Hypothesis Velocity
- **Before**: 1-2 hypotheses per session (inefficient execution)
- **After**: 3-5 hypotheses per session (faster execution, less wasted tokens)

---

## Integration Points

### For GLM-5.1

1. **UserPromptSubmit Hook** — hypothesis-pre-flight.py validates Phase 1 before any tool use
2. **CLAUDE.md Rule 14** — Global enforcement of hypothesis testing discipline
3. **Pre-commit Hook** — experiment-validator.py ensures documentation before merging

### For User

- Reference `glm5-hypothesis-testing-protocol.md` when testing new algorithm ideas
- Follow template in `hypothesis-criteria-template.json` for structured testing
- Check `EXPERIMENT_LOG.md` for history of past tests and learnings

---

## Next Steps

1. **Test the system** — Run next hypothesis through full 5-phase protocol
2. **Measure improvements** — Track token count, decision clarity, learnings captured
3. **Iterate** — Refine protocol based on what works in practice
4. **Document learnings** — Update protocol with new patterns/anti-patterns discovered

---

## Files Reference

```
~/.claude/
├── CLAUDE.md (updated with Rule 14)
├── glm5-hypothesis-testing-protocol.md (NEW — 344 lines)
├── hypothesis-criteria-template.json (NEW — 200 lines)
├── settings.json (updated with pre-flight hook)
├── GLM-5.1-ENHANCEMENT-SUMMARY.md (this file)
└── hooks/
    ├── glm5-hypothesis-pre-flight.py (NEW)
    └── glm5-experiment-validator.py (NEW)
```

---

## Validation

All components created and integrated:

✓ CLAUDE.md Rule 14 added
✓ Hypothesis testing protocol document created (344 lines)
✓ Criteria template JSON created (200 lines)
✓ Pre-flight hook created and integrated to settings.json
✓ Experiment validator pre-commit hook created
✓ Settings.json validated (valid JSON)

**Ready for next hypothesis test using full 5-phase protocol.**
