"""Shared model detection for GLM hooks. Import with: from detect_model import detect_model"""
import os
import json
import urllib.request


def detect_model(transcript_path=None):
    """Detect current model. Smart detection handles model switches mid-session.
    Priority: CLAUDE_MODEL env var → settings.json (authoritative) → transcript (fallback) → 'opus'.
    """
    # 1. Env var (set by some Claude Code versions)
    model = os.environ.get("CLAUDE_MODEL", "")
    if model:
        return model.lower()

    # 2. settings.json (authoritative — updated by /model command, reflects startup model)
    settings_model = None
    try:
        settings_path = os.path.expanduser("~/.claude/settings.json")
        with open(settings_path) as f:
            settings = json.load(f)
        settings_model = settings.get("model", "").lower()
        if settings_model:
            # If settings shows haiku/sonnet/opus, trust it (user just switched)
            if any(x in settings_model for x in ["haiku", "sonnet", "opus"]):
                return settings_model
    except Exception:
        pass

    # 3. Transcript — last assistant message (one-turn stale but usually correct)
    if transcript_path:
        try:
            with open(transcript_path) as f:
                lines = f.readlines()
            if lines:  # Only trust transcript if it has content
                for line in reversed(lines):
                    entry = json.loads(line)
                    msg = entry.get("message", {})
                    if msg.get("role") == "assistant" and "model" in msg:
                        return msg["model"].lower()
        except Exception:
            pass

    # 4. Fallback to settings.json if no transcript
    if settings_model:
        return settings_model

    # 5. Unknown = assume Anthropic (safe default).
    return "opus"


def is_glm5():
    """Return True if currently running on GLM-5 (Haiku picker)."""
    return "haiku" in detect_model()
