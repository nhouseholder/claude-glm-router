"""Shared model detection for GLM hooks. Import with: from detect_model import detect_model"""
import os
import json
import urllib.request


def detect_model():
    """Detect current model from CLAUDE_MODEL env var.

    CLAUDE_MODEL is the ONLY reliable source. The proxy's /last-route is stale
    (reflects last API call, not current picker). When unknown, default to 'opus'
    so we never accidentally inject GLM-5 scaffolding into an Opus session.
    """
    model = os.environ.get("CLAUDE_MODEL", "")
    if not model:
        # Unknown model = assume Anthropic (safe default).
        # A missing green emoji is harmless; a false green emoji is confusing.
        return "opus"
    return model.lower()


def is_glm5():
    """Return True if currently running on GLM-5 (Haiku picker)."""
    return "haiku" in detect_model()
