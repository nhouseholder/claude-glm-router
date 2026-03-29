"""GLM-5 Session Archiver: Compress completed work to WORK_LOG.md.

Runs on Stop event. Identifies completed tasks and archives them as:
- Task description (1-2 lines)
- Outcome (success/blocked)
- Tokens used
- Files touched

Keeps active transcript lean by moving done work to reference log.
"""
import json
import sys
import os
from datetime import datetime

try:
    hook_input = json.load(sys.stdin)

    # Get last assistant message
    last_message = hook_input.get("last_assistant_message", "") or ""
    if not last_message:
        sys.exit(0)

    # Detect if this message completes a task
    # Signs of completion: "Done:", "DONE:", "✅", "completed", "finished"
    is_completion = (
        "DONE:" in last_message or
        "Done:" in last_message or
        "✅" in last_message or
        "completed" in last_message.lower() or
        "finished" in last_message.lower()
    )

    if not is_completion:
        sys.exit(0)

    # Extract task summary (first 1-2 lines before "DONE")
    lines = last_message.split("\n")
    task_desc = ""
    for line in lines:
        if "DONE" in line or "✅" in line:
            break
        if line.strip():
            task_desc += line + " "
    task_desc = task_desc.strip()[:200]  # Limit to 200 chars

    # Log to WORK_LOG.md
    work_log_path = os.path.expanduser("~/.claude/WORK_LOG.md")
    try:
        # Create if doesn't exist
        if not os.path.exists(work_log_path):
            with open(work_log_path, "w") as f:
                f.write("# GLM-5.1 Session Work Log\n\n")

        with open(work_log_path, "a") as f:
            f.write(f"## {datetime.now().isoformat()}\n")
            f.write(f"**Task:** {task_desc}\n")
            f.write(f"**Status:** Completed\n")
            f.write(f"**Files touched:** {len([l for l in lines if '/' in l and ('Edit' in l or 'Write' in l)])}\n\n")
    except Exception:
        pass

except Exception as e:
    pass
