# GLM-5.1 Master Strategy — From Task Inefficiency to Deep Investigation Framework

**Date**: 2026-03-29
**Context**: Evaluation of backtesting task revealed 4 root execution problems affecting ALL complex tasks
**Solution**: Two-layer enhancement strategy (specific + general)

---

## Problem: 4 Root Execution Issues Visible in Backtesting Task

| Problem | Manifestation | Impact | Root Cause |
|---------|---|---|---|
| **Success criteria ambiguity** | Accepted "+0.00u" as valid; couldn't say "fail" clearly | Wasted compute on null results | No explicit pass/fail thresholds pre-execution |
| **Investigation depth** | Parlay lost -10.76u but just reverted; didn't ask WHY | Repeated same mistakes unknowingly | Stopping at symptoms, not root causes |
| **Learning capture** | Logged "+0.00u, revert" with no context; can't prevent re-testing | Hypothesis reuse across sessions | Template-less, incomplete documentation |
| **Scope creep** | After hypothesis failed, pivoted to repo sync + v11.17 backtest + future hypotheses | Original task never cleanly finished; context loss | No decision boundary enforcement |

**Insight**: These aren't hypothesis-testing problems. They're **GLM-5.1 execution problems** affecting bug fixes, refactors, research, optimization, and ANY complex task.

---

## Solution: Two-Layer Strategy

### Layer 1: Specific (Hypothesis Testing Enhanced)
**File**: `glm5-hypothesis-testing-protocol.md`
**Scope**: Hypothesis testing only
**Features**:
- 5-phase workflow (Pre-Test → Execute → Decide → Document → Next)
- Token efficiency (1000-1500 per test)
- Template-enforced logging

**Status**: ✅ Implemented

---

### Layer 2: General (Execution Framework)
**File**: `glm5-execution-framework.md`
**Scope**: ALL complex tasks (hypothesis testing, bug fixes, refactors, research, optimization)
**Features**:
- 5-phase general execution protocol
- Success criteria definition BEFORE starting
- Mandatory investigation protocol when results are FAIL/UNCLEAR
- Template-enforced learning capture
- Scope boundary enforcement (one task = one decision)

**Status**: ✅ Implemented (NEW)

---

## How Layer 2 (General Framework) Prevents Layer 1 (Specific) Problems

### Problem 1: Success Criteria Ambiguity
**Layer 1 fix** (Hypothesis-specific):
- Pre-test gate with "+1.5u minimum" threshold

**Layer 2 fix** (General, applicable everywhere):
- **Phase 1**: Success Criteria Definition
- Before ANY complex task, define PASS/FAIL/INVESTIGATE criteria explicitly
- Prevents "neutral" from being accepted because threshold was never set
- Applies to: hypothesis testing, bug fixes, refactors, research, etc.

---

### Problem 2: Investigation Depth
**Layer 1 fix** (Hypothesis-specific):
- Mandatory failure analysis: mechanism check, impact analysis, hypothesis challenge, learning capture

**Layer 2 fix** (General):
- **Phase 3**: Failure Investigation Protocol
- 4-step mandatory process: (1) did gate fire? (2) where was value lost? (3) why didn't mechanism work? (4) what prevents re-testing?
- Applies to: hypothesis testing, bug debugging, refactor issues, research contradictions

---

### Problem 3: Learning Capture
**Layer 1 fix** (Hypothesis-specific):
- Template logging with hypothesis, expected, actual, delta, root cause, fights, decision

**Layer 2 fix** (General):
- **Phase 4**: Structured Learning Capture
- Same template applied to ANY complex task: objective, approach, success criteria, results, root cause (if failed), learnings, decision
- Enables retention across sessions and projects

---

### Problem 4: Scope Creep
**Layer 1 fix** (Hypothesis-specific):
- "One hypothesis = one response" rule

**Layer 2 fix** (General):
- **Phase 5**: Scope Boundary Enforcement
- Single-task scope rule applies to hypothesis testing, bug fixing, refactoring, research
- One task execution = one decision = one stop point
- No auto-pivot to related work

---

## Implementation Map

### Files Created

1. **glm5-execution-framework.md** (550 lines)
   - General 5-phase protocol for all complex tasks
   - 4 root problems + their fixes
   - Task-type examples (hypothesis, bug fix, refactor, research)
   - When to apply / when not to apply

2. **glm5-execution-phase-detector.py** (Hook, 80 lines)
   - Runs on UserPromptSubmit
   - Detects complex tasks (hypothesis, bug, refactor, research, feature, optimization)
   - Enforces Phase 1 completion before execution
   - Outputs Phase 1 template if missing

### Files Modified

1. **CLAUDE.md**
   - Added Rule 14: Execution Framework (5 phases, applies to all complex tasks)
   - Moved Rule 15: Hypothesis Testing Protocol (Layer 1 specific fix)

2. **settings.json**
   - Added glm5-execution-phase-detector.py to UserPromptSubmit (first in chain)
   - Detects ALL complex tasks, not just hypotheses

---

## How They Work Together

### When User Asks to Test Hypothesis

```
UserPromptSubmit hooks fire:
1. glm5-execution-phase-detector.py → Detects "test hypothesis", checks Phase 1
2. glm5-hypothesis-pre-flight.py → Hypothesis-specific Phase 1 validation
```

**Result**: Dual validation ensures both general framework AND hypothesis-specific requirements are met.

### When User Asks to Fix Bug

```
UserPromptSubmit hooks fire:
1. glm5-execution-phase-detector.py → Detects "fix bug", checks Phase 1
2. [No hypothesis-specific hook — not needed]
```

**Result**: General framework applies; bug is fixed with proper success criteria, investigation protocol, learning capture.

### When User Asks to Refactor

```
UserPromptSubmit hooks fire:
1. glm5-execution-phase-detector.py → Detects "refactor", checks Phase 1
2. [Other project-specific hooks may fire]
```

**Result**: Refactor follows 5-phase protocol with success criteria, investigation if tests fail, learning capture.

---

## Example: Correct Execution Using Combined Framework

### Task: Test Algorithm Hypothesis (uses both layers)

**UserPromptSubmit**: glm5-execution-phase-detector.py detects task

**Phase 1** (General + Hypothesis-specific):
```
✓ Define success: "PASS if ≥+1.5u combined AND parlay P/L stays positive"
✓ Define failure: "FAIL if mixed results or parlay loss >5u"
✓ Sample validation: Show 3-5 fights where gate would apply
✓ Validate intuition: Does mechanism make sense?
```

**Phase 2** (Execution):
```
✓ Implement change (read, edit, verify syntax)
✓ Run backtest once (background)
✓ Checkpoint 1: Setup successful
✓ Checkpoint 2: Results extracted
✓ Checkpoint 3: Metrics calculated
```

**Phase 3** (Investigation — General + Hypothesis-specific):
```
✓ Mechanism check: Did gate fire on 42 events as expected?
✓ Impact analysis: Where was value lost? (Parlay -10.76u, others +3.85u)
✓ Hypothesis challenge: Why didn't the mechanism work? (Gate logic leaked into parlay)
✓ Learning capture: "Don't gate Method predictions in ways affecting parlay"
```

**Phase 4** (Learning Capture):
```
✓ Structured log entry with template
✓ Hypothesis + mechanism documented
✓ Expected vs actual with deltas
✓ Root cause analysis with example fights
✓ Decision: ❌ FAIL
✓ Learnings prevent re-testing
```

**Phase 5** (Scope Boundary):
```
Decision documented.
✓ STOP at this boundary.
"Ready for next hypothesis." [NO pivot to other work]
```

---

## Example: Correct Execution for Bug Fix (uses general framework only)

### Task: Fix Login Bug

**UserPromptSubmit**: glm5-execution-phase-detector.py detects "fix bug"

**Phase 1**:
```
✓ Define success: "PASS when: (1) bug reproduces in test, (2) fix applied, (3) test passes, (4) no regressions in auth suite"
✓ Define failure: "FAIL if fix breaks other auth flows or doesn't reproduce the original bug"
```

**Phase 2** (Execution with checkpoints):
```
✓ Checkpoint 1: Reproduce bug in isolated test ← **MUST pass**
✓ Checkpoint 2: Identify root cause in code
✓ Checkpoint 3: Apply fix
✓ Checkpoint 4: Verify test now passes
✓ Checkpoint 5: Run full auth suite for regressions
```

**Phase 3** (Investigation if needed):
```
If test still fails after fix:
1. Mechanism: Did the fix change what it was supposed to?
2. Impact: Which code path is still broken?
3. Root cause: Why is the fix incomplete?
4. Learning: Document the real root cause, update fix
```

**Phase 4** (Learning):
```
Bug: [What was broken]
Root cause: [Why]
Fix: [How to prevent]
Test case: [To catch regression]
Learning: [What this reveals about the system]
```

**Phase 5** (Stop):
```
Bug verified fixed. ✓ STOP.
No refactoring surrounding code, no optimization, no "while I'm here" changes.
"Bug fixed and verified. Ready for next task."
```

---

## Preventing the 4 Root Problems Going Forward

### For Hypothesis Testing (uses both layers)
- **Layer 1** (glm5-hypothesis-testing-protocol.md): Specific, optimized workflow
- **Layer 2** (glm5-execution-framework.md): General enforcement of all phases

### For Bug Fixes (uses general layer)
- **Layer 2** enforces: Success criteria before fixing, investigation on failure, learning capture, scope boundary

### For Refactors (uses general layer)
- **Layer 2** enforces: Tests must pass (success criteria), investigation if they don't, learning from failure patterns, stop at refactor completion

### For Research (uses general layer)
- **Layer 2** enforces: Research question clear (success criteria), investigation if findings contradict, learning captured, stop at conclusion

### For Optimization (uses general layer)
- **Layer 2** enforces: Performance improvement target (success criteria), root cause analysis if doesn't improve, learning from profiling data, stop when target reached

---

## Integration Points

### CLAUDE.md
- Rule 14: Execution Framework (5 phases, applies to ALL complex tasks)
- Rule 15: Hypothesis Testing Protocol (Layer 1 specific enhancements)

### settings.json
- glm5-execution-phase-detector.py → UserPromptSubmit (catches all complex tasks)
- glm5-hypothesis-pre-flight.py → UserPromptSubmit (hypothesis-specific validation)

### Hooks
- glm5-execution-phase-detector.py: General task detection + Phase 1 enforcement
- glm5-hypothesis-pre-flight.py: Hypothesis-specific Phase 1 validation
- glm5-hypothesis-testing-protocol.md: Reference for Layer 1 workflow
- glm5-execution-framework.md: Reference for Layer 2 framework

---

## Success Metrics: How We Know This Works

### Before (from backtesting task):
- ❌ Accepted "+0.00u" as valid result (no criteria)
- ❌ Reverted parlay loss without investigating why (shallow)
- ❌ Logged "+0.00u, revert" with no learning (incomplete)
- ❌ Pivoted to other work after hypothesis failed (scope creep)

### After (with framework):
- ✅ Phase 1 forces explicit PASS/FAIL before testing
- ✅ Phase 3 forces investigation: mechanism, impact, hypothesis challenge, learning
- ✅ Phase 4 forces structured logging with root cause + examples
- ✅ Phase 5 forces scope boundary: decision → stop, no pivot

### Measurable Outcomes:
- Fewer re-tested hypotheses (learning capture prevents)
- Clear PASS/FAIL decisions (no ambiguous "neutral")
- Understood failures (investigation protocol applies to any task type)
- No orphaned investigations (scope boundary prevents pivoting)

---

## What This Enables

This two-layer strategy enables:

1. **Systematic improvement**: Every complex task follows 5 phases, captures learnings, prevents repeat mistakes
2. **Cross-project consistency**: Same framework applies to UFC, bugs, refactors, research across all projects
3. **Deeper investigation**: Phase 3 protocol uncovers root causes, not symptoms
4. **Learning persistence**: Phase 4 ensures findings are documented and retained
5. **Scope discipline**: Phase 5 prevents task creep and context loss

---

## Files Reference

```
~/.claude/
├── CLAUDE.md (Rules 14-15 added)
├── glm5-execution-framework.md (NEW — general 5-phase protocol)
├── glm5-hypothesis-testing-protocol.md (existing — Layer 1 specific)
├── GLM-5.1-MASTER-STRATEGY.md (this file)
├── settings.json (updated with phase-detector hook)
└── hooks/
    ├── glm5-execution-phase-detector.py (NEW — catches all complex tasks)
    └── glm5-hypothesis-pre-flight.py (existing — hypothesis-specific)
```

---

## Next: Apply Framework to Next Task

Ready to test the framework on any complex task:
- Hypothesis testing
- Bug fixing
- Refactoring
- Research
- Optimization
- Experimentation

All will follow the 5-phase protocol with success criteria, investigation depth, learning capture, and scope boundaries.
