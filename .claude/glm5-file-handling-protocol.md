# GLM-5.1 File Handling Protocol — Mandatory Backup, Recovery, and Integrity Enforcement

**Status**: CRITICAL — File corruption incident (v11.18) revealed gaps. This protocol is now MANDATORY.

**Date**: 2026-03-29

**Incident**: Registry corruption during v11.18 hypothesis testing (3-leg HC parlay). Backtest showed +0.00u combined P/L despite 71 events. Root cause: restoration from backtest_summary.json created incomplete registry structure with invalid totals.

---

## RULE 1: NEVER Edit Files Without Backup First

**When this applies**:
- ANY edit to production algorithm files (UFC_Alg_v4_fast_2026.py)
- ANY write to data registry files (registry.json, fight_registry.json, etc.)
- ANY modification to backtest result files or summary files
- ANY configuration changes affecting test integrity

**What "backup first" means**:
1. Before using Edit or Write tool on a file, manually create a timestamped backup
2. Backup naming: `filename.pre-edit-{YYYYMMDD}_{HHMMSS}.bak`
3. Example: Before editing `UFC_Alg_v4_fast_2026.py`, create `UFC_Alg_v4_fast_2026.py.pre-edit-20260329_173710.bak`
4. Store backup in same directory as original (or in `.backups/` subdirectory)
5. Verify backup file exists and contains original content before proceeding with edit

**Enforcement**:
- The glm5-file-backup.py hook creates timestamped backups automatically for Edit operations
- YOU must also manually verify the backup exists before editing critical files
- If backup hook fails, STOP and report error before proceeding with edit
- "I'll create a backup later" = violation. Backup FIRST, edit SECOND.

---

## RULE 2: Detect File Corruption Immediately

**Corruption indicators** (data structure changes):

Registry/summary files:
- Totals calculation is invalid (sum of components ≠ reported total)
- Expected keys missing (e.g., parlay P/L missing from registry)
- Data type changed (string instead of float, dict instead of list)
- File size regression (new version smaller than previous despite more data)

Algorithm files:
- Syntax errors on import (try `import UFC_Alg_v4_fast_2026`)
- Version constant doesn't match expected (ALG_VERSION mismatch)
- Key functions missing or moved
- Gate logic no longer executes (backtest shows no fights affected when gate should fire)

**When you detect corruption**:
1. STOP immediately — do not continue with the hypothesis test
2. Document the corruption: what file, what changed, what should be correct
3. **Do NOT try to fix it by editing** — proceed directly to recovery

---

## RULE 3: Recover From Corruption Using Git History

**Recovery procedure** (in order):

### Step 1: Identify Last Known Good Version
```bash
cd ~/Projects/ufc-predict
git log --oneline | head -20
# Look for last commit BEFORE corruption occurred
# For v11.18 corruption: find last commit with v11.17 that was confirmed working
```

### Step 2: Verify That Version in Git
```bash
git show <commit-SHA>:path/to/file.json | head -50
# Verify the file structure looks correct
# Check totals calculations are valid
```

### Step 3: Restore From Git History
```bash
cd ~/Projects/ufc-predict
git checkout <commit-SHA> -- path/to/corrupted_file.json
# This restores the file to its last known good state
```

### Step 4: Verify Restoration
```bash
# Re-run the integrity checks that failed
# For registry: verify sum of components = reported total
# For algorithm: verify ALG_VERSION matches and functions execute
# For backtest: spot-check 2-3 events to ensure data is sensible
```

### Step 5: Document the Recovery
- Log what was corrupted, why (root cause), when discovered
- Note the commit SHA you restored from
- Add entry to file-change-audit.md documenting recovery action
- Example: `[2026-03-29 17:40] RECOVERED registry.json from commit abc123def — restoration from backtest_summary.json had created invalid totals. Restored to confirmed working state.`

**Example for v11.18 incident**:
```bash
cd ~/Projects/ufc-predict
git log --oneline | grep "v11.17"
# Returns: abc123d Fix: v11.17 baseline confirmed +285.25u
git checkout abc123d -- UFC_registry.json
# Registry now restored to pre-v11.18 state
python3 -c "import json; r=json.load(open('UFC_registry.json')); print(f'Total: {sum([v[\"p_l\"] for v in r.values()])}')"
# Verify totals calculation is now valid
```

---

## RULE 4: Improved File Handling — Phase 2 Checkpoints

Add data integrity validation to the execution framework Phase 2 (Execution with Checkpoints).

### Checkpoint 1B: File Integrity Validation (NEW)

**Before starting ANY hypothesis test**:

1. **Verify algorithm file structure**:
   ```bash
   python3 -c "from UFC_Alg_v4_fast_2026 import *; print(f'ALG_VERSION: {ALG_VERSION}')"
   # Should print expected version without errors
   ```

2. **Verify registry structure**:
   ```bash
   python3 << 'EOF'
   import json
   with open('UFC_registry.json') as f:
       reg = json.load(f)
   # Check: All required keys present
   assert 'metadata' in reg, "Missing metadata key"
   assert 'fights' in reg, "Missing fights key"
   # Check: Totals calculation is valid
   fight_pls = [f['p_l'] for f in reg['fights'].values()]
   reported_total = reg['metadata']['total_pl']
   actual_total = sum(fight_pls)
   assert abs(actual_total - reported_total) < 0.01, f"Total mismatch: {actual_total} vs {reported_total}"
   print(f"✓ Registry valid: {len(fight_pls)} fights, total P/L {actual_total:.2f}u")
   EOF
   ```

3. **Verify baseline file is readable**:
   ```bash
   python3 -c "import json; b=json.load(open('baseline.json')); print(f'Baseline: {b[\"total_pl\"]:.2f}u')"
   # Should match expected baseline (e.g., +285.25u for v11.17)
   ```

**Action if validation fails**:
- Do NOT proceed with hypothesis test
- Restore corrupted file from git history (RULE 3)
- Re-run validation
- Only proceed when all checks pass

### Checkpoint 2C: Post-Backtest Integrity Check (NEW)

**After backtest completes, BEFORE accepting results**:

1. **Verify backtest output file exists and is readable**:
   ```bash
   ls -lh backtest_output.json
   # Check: file size > 100 bytes (not empty)
   python3 -c "import json; o=json.load(open('backtest_output.json')); print(f'Events: {len(o[\"fights\"])}, P/L: {o[\"total_pl\"]:.2f}u')"
   ```

2. **Verify data structure correctness**:
   ```bash
   python3 << 'EOF'
   import json
   with open('backtest_output.json') as f:
       backtest = json.load(f)
   # Check: Totals match sum of components
   fight_pls = [f['p_l'] for f in backtest['fights'].values()]
   reported_total = backtest['total_pl']
   actual_total = sum(fight_pls)
   assert abs(actual_total - reported_total) < 0.01, f"CORRUPTION: Total {actual_total} vs reported {reported_total}"
   # Check: No negative event counts or NaN values
   for fight_id, fight in backtest['fights'].items():
       assert fight['p_l'] == fight['p_l'], f"NaN detected in fight {fight_id}"
   print(f"✓ Backtest output valid")
   EOF
   ```

3. **Verify against baseline**:
   ```bash
   python3 << 'EOF'
   import json
   with open('baseline.json') as f:
       baseline = json.load(f)
   with open('backtest_output.json') as f:
       test = json.load(f)
   # Check: Same event count (no lost data)
   assert len(baseline['fights']) == len(test['fights']), "Event count mismatch"
   # Check: Same streams (no missing data structure)
   baseline_keys = set(baseline.keys())
   test_keys = set(test.keys())
   assert baseline_keys == test_keys, f"Structure mismatch: {baseline_keys - test_keys} missing"
   print(f"✓ Backtest matches baseline structure")
   EOF
   ```

**Action if integrity check fails**:
- DO NOT accept the backtest results
- Do NOT proceed to Phase 3 (Decision Gate)
- Log the corruption and restore from git history (RULE 3)
- Re-run the hypothesis test from Phase 2 start
- Report the corruption incident to user

---

## RULE 5: Document All File Operations in Audit Log

Every backup, edit, restore, or corruption detection goes into `file-change-audit.md`:

```markdown
## [Date] [Time] — Operation Type

**File**: filename
**Operation**: backup | edit | restore | corruption-detected | recovered
**Context**: What hypothesis or task triggered this operation
**Details**:
- Before state: [file size, key hash, or descriptor]
- After state: [same]
- Root cause (if corruption): [what went wrong]
- Recovery action (if needed): [what was done]

**Status**: ✓ SUCCESS | ⚠ WARNING | ❌ FAILED
```

Example:
```markdown
## 2026-03-29 17:37 — Corruption Detected

**File**: UFC_registry.json
**Operation**: corruption-detected
**Context**: v11.18 hypothesis testing (3-leg HC parlay variant)
**Details**:
- Before state: 71 fights, totals validated +285.25u
- After state: 71 fights, totals showed +0.00u (INVALID)
- Root cause: Restoration from backtest_summary.json created incomplete registry format
- Recovery action: Restored from commit abc123d (v11.17 confirmed baseline)

**Status**: ✓ RECOVERED
```

---

## Integration: Where These Rules Apply

### Phase 2 Enhanced (Execution with Checkpoints)

```
Phase 2 Execution:
├─ Checkpoint 1: Setup (existing)
├─ Checkpoint 1B: File Integrity Validation (NEW — RULE 4)
│  ├─ Verify algorithm syntax
│  ├─ Verify registry structure
│  └─ Verify baseline readable
├─ Checkpoint 2: Initial test (existing)
├─ Checkpoint 2C: Post-Backtest Integrity Check (NEW — RULE 4)
│  ├─ Verify output file exists
│  ├─ Verify data structure
│  └─ Verify against baseline
└─ Checkpoint 3: Before decision (existing)
```

### Pre-Tool-Use Protection (Existing)

The glm5-file-backup.py hook creates timestamped backups automatically before Edit operations.
YOU must verify the backup was created before editing critical files.

### Git-Based Recovery (RULE 3)

When corruption is detected, always restore from git history.
Never try to "fix" a corrupted file by editing it — restore instead.

---

## Checklist: Before Starting Any Hypothesis Test

- [ ] Algorithm file imports without errors
- [ ] Registry structure is valid (all required keys present)
- [ ] Registry totals calculation is correct (sum of fights = reported total)
- [ ] Baseline file is readable and shows expected P/L
- [ ] Backup of algorithm file created pre-edit
- [ ] Phase 1 success criteria defined explicitly
- [ ] Ready to proceed to Phase 2 Execution

---

## Checklist: After Backtest Completes

- [ ] Backtest output file exists and > 100 bytes
- [ ] Output file is valid JSON (imports without errors)
- [ ] Totals calculation is correct (sum of fights = reported total)
- [ ] Event count matches baseline (no lost data)
- [ ] Data structure matches baseline (same keys, same format)
- [ ] No NaN values or negative counts
- [ ] Ready to proceed to Phase 3 Decision Gate

**If ANY check fails**: Restore from git history (RULE 3) and re-run backtest.

---

## Summary

| Rule | What | Why |
|------|------|-----|
| **RULE 1** | NEVER edit without backup first | v11.18 was edited without backup verification |
| **RULE 2** | Detect corruption immediately | Corruption was detected AFTER backtest, wasted results |
| **RULE 3** | Recover using git history | Git is source of truth; rollback is clean and verifiable |
| **RULE 4** | Add Phase 2 checkpoints | Validate file integrity before AND after backtest |
| **RULE 5** | Audit all operations | Prevents loss of context; helps identify patterns |

**This protocol is MANDATORY starting immediately. File handling discipline is not optional.**
