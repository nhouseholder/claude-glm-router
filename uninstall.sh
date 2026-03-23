#!/bin/bash
set -e

echo "=== Claude Code GLM Router — Uninstall ==="
echo ""

PLIST="$HOME/Library/LaunchAgents/com.claude.model-router.plist"
SETTINGS="$HOME/.claude/settings.json"

# Stop the proxy
launchctl unload "$PLIST" 2>/dev/null || true
pkill -f model-router-proxy 2>/dev/null || true
echo "[1/3] Proxy stopped"

# Remove ANTHROPIC_BASE_URL from settings
if [ -f "$SETTINGS" ]; then
    python3 << PYEOF
import json

path = "$SETTINGS"
with open(path) as f:
    s = json.load(f)

removed = []
if "ANTHROPIC_BASE_URL" in s.get("env", {}):
    del s["env"]["ANTHROPIC_BASE_URL"]
    removed.append("ANTHROPIC_BASE_URL")

with open(path, "w") as f:
    json.dump(s, f, indent=2)

if removed:
    print(f"[2/3] Removed {', '.join(removed)} from settings.json")
else:
    print("[2/3] settings.json already clean")
PYEOF
else
    echo "[2/3] No settings.json found"
fi

# Remove installed files
rm -f "$PLIST"
rm -f "$HOME/.claude/scripts/model-router-proxy.py"
rm -f "$HOME/.claude/hooks/api-banner.py"
echo "[3/3] Removed proxy, banner hook, and LaunchAgent"

echo ""
echo "=== Uninstall complete ==="
echo "Restart Claude Code (Cmd+Q, reopen) to go back to direct Anthropic."
echo ""
echo "Note: Your Z AI API key and banner hook entries in settings.json were"
echo "left in place (harmless without the proxy). Remove manually if desired."
