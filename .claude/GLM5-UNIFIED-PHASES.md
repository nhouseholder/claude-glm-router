# GLM-5.1 Unified Phases & Rules — Single Reference

**Quick reference for all 5 phases + file handling rules (one page)**

---

## PHASE 1: Success Criteria Definition (2 min)

**Before starting complex task, define PASS/FAIL/INVESTIGATE explicitly.**

```
TASK: [What are you trying to accomplish?]

SUCCESS CRITERIA:
- Primary: [Quantified outcome = success, e.g., "+1.5u improvement"]
- Secondary: [What else must hold? e.g., "no stream loses >5u"]

FAILURE CRITERIA:
- Auto-revert if: [e.g., "-5u loss = clearly failed"]
- Investigate if: [e.g., "mixed results = unclear"]

DECISION GATE:
✓ PASS: [Condition to proceed]
❌ FAIL: [Condition to revert]
❓ INVESTIGATE: [Condition for Phase 3]
```

**Enforcement**: glm5-execution-phase-detector.py blocks execution until Phase 1 complete.

---

## PHASE 2: Execution with Checkpoints (variable)

**Execute task with integrity validation at 3 checkpoints.**

```
Checkpoint 1: Setup
├─ Environment ready? Does local match remote?
└─ Baseline established?

Checkpoint 1B: File Integrity Validation (PRE-execution)
├─ Algorithm syntax: import without errors ✓
├─ Registry structure: all required keys present ✓
└─ Baseline readable: can load and verify values ✓

Checkpoint 2: Initial Test Results
├─ Test completed successfully?
└─ Results suggest promise or failure?

Checkpoint 2C: Post-Backtest Integrity Check (AFTER execution)
├─ Output file exists: > 100 bytes ✓
├─ Data structure valid: totals = sum of components ✓
└─ Matches baseline: same structure, same keys ✓

Checkpoint 3: Before Decision
├─ All metrics calculated?
└─ Ready for Phase 3 or Phase 4?
```

**Failure**: Any checkpoint fails → Restore from git, re-run Phase 2

**Reference**: glm5-execution-framework.md Phase 2

---

## PHASE 3: Mandatory Investigation (2-5 min)

**When Phase 2 returns FAIL or UNCLEAR, investigate deeply.**

```
Required ONLY if: Phase 2 result is FAIL or INVESTIGATE gate triggered

1. MECHANISM CHECK
   ├─ Did your change fire as expected?
   ├─ Sample 3-5 events showing mechanism applies
   └─ Does mechanism make intuitive sense?

2. IMPACT ANALYSIS
   ├─ Baseline P/L: [breakdown by stream]
   ├─ Test P/L: [breakdown by stream]
   ├─ Delta: [what changed]
   └─ Finding: [where did value get lost?]

3. HYPOTHESIS CHALLENGE
   ├─ Expected: [what you thought would happen]
   ├─ Observed: [what actually happened]
   └─ Why didn't it work? [3+ explanations]

4. LEARNING CAPTURE
   ├─ Root cause: [specific, not vague]
   ├─ Example: [3+ fights showing the problem]
   └─ Prevention: "Don't [specific action] because [reason]"
```

**Enforcement**: glm5-investigation-enforcer.py blocks Phase 4 if Phase 3 incomplete.

**Reference**: glm5-execution-framework.md Phase 3 (detailed with examples)

---

## PHASE 4: Structured Learning Capture (2 min)

**Document findings with template to prevent re-testing.**

```
Objective: [What were you trying to achieve?]

Approach: [What did you do?]

Success Criteria:
- Primary: [e.g., "+1.5u minimum"]
- Secondary: [e.g., "parlay stays positive"]

Results:
| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| [KPI] | [value] | [value] | ✓/❌ |

Root Cause Analysis (if FAIL/INVESTIGATE):
1. Symptom: [What failed?]
2. Mechanism: [How did you attempt to fix it?]
3. Impact: [Where was value lost?]
4. Hypothesis: [Why didn't mechanism work?]
5. Learning: [What prevents re-testing?]

Decision: ✓ PASS | ❌ FAIL | ❓ INVESTIGATE

Learnings:
- [Insight 1] — prevents future mistake
- [Insight 2] — suggests new approach
```

**Enforcement**: glm5-experiment-validator.py (pre-commit) ensures completeness.

**Output**: Entry in EXPERIMENT_LOG.md (prevents hypothesis reuse)

**Reference**: glm5-hypothesis-testing-protocol.md Phase 4

---

## PHASE 5: Scope Boundary & Stop (1 min)

**One task = one decision = one stop point. No auto-pivot.**

```
VALID STOP:
"Hypothesis FAILED due to [root cause]. Reverting. Ready for next hypothesis."

INVALID STOP:
"Hypothesis FAILED. Let me also run a full v11.17 backtest. And test 3 more hypotheses..."

BOUNDARY RULE:
After Phase 3/4 complete:
- Make decision: ✓ PASS | ❌ FAIL | ❓ INVESTIGATE
- State decision clearly
- STOP at that boundary
- No auto-pivot to related work
```

**Enforcement**:
- glm5-focus-guard.py (monitors for task-switching)
- no-narration-stops.py (prevents narration-only, enforces decision)
- unpushed-commits-check.py (blocks session exit without commit)

**Reference**: glm5-execution-framework.md Phase 5

---

## FILE HANDLING RULES (Cross-cutting)

**These apply to ANY complex task involving data/algorithm files.**

### RULE 1: Backup Before Edit
- **When**: Before EVERY Edit tool call on critical files
- **How**: Timestamped backup — `filename.pre-edit-{YYYYMMDD}_{HHMMSS}.bak`
- **Verify**: Backup exists before proceeding
- **Enforcement**: glm5-file-backup.py hook (PreToolUse on Edit)

### RULE 2: Detect Corruption Immediately
- **Indicators**: Invalid totals, missing keys, type changes, syntax errors
- **Action**: STOP. Do NOT continue. Do NOT edit to fix.
- **Enforcement**: Phase 2 Checkpoint 2C (post-execution validation)

### RULE 3: Restore From Git History
- **On corruption**: `git checkout <commit-SHA> -- path/to/file.json`
- **Never**: Try to "fix" corrupted file by manual editing
- **Source of truth**: Git, not local edits
- **Reference**: glm5-file-handling-protocol.md RULE 3

### RULE 4: Phase 2 Integrity Checkpoints
- **Checkpoint 1B (pre)**: Algorithm syntax, registry structure, baseline readable
- **Checkpoint 2C (post)**: Output exists, structure valid, totals match baseline
- **Failure**: Restore from git (RULE 3), re-run
- **Enforcement**: Phase 2 checkpoints (documented above)

### RULE 5: Audit All Operations
- **What to log**: Timestamp, file, operation (backup/edit/restore/corruption), status
- **Where**: file-change-audit.md
- **Enforcement**: glm5-file-backup.py hook auto-logs edits

---

## Quick Decision Tree

```
START complex task
    ↓
PHASE 1: Define success criteria (explicit PASS/FAIL)
    ↓
Check Phase 1 complete? → NO: output template, wait
    ↓ YES
PHASE 2: Execute with checkpoints (1, 1B, 2, 2C, 3)
    ↓
Result PASS? → YES: Go to Phase 4
    ↓ NO (FAIL or UNCLEAR)
PHASE 3: Mandatory investigation (mechanism, impact, hypothesis, learning)
    ↓
Investigation complete? → NO: glm5-investigation-enforcer blocks, re-run Phase 3
    ↓ YES
PHASE 4: Structured learning (template + EXPERIMENT_LOG.md)
    ↓
PHASE 5: Stop at boundary (decision + "Ready for next task")
```

---

## Checklists

### Pre-Test Checklist (Phase 1 → Phase 2)
- [ ] Success criteria defined (primary + secondary + decision gate)
- [ ] Hypothesis validated with 3-5 sample events
- [ ] Pass threshold explicitly set (not vague)
- [ ] Failure threshold set (auto-revert point)

### Pre-Backtest Checklist (Checkpoint 1B)
- [ ] Algorithm file imports without errors
- [ ] Registry structure is valid (all required keys)
- [ ] Registry totals calculation is correct
- [ ] Baseline file readable and matches expected

### Post-Backtest Checklist (Checkpoint 2C)
- [ ] Output file exists and > 100 bytes
- [ ] Output file valid JSON (imports without errors)
- [ ] Totals calculation correct (sum = reported)
- [ ] Event count matches baseline (no lost data)
- [ ] Data structure matches baseline (same keys/format)
- [ ] No NaN values or negative counts

### Pre-Phase-4 Checklist (Phase 3 completion)
- [ ] Mechanism verified with 3+ sample events
- [ ] Impact analysis complete (baseline vs. test breakdown)
- [ ] Hypothesis challenged (why didn't it work?)
- [ ] Learning documented (prevention statement clear)
- [ ] No ambiguity in root cause analysis

---

## Files Reference

```
~/.claude/
├── CLAUDE.md (Rules 14-16)
├── glm5-execution-framework.md (5-phase protocol, detailed)
├── glm5-hypothesis-testing-protocol.md (hypothesis-specific, token efficiency)
├── glm5-file-handling-protocol.md (file safety, recovery procedures)
├── GLM5-UNIFIED-PHASES.md (this file — one-page reference)
└── hooks/
    ├── glm5-execution-phase-detector.py (enforces Phase 1)
    ├── glm5-investigation-enforcer.py (enforces Phase 3)
    ├── glm5-file-backup.py (Rule 1 backup)
    ├── glm5-focus-guard.py (enforces Phase 5 boundary)
    └── [others supporting phases]
```

---

## One-Line Summary Per Phase

| Phase | What | Why |
|-------|------|-----|
| **1** | Define PASS/FAIL before starting | Prevents wasting compute on ambiguous results |
| **2** | Execute with integrity checkpoints | Catches corruption before accepting results |
| **3** | Investigate if FAIL/UNCLEAR | Prevents repeating mistakes unknowingly |
| **4** | Document structured learning | Prevents re-testing same hypothesis |
| **5** | Stop at decision boundary | Prevents task creep and context loss |

---

**Print this page. Reference it before every complex task.**
