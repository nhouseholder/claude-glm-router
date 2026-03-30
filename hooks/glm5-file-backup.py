#!/usr/bin/env python3
"""GLM-5.1 File Backup Hook — Auto-backup before edits, prevent data loss.

Runs on PreEdit to:
1. Create timestamped backup before every edit
2. Register backup in file-backups.json
3. Prompt for confirmation on risky edits
4. Log changes to audit trail

Backup naming: filename.v{N}.{YYYYMMDD}_{HHMMSS}.bak
"""
import json
import sys
import os
import shutil
from datetime import datetime

BACKUP_REGISTRY = os.path.expanduser("~/.claude/file-backups.json")
AUDIT_LOG = os.path.expanduser("~/.claude/file-change-audit.md")
CRITICAL_FILES = {
    "~/.claude/settings.json",
    "~/.claude/CLAUDE.md",
    "~/.claude/hooks/",
    "~/.claude/anti-patterns.md",
}

def load_backup_registry():
    """Load existing backup registry."""
    if os.path.exists(BACKUP_REGISTRY):
        with open(BACKUP_REGISTRY) as f:
            return json.load(f)
    return {"backups": {}, "metadata": {"total_backups": 0}}

def save_backup_registry(registry):
    """Save backup registry."""
    os.makedirs(os.path.dirname(BACKUP_REGISTRY), exist_ok=True)
    with open(BACKUP_REGISTRY, 'w') as f:
        json.dump(registry, f, indent=2)

def get_next_version(file_path):
    """Get next version number for file."""
    registry = load_backup_registry()
    if file_path not in registry["backups"]:
        return 1
    return registry["backups"][file_path].get("current_version", 0) + 1

def is_critical_file(file_path):
    """Check if file is critical (requires confirmation)."""
    expanded_path = os.path.expanduser(file_path)
    for critical in CRITICAL_FILES:
        critical_expanded = os.path.expanduser(critical)
        if critical_expanded in expanded_path or expanded_path in critical_expanded:
            return True
    return False

def is_risky_edit(old_string, new_string, is_critical):
    """Check if edit is risky (requires confirmation)."""
    if is_critical:
        return True

    # Large deletions (3+ lines)
    old_lines = len(old_string.split('\n'))
    if old_lines >= 3:
        return True

    # Total change is large
    if len(old_string) > 500:
        return True

    return False

def create_backup(file_path):
    """Create timestamped backup of file."""
    try:
        # Generate backup name
        version = get_next_version(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.v{version}.{timestamp}.bak"

        # Create backup
        shutil.copy(file_path, backup_path)

        # Register backup
        registry = load_backup_registry()

        if file_path not in registry["backups"]:
            registry["backups"][file_path] = {"versions": []}

        file_record = registry["backups"][file_path]
        file_record["versions"].append({
            "version": version,
            "timestamp": datetime.now().isoformat() + "Z",
            "backup_path": backup_path,
            "original_size": os.path.getsize(file_path),
        })
        file_record["current_version"] = version
        file_record["last_edited"] = datetime.now().isoformat() + "Z"

        registry["metadata"]["total_backups"] = registry["metadata"].get("total_backups", 0) + 1

        save_backup_registry(registry)

        return backup_path

    except Exception as e:
        return None

def log_edit(file_path, backup_path, version, lines_changed):
    """Log edit to audit trail."""
    try:
        entry = f"""
## Edit: {os.path.basename(file_path)} — {datetime.now().strftime("%Y-%m-%d %H:%M")}

**File**: {file_path} (v{version})
**Timestamp**: {datetime.now().isoformat()}Z
**Lines changed**: {lines_changed}
**Backup**: {backup_path}

---
"""
        with open(AUDIT_LOG, 'a') as f:
            f.write(entry)

    except Exception:
        pass  # Fail silently

def prompt_confirmation(file_path, old_string, new_string):
    """Output confirmation prompt."""
    is_critical = is_critical_file(file_path)
    lines_deleted = len(old_string.split('\n'))

    risk_level = "CRITICAL" if is_critical else "RISKY"

    prompt = f"""
⚠️  PRE-EDIT CONFIRMATION

File: {file_path}
Type: {"Critical configuration" if is_critical else "Important file"}
Risk level: {risk_level}
Lines affected: {lines_deleted}

BEFORE PROCEEDING, verify:
(1) Is this change necessary?
(2) Have I tested the alternative approaches?
(3) Do I understand what could break?
(4) Is a backup created? (Yes — hook created it automatically)

Backup created: {os.path.basename(file_path)}.v*.bak

If you want to cancel, stop now.
Proceeding with edit...
"""
    print(prompt)

# Hook entry point
try:
    hook_input = json.load(sys.stdin)
    event = hook_input.get("hook_event_name", "")

    # Support PreToolUse (Edit matcher) since PreEdit hook type doesn't exist
    if event == "PreToolUse":
        tool_name = hook_input.get("tool_name", "")
        if tool_name != "Edit":
            sys.exit(0)
        tool_input = hook_input.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
    elif event == "PreEdit":
        # Future support if PreEdit hook type becomes available
        file_path = hook_input.get("file_path", "")
        old_string = hook_input.get("old_string", "")
        new_string = hook_input.get("new_string", "")
    else:
        sys.exit(0)

    if not file_path or not os.path.exists(file_path):
        sys.exit(0)

    # Create backup
    backup_path = create_backup(file_path)
    if not backup_path:
        print("⚠️  Warning: Could not create backup. Proceeding with caution.")
        sys.exit(0)

    # Log backup creation
    lines_changed = len(old_string.split('\n'))
    log_edit(file_path, backup_path, get_next_version(file_path), lines_changed)

    # Check if risky
    is_critical = is_critical_file(file_path)
    if is_risky_edit(old_string, new_string, is_critical):
        prompt_confirmation(file_path, old_string, new_string)

except Exception as e:
    # Fail silently; don't block edits
    pass

sys.exit(0)
