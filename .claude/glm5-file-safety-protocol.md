# GLM-5.1 File Safety Protocol — Backup, Audit, Verify

**Goal**: Prevent file corruption and data loss through automated backups, pre-edit confirmation, and change auditing.

**System**:
1. **Pre-edit backup** — Auto-creates backup before every Edit tool use
2. **Backup naming** — `filename.v1.20260329_120000.bak` (version + date + time)
3. **Backup registry** — `~/.claude/file-backups.json` tracks all backups
4. **Pre-edit confirmation** — Hook prompts before major edits (3+ lines, destructive)
5. **Change audit** — Logs what changed, why, and by whom

---

## Layer 1: Pre-Edit Backup Hook

**Trigger**: Before ANY Edit tool use

**Action**:
```bash
# When user tries: Edit(file_path="/path/to/file.py", ...)

# Hook intercepts and:
1. Read original file content
2. Calculate version number (from backup registry)
3. Create backup: /path/to/file.v1.20260329_120000.bak
4. Register backup in file-backups.json
5. Allow edit to proceed
```

**Naming convention**:
```
filename.v{N}.{YYYYMMDD}_{HHMMSS}.bak

Examples:
- CLAUDE.md.v1.20260329_120000.bak (first version, Mar 29 @ 12:00:00)
- api-banner.py.v2.20260329_143022.bak (second version, same day @ 14:30:22)
- settings.json.v5.20260328_093015.bak (fifth version, Mar 28 @ 09:30:15)
```

**Benefits**:
- ✓ Automatic (user doesn't have to remember)
- ✓ Versioned (keeps all prior versions)
- ✓ Timestamped (know exactly when change was made)
- ✓ Reversible (can restore any prior version)

---

## Layer 2: Backup Registry

**File**: `~/.claude/file-backups.json`

**Structure**:
```json
{
  "backups": {
    "/path/to/file1.py": {
      "versions": [
        {
          "version": 1,
          "timestamp": "2026-03-29T12:00:00Z",
          "backup_path": "/path/to/file1.py.v1.20260329_120000.bak",
          "original_size": 1024,
          "change_reason": "Initial version"
        },
        {
          "version": 2,
          "timestamp": "2026-03-29T14:30:22Z",
          "backup_path": "/path/to/file1.py.v2.20260329_143022.bak",
          "original_size": 1024,
          "change_reason": "Fixed typo in docstring"
        }
      ],
      "current_version": 2,
      "last_edited": "2026-03-29T14:30:22Z"
    }
  },
  "metadata": {
    "last_cleanup": "2026-03-29T12:00:00Z",
    "total_backups": 47,
    "total_disk_usage_mb": 12.3
  }
}
```

**Automatic actions**:
- ✓ Add entry when first edit happens
- ✓ Increment version on each edit
- ✓ Track timestamps and reasons
- ✓ Cleanup old versions (keep 5 most recent per file)

---

## Layer 3: Pre-Edit Confirmation Hook

**Trigger**: Before Edit tool use on "risky" operations

**Risky operations**:
- Deleting 3+ lines
- Replacing entire file sections
- Destructive refactors
- Changing critical files (hooks, settings.json, CLAUDE.md)

**Hook prompts**:
```
⚠️ BEFORE EDITING: Think deeply

File: ~/.claude/settings.json
Type: Critical configuration
Change: Replace 20 lines
Risk: Could break hook execution

VERIFY:
(1) Is this change necessary? [yes/no]
(2) Have I tested it? [yes/no/n/a]
(3) Can I revert if needed? [yes/no/backup created]
(4) What could go wrong? [state 1 risk]

Backup created: ~/.claude/settings.json.v1.20260329_120000.bak

Proceed? (yes/no)
```

**Critical files** (always prompt):
- `~/.claude/settings.json`
- `~/.claude/CLAUDE.md`
- `~/.claude/hooks/*.py`
- `~/.claude/anti-patterns.md`

**Non-critical files**:
- Prompt only if 10+ lines deleted
- Otherwise auto-backup and proceed

---

## Layer 4: Change Audit Log

**File**: `~/.claude/file-change-audit.md`

**Entries**:
```markdown
## Edit: settings.json — 2026-03-29 14:30

**File**: ~/.claude/settings.json (v2)
**Type**: Hook configuration
**Lines changed**: 20 (added glm5-sanity-check-prompter)
**Reason**: Added SANITY CHECK prompter to PreToolUse hooks
**Backup**: ~/.claude/settings.json.v1.20260329_143022.bak
**User approval**: Confirmed before edit
**Impact**: PreToolUse hook order changed; reality-check now first

---

## Edit: api-banner.py — 2026-03-29 12:15

**File**: ~/.claude/hooks/api-banner.py (v3)
**Type**: Hook code
**Lines changed**: 5 (added reference to planning protocol)
**Reason**: Include planning protocol suggestion in GLM-5 scaffolding
**Backup**: ~/.claude/hooks/api-banner.py.v2.20260329_121500.bak
**User approval**: Explicit (editing critical hook)
**Impact**: GLM-5 users now see planning protocol reference

...
```

**Automatically logged**:
- Timestamp of edit
- File path and version
- Number of lines changed
- Change reason (from Edit tool commit message if available)
- Backup path
- User confirmation status
- Impact assessment

---

## Layer 5: File Recovery Protocol

**If something breaks:**

```bash
# List all backups for a file
cat ~/.claude/file-backups.json | grep "api-banner.py" -A 20

# Restore a specific version
cp ~/.claude/hooks/api-banner.py.v2.20260329_121500.bak \
   ~/.claude/hooks/api-banner.py

# Or restore most recent
LATEST_BACKUP=$(ls -t ~/.claude/hooks/api-banner.py.v*.bak | head -1)
cp "$LATEST_BACKUP" ~/.claude/hooks/api-banner.py

# Verify restoration
git diff ~/.claude/hooks/api-banner.py  # Check what changed
```

---

## Layer 6: Cleanup Policy

**Auto-cleanup**:
- Keep 5 most recent backups per file
- Delete backups older than 30 days
- Remove backups for deleted files
- Log cleanup to file-backups.json

**Manual cleanup**:
```bash
# See all backups
cat ~/.claude/file-backups.json | jq '.metadata'

# Clean up old backups
python3 ~/.claude/file-backup-cleanup.py --older-than 30d --keep 5
```

---

## Implementation: glm5-file-safety.py Hook

**Runs on**: PreEdit (before Edit tool use)

**Actions**:
1. Intercept Edit request
2. Read file to backup
3. Generate backup filename (v{N}.{YYYYMMDD}_{HHMMSS}.bak)
4. Create backup
5. Register in file-backups.json
6. If risky operation: prompt for confirmation
7. Allow edit to proceed

**Pseudo-code**:
```python
def on_pre_edit(file_path, old_string, new_string):
    # 1. Check if file exists
    if not os.path.exists(file_path):
        return "error: file not found"

    # 2. Read original
    with open(file_path) as f:
        original = f.read()

    # 3. Get next version number
    version = get_next_version(file_path)

    # 4. Create backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path}.v{version}.{timestamp}.bak"
    shutil.copy(file_path, backup_name)

    # 5. Register
    register_backup(file_path, version, backup_name, original)

    # 6. Check if risky
    lines_deleted = count_lines(old_string)
    is_critical = file_path in CRITICAL_FILES

    if is_risky(lines_deleted, is_critical):
        prompt_for_confirmation(file_path, old_string, new_string)
        if not confirmed:
            return "edit cancelled by user"

    # 7. Allow edit
    return "backup created; edit allowed"
```

---

## Integration with Existing Protocols

**Fits into SANITY CHECK**:
- Assumption: "I can safely edit this file"
- Test: Backup exists? Confirmation prompted?
- Risk: File corruption; mitigation: backups + audit

**Fits into EXECUTE**:
- Rule: "Read files before editing"
- Extended: "Backup before editing; log changes"

**Fits into VERIFY**:
- Trace: "File edited and backed up to v1.20260329_120000.bak"
- Log: Change audit entry created

---

## What This Prevents

| Scenario | Prevention |
|----------|-----------|
| Accidental file corruption | Automatic backup before edit |
| Lost work | Timestamped versions (restore any version) |
| "I don't remember what changed" | Change audit log with reasons |
| Editing wrong file | Pre-edit confirmation on critical files |
| Cascade failures (broken hook breaks others) | Prompt before editing hooks/settings |
| No recovery path | Backup registry + recovery protocol |

---

## Example: Recovering from a Bad Edit

**Scenario**: Edited settings.json and broke hook execution

**Recovery steps**:
```bash
# 1. Find the backup
cat ~/.claude/file-backups.json | grep "settings.json" -A 5

# Output:
# "backup_path": "~/.claude/settings.json.v1.20260329_120000.bak",

# 2. Restore
cp ~/.claude/settings.json.v1.20260329_120000.bak \
   ~/.claude/settings.json

# 3. Verify (check what changed)
diff ~/.claude/settings.json.v1.20260329_120000.bak \
     ~/.claude/settings.json.v2.20260329_140000.bak

# 4. Continue (issue is fixed)
```

**Time to recover**: <1 minute

---

## Responsibility Checklist for GLM-5.1

Before editing any file:

- [ ] **Backup created?** (Hook does this automatically)
- [ ] **Change reason clear?** (Why am I editing this?)
- [ ] **If critical file: confirm?** (Hook prompts)
- [ ] **Impact understood?** (What could break?)
- [ ] **Recovery path exists?** (Backup + audit log)

If ANY checkbox is ❌, don't edit yet. Investigate first.

---

## Status: Beta → Ready

**Current GLM-5.1 file handling**: Write without explicit backups

**With this protocol**: Every edit is automatically backed up and logged

**Safety improvement**: From reactive (recover if broken) → proactive (prevent breakage)
