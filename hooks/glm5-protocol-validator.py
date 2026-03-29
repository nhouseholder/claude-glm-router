"""GLM-5 Protocol Enforcement: Requires explicit PLAN before tool execution.

Prevents tool use without stating approach first. Enforces:
- All tool calls must be preceded by a PLAN statement
- PLAN must be on current turn (not inherited from history)
"""
import json
import sys

try:
    hook_input = json.load(sys.stdin)

    # Only enforce on GLM-5 (Haiku)
    # Check if this is Haiku by reading from transcript
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
        sys.exit(0)  # Only enforce on GLM-5

    # Get the current user message
    user_message = hook_input.get("user_message", "") or hook_input.get("prompt", "")

    # Check if this message contains a PLAN statement
    has_plan = "PLAN:" in user_message or "plan:" in user_message.lower()

    # If no PLAN and they're about to use a tool, block it
    if not has_plan and hook_input.get("tool_name"):
        print(json.dumps({
            "type": "error",
            "message": "GLM-5 Protocol: State your PLAN before using tools. Example: 'PLAN: Read the file first to understand the structure, then edit line 42.'"
        }))
        sys.exit(1)

except Exception as e:
    pass
