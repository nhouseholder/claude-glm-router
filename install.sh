#!/bin/bash
set -e

echo "=== Claude Code GLM Router — Install ==="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROXY_DEST="$HOME/.claude/scripts/model-router-proxy.py"
BANNER_DEST="$HOME/.claude/hooks/api-banner.py"
PLIST_DEST="$HOME/Library/LaunchAgents/com.claude.model-router.plist"
SETTINGS="$HOME/.claude/settings.json"

# --- Check for Z AI API key ---
if [ -z "$ZAI_API_KEY" ]; then
    echo "Enter your Z AI API key (or press Enter to set it later):"
    read -r ZAI_API_KEY
fi

# --- Copy proxy script ---
mkdir -p "$HOME/.claude/scripts"
cp "$SCRIPT_DIR/src/model-router-proxy.py" "$PROXY_DEST"
echo "[1/5] Proxy script installed → $PROXY_DEST"

# --- Copy banner hook ---
mkdir -p "$HOME/.claude/hooks"
cp "$SCRIPT_DIR/src/api-banner.py" "$BANNER_DEST"
echo "[2/5] Banner hook installed → $BANNER_DEST"

# --- Install LaunchAgent ---
# Stop existing proxy if running
launchctl unload "$PLIST_DEST" 2>/dev/null || true
pkill -f model-router-proxy 2>/dev/null || true
sleep 1

# Write plist with correct path
sed "s|PROXY_PATH_PLACEHOLDER|$PROXY_DEST|g" "$SCRIPT_DIR/config/com.claude.model-router.plist" > "$PLIST_DEST"
launchctl load "$PLIST_DEST"
echo "[3/5] LaunchAgent installed → auto-starts on login"

# --- Update settings.json ---
if [ -f "$SETTINGS" ]; then
    python3 << PYEOF
import json

path = "$SETTINGS"
with open(path) as f:
    s = json.load(f)

# Add proxy URL
s.setdefault("env", {})
s["env"]["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:17532"

# Add Z AI key if provided
zai_key = "$ZAI_API_KEY"
if zai_key:
    s["env"]["Z_AI_API_KEY"] = zai_key

# Add SessionStart banner hook (if not already present)
s.setdefault("hooks", {})
banner_cmd = "python3 ~/.claude/hooks/api-banner.py"
banner_entry = {"hooks": [{"type": "command", "command": banner_cmd}]}

if "SessionStart" not in s["hooks"]:
    s["hooks"]["SessionStart"] = [banner_entry]

# Add UserPromptSubmit banner hook (if not already present)
if "UserPromptSubmit" not in s["hooks"]:
    s["hooks"]["UserPromptSubmit"] = [banner_entry]
else:
    # Check if banner hook already exists
    existing = s["hooks"]["UserPromptSubmit"]
    has_banner = any(
        any(h.get("command", "") == banner_cmd for h in entry.get("hooks", []))
        for entry in existing
    )
    if not has_banner:
        s["hooks"]["UserPromptSubmit"].insert(0, banner_entry)

with open(path, "w") as f:
    json.dump(s, f, indent=2)

print("[4/5] settings.json updated")
PYEOF
else
    echo "[4/5] No settings.json found — create one or configure manually"
fi

# --- Verify ---
sleep 3
echo ""
if curl -s http://127.0.0.1:17532/health | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'[5/5] Proxy v{d[\"version\"]} running on port {d[\"port\"]}')"; then
    echo ""
    echo "=== Install complete ==="
    echo ""
    echo "Restart Claude Code (Cmd+Q, reopen) to activate."
    echo ""
    echo "Usage:"
    echo "  Haiku 4.5 in picker  →  routes to Z AI (GLM-5)"
    echo "  Opus/Sonnet in picker →  routes to Anthropic"
    echo ""
    if [ -z "$ZAI_API_KEY" ]; then
        echo "⚠️  Don't forget to set your Z AI API key:"
        echo "   export ZAI_API_KEY='your-key-here'"
        echo "   Or add it to ~/.claude/settings.json env block"
    fi
else
    echo "[5/5] ⚠️  Proxy did not start. Check /tmp/proxy.log"
fi
