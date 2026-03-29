"""GLM-5 Protocol Audit: Post-execution quality checks.

Validates compliance with GLM-5 protocol on every Stop event:
- Response length (keep <40 lines)
- Verification (includes example trace)
- Uncertainty handling (acknowledges unknowns)

Logs violations to anti-patterns.md for pattern detection.
"""
import json
import sys
import os
from datetime import datetime

try:
    hook_input = json.load(sys.stdin)

    # Only audit GLM-5.1 responses
    transcript_path = hook_input.get("transcript_path", "")
    is_glm5 = False
    if transcript_path:
        try:
            with open(transcript_path) as f:
                lines = f.readlines()
            for line in reversed(lines):
                entry = json.loads(line)
                msg = entry.get("message", {})
                if msg.get("role") == "assistant" and "model" in msg:
                    is_glm5 = "haiku" in msg["model"].lower()
                    break
        except Exception:
            pass

    if not is_glm5:
        sys.exit(0)

    # Get last assistant message
    last_message = hook_input.get("last_assistant_message", "") or ""
    if not last_message:
        sys.exit(0)

    # Count lines (rough: split by \n)
    line_count = len(last_message.split("\n"))

    # Checks
    violations = []

    # Check 1: Under 40 lines
    if line_count > 40:
        violations.append(f"line_count={line_count}>40")

    # Check 2: Includes example or trace
    has_trace = (
        "example" in last_message.lower() or
        "trace" in last_message.lower() or
        "test" in last_message.lower() or
        "verify" in last_message.lower()
    )
    if not has_trace and "VERIFY" not in last_message:
        violations.append("no_verification_trace")

    # Check 3: Uncertainty acknowledged
    has_uncertainty_handling = (
        "uncertain" in last_message.lower() or
        "unknown" in last_message.lower() or
        "need to" in last_message.lower() or
        "?" in last_message
    )
    if not has_uncertainty_handling and "?" not in last_message:
        violations.append("no_uncertainty_flag")

    # Log violations to anti-patterns.md
    if violations:
        anti_patterns_path = os.path.expanduser("~/.claude/anti-patterns.md")
        try:
            with open(anti_patterns_path, "a") as f:
                f.write(f"\n[{datetime.now().isoformat()}] GLM-5 violations: {', '.join(violations)}\n")
        except Exception:
            pass

except Exception as e:
    pass
