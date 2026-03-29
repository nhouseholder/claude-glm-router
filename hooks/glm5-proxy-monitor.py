"""GLM-5 Proxy Health Monitor: Check Z AI connectivity, log health status.

Runs periodically (via SessionStart to initialize, then user can run via loop).
Checks proxy health every check, logs to ~/.claude/proxy-health.log.

If proxy is unhealthy, logs alert (user should check /tmp/proxy.log).
"""
import json
import urllib.request
import os
from datetime import datetime

health_log = os.path.expanduser("~/.claude/proxy-health.log")

try:
    # Query proxy health
    resp = urllib.request.urlopen("http://127.0.0.1:17532/health", timeout=2)
    health = json.loads(resp.read())

    status = health.get("status", "unknown")
    version = health.get("version", "?")
    uptime = health.get("uptime_seconds", 0)
    last_route = health.get("last_route", {})
    routing = health.get("routing", {})

    # Log to file
    with open(health_log, "a") as f:
        ts = datetime.now().isoformat()
        f.write(f"[{ts}] proxy_status={status} v{version} uptime={uptime}s\n")
        if status == "ok":
            f.write(f"  routing: {routing}\n")
            f.write(f"  last_route: {last_route}\n")
        else:
            f.write(f"  ⚠️ ALERT: Proxy unhealthy. Check /tmp/proxy.log\n")

except Exception as e:
    with open(health_log, "a") as f:
        ts = datetime.now().isoformat()
        f.write(f"[{ts}] ❌ ALERT: Proxy unreachable — {str(e)}\n")

