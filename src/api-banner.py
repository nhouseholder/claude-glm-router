#!/usr/bin/env python3
"""API routing banner + GLM-5 reasoning scaffolding.

🟠 = Anthropic (Opus/Sonnet), 🟢 = Z AI (GLM-5).

On UserPromptSubmit:
  - Always injects icon prefix instruction
  - When Haiku/GLM-5: also injects reasoning scaffolding (replaces glm5-boost skill)
  - When Opus/Sonnet: no scaffolding (native intelligence sufficient)

On SessionStart:
  - Shows API status banner with proxy health
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detect_model import detect_model

# GLM-5 reasoning scaffolding — injected ONLY when Haiku is active.
# This replaces the glm5-boost skill with zero-cost dynamic injection.
GLM5_SCAFFOLDING = """
[GLM-5 MODE] CORE RULES (enforced by hooks):
• PLAN — State your approach in 1 line before using tools (validator enforces this)
• VERIFY — Include example trace. Keep <40 lines (auditor checks this)
• SANITY CHECK — Before executing: (1) Verify correct project/file. (2) Identify 3 assumptions. (3) Test them. (4) What could go wrong?
• MATH/BETTING — profit = stake × (odds/100) for +odds, stake × (100/|odds|) for -odds. Losses = -1u. Never flat +1u.

EXTENDED PROTOCOL:
1. ORIENT — Read handoff. If continuing work: git diff --stat to see changes. Don't redo.
2. PLAN — State approach in 1 line before acting.
3. EXECUTE — Read files before editing. One change per tool call. Use tools for facts, never generate.
4. VERIFY — Answer the question? Trace one example. Keep <40 lines.
5. MULTI-FILE — Note key fact from each file before next.
6. Uncertain? Ask."""



try:
    hook_input = json.load(sys.stdin)
    event = hook_input.get("hook_event_name", "")

    model_lower = detect_model(hook_input.get("transcript_path"))

    if "haiku" in model_lower:
        icon = "🟢"
        label = "GLM-5"
        is_glm5 = True
    elif "opus" in model_lower:
        icon = "🟠"
        label = "Opus"
        is_glm5 = False
    elif "sonnet" in model_lower:
        icon = "🟠"
        label = "Sonnet"
        is_glm5 = False
    else:
        icon = "🟠"
        label = "Claude"
        is_glm5 = False

    # UserPromptSubmit: only inject for GLM-5 (Haiku). Opus/Sonnet don't need scaffolding.
    if event == "UserPromptSubmit":
        if is_glm5:
            context = f'Place exactly "{icon}" as the very first character of your FIRST message only. Do NOT repeat the emoji mid-response, after tool calls, or when subagent results return. One emoji total, at the very start. You are running on {label}.'
            context += GLM5_SCAFFOLDING
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": context
                }
            }))
        else:
            # Opus/Sonnet: emit minimal icon instruction only — no scaffolding overhead
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": f'Begin your response with exactly "{icon}" (the single emoji, nothing else before it). This indicates you are running on {label}.'
                }
            }))

    # SessionStart: show info banner with proxy status
    elif event == "SessionStart":
        if is_glm5:
            banner = f"{icon} Z AI API ACTIVE (GLM-5) — Anthropic limits bypassed"
        else:
            banner = f"{icon} Anthropic API ACTIVE — Claude {label}"
        try:
            resp = urllib.request.urlopen("http://127.0.0.1:17532/health", timeout=1)
            health = json.loads(resp.read())
            v = health.get("version", "?")
            up = health.get("uptime_seconds", 0)
            h, m = divmod(up // 60, 60)
            uptime_str = f"{h}h{m}m" if h else f"{m}m"
            banner += f"  |  Proxy v{v} up {uptime_str}"
        except Exception:
            banner += "  |  Proxy not running"

        # For GLM-5 sessions, also inject scaffolding at session level
        if is_glm5:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": GLM5_SCAFFOLDING
                }
            }))
        print(json.dumps({"type": "info", "message": banner}))

    else:
        print(json.dumps({"type": "info", "message": f"{icon} {label}"}))

except Exception:
    pass
