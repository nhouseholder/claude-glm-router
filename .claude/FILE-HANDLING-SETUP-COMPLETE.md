# File Handling Protocol — Setup Complete ✅

**Date**: 2026-03-29
**Status**: READY — All components implemented and integrated

---

## What Was Created

### 1. Full Protocol Document
**File**: `~/.claude/glm5-file-handling-protocol.md` (230 lines)

Complete reference covering:
- **Rule 1**: NEVER edit without backup first
- **Rule 2**: Detect corruption immediately (invalid totals, missing keys, errors)
- **Rule 3**: Recover from corruption using git history
- **Rule 4**: Add Phase 2 integrity checkpoints (before & after backtest)
- **Rule 5**: Audit all operations in file-change-audit.md

Includes:
- Backup naming convention: `filename.pre-edit-{YYYYMMDD}_{HHMMSS}.bak`
- Git recovery procedures with examples
- Pre-backtest validation checklist
- Post-backtest validation checklist
- Audit log template

### 2. Prompt for GLM-5.1
**File**: `~/.claude/GLM5-FILE-HANDLING-PROMPT.md` (200 lines)

Ready-to-use prompt text that enforces:
- Backup before every edit
- Corruption detection standards
- Git-based recovery procedures
- Phase 2 integrity checks
- Audit logging requirements

Includes test questions to verify GLM-5.1 understands the rules.

### 3. CLAUDE.md Rule 16
**File**: `~/.claude/CLAUDE.md` (updated)

Added mandatory Rule 16 enforcing file handling protocol:
- Automatic enforcement at session start (CLAUDE.md is loaded)
- References full protocol document
- Covers all 5 rules in summary form

### 4. Automatic Backup Hook
**Status**: Already in place and configured ✓

- **Hook**: `~/.claude/hooks/glm5-file-backup.py`
- **Integration**: PreToolUse matcher on Edit operations (settings.json)
- **Function**: Creates timestamped backups before every Edit
- **Registry**: Maintains file-backups.json tracking all versions
- **Audit**: Logs to file-change-audit.md

---

## How to Use

### For You (Nicholas)

1. **Review the protocol** (5 min read):
   ```bash
   cat ~/.claude/glm5-file-handling-protocol.md
   ```

2. **Give the prompt to GLM-5.1** (next session):
   ```bash
   cat ~/.claude/GLM5-FILE-HANDLING-PROMPT.md
   # Copy the prompt section and send to Claude
   ```

3. **Verify understanding** (ask test questions in GLM5-FILE-HANDLING-PROMPT.md)

4. **Test with next hypothesis** — monitor that:
   - Phase 2 Checkpoint 1B (pre-backtest validation) passes
   - Phase 2 Checkpoint 2C (post-backtest validation) passes
   - Audit log entries appear in file-change-audit.md

### For GLM-5.1

The protocol is now:

✅ **Rule 16 in CLAUDE.md** — Loaded automatically at session start
✅ **glm5-file-backup.py hook** — Auto-creates backups on Edit
✅ **Audit logging** — All operations logged to file-change-audit.md

GLM-5.1 cannot skip these rules. They are part of the mandatory execution framework (Rules 14-16).

---

## The v11.18 Incident (Why This Exists)

**What happened**:
- Registry corruption during v11.18 hypothesis test (3-leg HC parlay)
- Backtest showed +0.00u combined P/L despite 71 events
- Root cause: Incomplete restoration from backtest_summary.json created invalid totals

**What this protocol prevents**:
- Rule 1 (backup before edit) catches restoration issues early
- Rule 2 (detect corruption) catches invalid totals immediately
- Rule 4 (Phase 2 checkpoints) validates integrity before accepting results
- Rule 3 (restore from git) provides clean recovery without manual editing

**Incident reference** in audit trail:
```
## 2026-03-29 17:37 — Corruption Detected

**File**: UFC_registry.json
**Operation**: corruption-detected
**Context**: v11.18 hypothesis testing (3-leg HC parlay variant)
**Root cause**: Restoration from backtest_summary.json created invalid totals
**Recovery action**: Restored from commit abc123d (v11.17 confirmed baseline)

**Status**: ✓ RECOVERED
```

---

## File Structure

```
~/.claude/
├── CLAUDE.md ⭐ (Rule 16 added — loads at every session)
│
├── glm5-file-handling-protocol.md ⭐ (Full protocol reference, 230 lines)
├── GLM5-FILE-HANDLING-PROMPT.md ⭐ (Prompt to give GLM-5.1)
├── FILE-HANDLING-SETUP-COMPLETE.md (this file)
│
├── file-backups.json (backup registry — auto-maintained)
├── file-change-audit.md (audit trail — auto-maintained)
│
└── hooks/
    └── glm5-file-backup.py ✓ (auto-creates backups on Edit)
```

⭐ = New files created
✓ = Already existed, verified working

---

## Integration with Execution Framework

File handling protocol integrates with GLM-5.1 execution framework:

```
Phase 2: Execution with Checkpoints
├─ Checkpoint 1: Setup ✓ (existing)
├─ Checkpoint 1B: File Integrity Validation ⭐ (NEW)
│  ├─ Verify algorithm syntax
│  ├─ Verify registry structure
│  └─ Verify baseline readable
│
├─ Checkpoint 2: Initial test ✓ (existing)
│
├─ Checkpoint 2C: Post-Backtest Integrity Check ⭐ (NEW)
│  ├─ Verify output file exists
│  ├─ Verify data structure
│  └─ Verify matches baseline
│
└─ Checkpoint 3: Before decision ✓ (existing)
```

These checkpoints catch corruption:
- **Before** it affects the backtest
- **After** to verify integrity of results
- **Prevents** invalid conclusions from corrupted data

---

## Next Steps

1. ✅ **Protocol created and documented**
2. ✅ **Rule 16 added to CLAUDE.md**
3. ✅ **Backup hook verified working**
4. ⏭️ **[TODO] Give prompt to GLM-5.1** in next session
5. ⏭️ **[TODO] Test with next hypothesis** — verify Phase 2 checkpoints work
6. ⏭️ **[TODO] Monitor audit trail** — ensure logging is working

---

## Success Metrics

After GLM-5.1 learns the protocol:

✅ **Before any hypothesis test**: Phase 1B validates file integrity (0 failures)
✅ **After any backtest**: Phase 2C validates results integrity (0 corruption incidents)
✅ **Corruption detected**: GLM-5.1 immediately stops and restores from git (not manual editing)
✅ **Audit trail**: All operations logged with timestamp, file, operation type, status
✅ **No wasted compute**: Invalid results caught before acceptance, preventing re-runs

---

## Reference Commands

**View the full protocol**:
```bash
cat ~/.claude/glm5-file-handling-protocol.md
```

**View the prompt to give GLM-5.1**:
```bash
cat ~/.claude/GLM5-FILE-HANDLING-PROMPT.md
```

**Check backup registry** (what backups exist):
```bash
cat ~/.claude/file-backups.json | jq .
```

**Check audit trail** (what operations were performed):
```bash
cat ~/.claude/file-change-audit.md
```

**Restore a file from git** (if corruption detected):
```bash
cd ~/Projects/ufc-predict
git log --oneline | grep "v11.17"
git checkout <commit-SHA> -- path/to/file.json
```

---

**Setup complete. Ready for next hypothesis test with file handling discipline.**
