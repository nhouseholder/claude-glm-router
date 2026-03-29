"""Shared model detection for GLM hooks. Import with: from detect_model import detect_model"""
import os
import json
import urllib.request


def detect_model(transcript_path=None):
    """Detect current model. Prioritizes transcript (actual usage) over settings (stale on mid-session switches).
    Priority: CLAUDE_MODEL env var → transcript (recent) → settings.json (fallback) → 'opus'.
    """
    # 1. Env var (set by some Claude Code versions)
    model = os.environ.get("CLAUDE_MODEL", "")
    if model:
        return model.lower()

    # 2. Transcript — FIRST if it has content (reflects actual last model used, catches mid-session switches)
    if transcript_path:
        try:
            with open(transcript_path) as f:
                lines = f.readlines()
            if lines:  # If transcript has content, trust it over settings.json
                for line in reversed(lines):
                    entry = json.loads(line)
                    msg = entry.get("message", {})
                    if msg.get("role") == "assistant" and "model" in msg:
                        return msg["model"].lower()
        except Exception:
            pass

    # 3. settings.json — only if transcript is empty/new session
    try:
        settings_path = os.path.expanduser("~/.claude/settings.json")
        with open(settings_path) as f:
            settings = json.load(f)
        model = settings.get("model", "").lower()
        if model:
            return model
    except Exception:
        pass

    # 4. Unknown = assume Anthropic (safe default).
    return "opus"


def is_glm5():
    """Return True if currently running on GLM-5 (Haiku picker)."""
    return "haiku" in detect_model()
