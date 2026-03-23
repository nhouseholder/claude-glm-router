#!/usr/bin/env python3
"""API routing banner — shows active backend on session start and every prompt.
Queries the proxy for actual routing state, falls back to CLAUDE_MODEL env var."""
import json
import sys
import os
import urllib.request

try:
    hook_input = json.load(sys.stdin)
    event = hook_input.get("hook_event_name", "")

    # Determine model from the best available source
    backend = None
    model_name = None

    # Source 1: Query the proxy for actual last-routed model
    try:
        resp = urllib.request.urlopen("http://127.0.0.1:17532/last-route", timeout=1)
        data = json.loads(resp.read())
        ts = data.get("timestamp", 0)
        # Only trust proxy data if it's recent (within last 5 minutes)
        # On SessionStart there's no prior request, so timestamp will be 0 or stale
        import time
        if ts > 0 and (time.time() - ts) < 300:
            backend = data.get("backend", "")
            model_name = data.get("model", "")
    except Exception:
        pass

    # Source 2: Fall back to CLAUDE_MODEL env var (always available)
    if not backend:
        model = os.environ.get("CLAUDE_MODEL", "")
        if "haiku" in model.lower():
            backend = "Z AI (GLM-5)"
            model_name = model
        elif "opus" in model.lower():
            backend = "Anthropic"
            model_name = model
        elif "sonnet" in model.lower():
            backend = "Anthropic"
            model_name = model
        else:
            # Source 3: Check proxy health to confirm it's running
            try:
                resp = urllib.request.urlopen("http://127.0.0.1:17532/health", timeout=1)
                health = json.loads(resp.read())
                if health.get("status") == "ok":
                    backend = "Anthropic"
                    model_name = model or "unknown"
                else:
                    backend = "unknown"
                    model_name = model or "unknown"
            except Exception:
                backend = "direct (proxy offline)"
                model_name = model or "unknown"

    # Build banner
    if "Z AI" in backend or "GLM" in backend:
        banner = "🟢 Z AI API ACTIVE (GLM-5) — Anthropic rate limits BYPASSED"
    elif "Anthropic" in backend:
        short = "Opus" if "opus" in model_name.lower() else "Sonnet" if "sonnet" in model_name.lower() else "Haiku" if "haiku" in model_name.lower() else model_name
        banner = f"🔵 Anthropic API ACTIVE — Claude {short}"
    elif "proxy offline" in backend:
        banner = "⚠️ Proxy offline — requests going direct to Anthropic"
    else:
        banner = f"⚪ Model: {model_name}"

    # On SessionStart, also show proxy status
    if event == "SessionStart":
        try:
            resp = urllib.request.urlopen("http://127.0.0.1:17532/health", timeout=1)
            health = json.loads(resp.read())
            v = health.get("version", "?")
            up = health.get("uptime_seconds", 0)
            h, m = divmod(up // 60, 60)
            uptime_str = f"{h}h{m}m" if h else f"{m}m"
            banner += f"  |  Proxy v{v} up {uptime_str}"
        except Exception:
            banner += "  |  ⚠️ Proxy not running"

    print(json.dumps({"type": "info", "message": banner}))

except Exception:
    pass
