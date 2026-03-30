# Prompt for GLM-5.1: File Handling Discipline (MANDATORY)

Use this text when instructing GLM-5.1 on file handling requirements. This establishes non-negotiable standards to prevent data corruption like the v11.18 registry incident.

---

## THE PROMPT (copy/paste to GLM-5.1)

```
CRITICAL: File Handling Protocol — Enforce Before Any Edit

You must follow these rules without exception when working with data files, algorithm code,
or registry files. These rules exist because v11.18 hypothesis testing corrupted the registry
(+0.00u totals from incomplete restoration), wasting backtest compute and results.

RULE 1: NEVER Edit Files Without Backup First
— Before using Edit or Write on ANY algorithm file, registry, or result file, create a timestamped backup
— Backup naming: filename.pre-edit-{YYYYMMDD}_{HHMMSS}.bak (example: UFC_Alg_v4_fast_2026.py.pre-edit-20260329_173710.bak)
— Store backup in same directory as original
— Verify backup exists and contains original content BEFORE proceeding with edit
— The glm5-file-backup.py hook creates automatic backups on Edit operations
— You are responsible for verifying the backup was created successfully

RULE 2: Detect Corruption Immediately
— Corruption indicators for registry/summary files:
  • Totals calculation is invalid (sum of components ≠ reported total) ← MOST COMMON
  • Expected keys missing (e.g., parlay P/L missing from registry)
  • Data type changed (string instead of float, dict instead of list)
  • File size regression (new version smaller despite more data)
— Corruption indicators for algorithm files:
  • Syntax errors on import (try: import UFC_Alg_v4_fast_2026)
  • Version constant doesn't match expected (ALG_VERSION mismatch)
  • Key functions missing or moved
  • Gate logic doesn't execute (backtest shows 0 fights affected when gate should fire)

— Action on corruption: STOP immediately. Do NOT continue. Do NOT try to fix by editing.

RULE 3: Recover From Corruption Using Git History
— On corruption, restore from git:
  cd ~/Projects/ufc-predict
  git log --oneline | head -20
  # Find last commit BEFORE corruption occurred
  git checkout <commit-SHA> -- path/to/corrupted_file.json
— Verify restoration:
  cd ~/Projects/ufc-predict
  python3 -c "import json; r=json.load(open('UFC_registry.json')); print(f'Total: {sum([v[\"p_l\"] for v in r.values()])}')"
— Git is source of truth. Never try to "fix" a corrupted file by editing.

RULE 4: Add File Integrity Checks to Phase 2 Execution
— Before starting ANY hypothesis test (Phase 2 Checkpoint 1B):
  (1) Verify algorithm file imports: python3 -c "from UFC_Alg_v4_fast_2026 import *; print(ALG_VERSION)"
  (2) Verify registry structure: Check all required keys present + totals calculation correct
  (3) Verify baseline readable: Should match expected P/L (e.g., +285.25u for v11.17)

— After backtest completes (Phase 2 Checkpoint 2C):
  (1) Verify output file exists and > 100 bytes
  (2) Verify data structure: Totals match sum of components, no NaN values, all keys present
  (3) Verify against baseline: Same event count, same keys, same format

— If ANY check fails: Do NOT accept the results. Restore from git (RULE 3) and re-run.

RULE 5: Document All Operations in file-change-audit.md
— Every backup, edit, restore, corruption detection goes into file-change-audit.md
— Format:
  ## [Date] [Time] — [Operation Type]
  **File**: filename
  **Operation**: backup | edit | restore | corruption-detected | recovered
  **Details**: [What happened, root cause if corruption, recovery action if needed]
  **Status**: ✓ SUCCESS | ⚠ WARNING | ❌ FAILED

SUMMARY:
1. Backup BEFORE edit (hook does this; you verify it worked)
2. Detect corruption immediately (invalid totals, missing keys, syntax errors)
3. Restore from git history (git checkout, never manual editing)
4. Validate file integrity before AND after backtest
5. Log everything to audit trail

Reference: ~/.claude/glm5-file-handling-protocol.md for full protocol, examples, checklists.

This protocol is MANDATORY. Failure to follow it results in data corruption and wasted compute.
```

---

## How to Use This Prompt

### Option 1: Direct Instruction (Recommended)
Copy the prompt above and send it to GLM-5.1 in a new conversation:

```
[paste the prompt from THE PROMPT section above]

Acknowledge that you understand these rules and will follow them.
```

### Option 2: Make It Part of CLAUDE.md
The protocol is already added as Rule 16 in CLAUDE.md. GLM-5.1 reads CLAUDE.md at session start via context loading. The rule now enforces this protocol automatically.

### Option 3: Reference in Every Complex Task
When asking GLM-5.1 to test a hypothesis, include:

```
Before testing, review ~/.claude/glm5-file-handling-protocol.md.
Follow Rule 1 (backup before edit), Rule 2 (detect corruption), Rule 3 (recover from git).
Add Phase 2 integrity checks (Rule 4).
```

---

## What Changed (Why This Protocol Exists)

### The v11.18 Incident

**What happened**:
- Hypothesis test: 3-leg HC parlay variant
- Expected to improve ROI by +3-5u
- Backtest returned: +0.00u combined P/L (neutral)
- Issue: Registry totals showed +0.00u despite processing 71 events

**Root cause**:
- Registry file was restored from backtest_summary.json
- Restoration created incomplete format with invalid totals
- Totals calculation was broken (sum of components ≠ reported total)
- Corruption went undetected until AFTER backtest completed

**Impact**:
- Wasted backtest compute
- Invalid results (couldn't trust the outcome)
- Hypothesis appeared to fail when really the data structure was corrupted
- Needed manual restoration from git history (v11.17 baseline confirmed at +285.25u)

**Why this protocol prevents it**:
- Rule 1: Backup BEFORE edit — would have caught the restoration issue
- Rule 2: Detect corruption immediately — would have failed integrity checks post-restore
- Rule 4: Phase 2 Checkpoint 2C — would have caught invalid totals before accepting results
- Rule 3: Restore from git — provided clean recovery path without manual editing

---

## Enforcement

This protocol is now:

✅ **Rule 16 in CLAUDE.md** — Loaded at every session start
✅ **glm5-file-handling-protocol.md** — Full reference with examples
✅ **glm5-file-backup.py hook** — Automatic backups on Edit operations
✅ **file-change-audit.md** — Logs all operations for audit trail

GLM-5.1 cannot skip these rules. They are part of the mandatory execution framework.

---

## Quick Reference

| Rule | What | When |
|------|------|------|
| **1. Backup first** | Create timestamped backup before edit | Before every Edit tool call |
| **2. Detect corruption** | Check for invalid totals, missing keys, errors | After operations, immediately |
| **3. Restore from git** | Use git checkout to restore from last good version | When corruption detected |
| **4. Phase 2 checks** | Validate file structure before AND after backtest | Checkpoint 1B and 2C |
| **5. Audit log** | Document every operation in file-change-audit.md | After every significant operation |

---

## How to Verify GLM-5.1 Understands

After giving the prompt, ask:

**Test Question 1**: "If you detect that a registry totals calculation is invalid (sum of components doesn't equal reported total), what do you do?"
- Correct answer: "Stop immediately, do not continue, restore from git history to last known good version."

**Test Question 2**: "Before running a hypothesis test backtest, what Phase 2 integrity checks must pass?"
- Correct answer: "Algorithm syntax check, registry structure validation, baseline readability. If any fail, restore from git and re-run."

**Test Question 3**: "You're about to edit UFC_Alg_v4_fast_2026.py. What's your first step?"
- Correct answer: "Verify the backup hook created a timestamped backup successfully, then proceed with edit."

If GLM-5.1 answers all three correctly, the protocol has been understood.

---

## Files Reference

```
~/.claude/
├── CLAUDE.md (Rule 16: File Handling Protocol)
├── glm5-file-handling-protocol.md (FULL PROTOCOL — 230 lines)
├── GLM5-FILE-HANDLING-PROMPT.md (this file — prompt to give GLM-5.1)
├── file-change-audit.md (audit trail of all operations)
├── file-backups.json (registry of all backups)
└── hooks/
    └── glm5-file-backup.py (automatic backup creation on Edit)
```

---

## Next Steps

1. **Review** the full protocol: `cat ~/.claude/glm5-file-handling-protocol.md`
2. **Give the prompt** to GLM-5.1 in the next session or conversation
3. **Verify understanding** using the test questions above
4. **Test with next hypothesis** — ensure Phase 2 integrity checks pass before accepting results
5. **Monitor audit trail** — check file-change-audit.md after complex tasks to verify logging is working

---

**This protocol is MANDATORY as of 2026-03-29. No exceptions.**
