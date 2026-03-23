# Claude Code GLM Router

A local proxy that lets you seamlessly switch between **Anthropic (Opus/Sonnet)** and **Z AI (GLM-5)** inside Claude Code — without restarting, without losing context.

When you hit Anthropic rate limits, switch to Haiku in the model picker. The proxy intercepts the request and routes it to Z AI's GLM-5 instead. Switch back to Opus/Sonnet when limits reset. Zero interruption, full conversation context preserved.

## How It Works

```
Claude Code Desktop App
        │
        ▼
  ┌─────────────┐
  │  Local Proxy │  ← http://127.0.0.1:17532
  │  (port 17532)│
  └──────┬──────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
 Anthropic   Z AI
 (Opus/      (GLM-5)
  Sonnet)
```

| Model Picker Selection | Routes To | API Key |
|---|---|---|
| **Haiku 4.5** | Z AI → GLM-5 | Your Z AI API key |
| **Sonnet 4.6** | Anthropic | Your Pro subscription |
| **Opus 4.6** | Anthropic | Your Pro subscription |

### What the proxy does

1. Claude Code reads `ANTHROPIC_BASE_URL=http://127.0.0.1:17532` from settings
2. All API calls hit the local proxy instead of Anthropic directly
3. Proxy inspects the `model` field:
   - `claude-haiku-*` → rewrites to `glm-5`, forwards to Z AI
   - anything else → forwards to Anthropic with all auth headers intact
4. **Thinking block stripping** — removes `thinking` and `redacted_thinking` blocks from conversation history before forwarding. This is what makes seamless Opus↔Haiku switching possible (without it, signature errors break the session)
5. **Port conflict protection** — if a second instance starts, it detects port 17532 is in use and exits cleanly

### What's preserved when switching models

- All conversation text (both directions)
- Tool use and tool results
- System prompts and skills
- Full message history

### What's intentionally stripped

- Thinking blocks (Opus internal reasoning — invisible to you, causes signature errors on model switch)
- Z AI-unsupported fields (`betas`, `anthropic_beta`, `metadata.thinking`)

## Installation

### Prerequisites

- macOS (uses LaunchAgent for auto-start)
- Python 3.9+
- Claude Code Desktop App
- A [Z AI](https://z.ai) API key

### Quick Install

```bash
git clone https://github.com/nhouseholder/claude-glm-router.git
cd claude-glm-router
./install.sh
```

The install script will:
1. Copy the proxy to `~/.claude/scripts/`
2. Copy the banner hook to `~/.claude/hooks/`
3. Install the LaunchAgent (auto-starts on login)
4. Add `ANTHROPIC_BASE_URL` to your Claude Code settings
5. Start the proxy
6. Verify everything is working

### Manual Install

If you prefer to set things up yourself:

```bash
# 1. Copy the proxy script
mkdir -p ~/.claude/scripts
cp src/model-router-proxy.py ~/.claude/scripts/

# 2. Copy the banner hook
mkdir -p ~/.claude/hooks
cp src/api-banner.py ~/.claude/hooks/

# 3. Install the LaunchAgent
cp config/com.claude.model-router.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.claude.model-router.plist

# 4. Add to your ~/.claude/settings.json:
#    "env": { "ANTHROPIC_BASE_URL": "http://127.0.0.1:17532" }
#    "hooks": { "SessionStart": [{"hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/api-banner.py"}]}] }

# 5. Set your Z AI API key (either env var or edit the proxy script)
export ZAI_API_KEY="your-key-here"
```

## Configuration

### Z AI API Key

Set your key in one of these places (checked in order):

1. **Environment variable:** `ZAI_API_KEY` (recommended)
2. **Claude Code settings.json:** Add `"Z_AI_API_KEY": "your-key"` to the `env` block
3. **Proxy script:** Edit the fallback value in `model-router-proxy.py` (least recommended)

### Banner Hook

The banner hook shows which backend is active:

- `🟢 Z AI API ACTIVE (GLM-5)` — requests going to Z AI
- `🔵 Anthropic API ACTIVE — Claude Opus` — requests going to Anthropic
- `⚠️ Proxy offline` — proxy not running, requests going direct

It fires on:
- **Session start** — automatic, no user action needed
- **Every prompt** — updates if you switched models

To enable the banner, add these hooks to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/api-banner.py" }]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/api-banner.py" }]
      }
    ]
  }
}
```

## Usage

### Switching to GLM-5 (when you hit rate limits)

1. Click the model picker (bottom right of Claude Code)
2. Select **Haiku 4.5**
3. Banner shows: `🟢 Z AI API ACTIVE (GLM-5) — Anthropic rate limits BYPASSED`
4. Keep working — full conversation context preserved

### Switching back to Anthropic

1. Click the model picker
2. Select **Opus 4.6** or **Sonnet 4.6**
3. Banner shows: `🔵 Anthropic API ACTIVE — Claude Opus`
4. Keep working — same session, same context

### Verifying the proxy

```bash
curl -s http://127.0.0.1:17532/health | python3 -m json.tool
```

Expected:
```json
{
  "status": "ok",
  "version": 6,
  "port": 17532,
  "routing": {
    "haiku": "Z AI (GLM-5)",
    "opus": "Anthropic",
    "sonnet": "Anthropic"
  },
  "thinking_strip": "enabled",
  "uptime_seconds": 3600
}
```

### Watching proxy logs

```bash
tail -f /tmp/proxy.log
```

## Troubleshooting

### Claude Code freezes / "Shimmying" with no response

**Cause:** Proxy is dead but `ANTHROPIC_BASE_URL` is still in settings.json.

**Fix:**
```bash
# Remove the proxy URL from settings
python3 -c "
import json
path = '$HOME/.claude/settings.json'
with open(path) as f: s = json.load(f)
s['env'].pop('ANTHROPIC_BASE_URL', None)
with open(path, 'w') as f: json.dump(s, f, indent=2)
print('Fixed — restart Claude Code')
"
```
Then Cmd+Q and reopen Claude Code.

### Port 17532 already in use

```bash
lsof -ti :17532 | xargs kill -9
sleep 2
launchctl unload ~/Library/LaunchAgents/com.claude.model-router.plist
launchctl load ~/Library/LaunchAgents/com.claude.model-router.plist
```

### "Invalid signature in thinking block" error

Start a **new session** in Claude Code. The proxy prevents this going forward, but existing corrupted sessions can't be recovered.

### Opus/Sonnet returns login or auth error

Your Pro subscription session token expired. Cmd+Q and reopen Claude Code — it re-authenticates automatically.

### Nuclear reset (removes all proxy, restores vanilla Claude Code)

```bash
./uninstall.sh
```

Or manually:
```bash
python3 -c "
import json, subprocess
path = '$HOME/.claude/settings.json'
with open(path) as f: s = json.load(f)
s['env'].pop('ANTHROPIC_BASE_URL', None)
with open(path, 'w') as f: json.dump(s, f, indent=2)
subprocess.run(['launchctl', 'unload', '$HOME/Library/LaunchAgents/com.claude.model-router.plist'], capture_output=True)
subprocess.run(['pkill', '-f', 'model-router-proxy'], capture_output=True)
print('Reset complete — restart Claude Code')
"
```

## Known Limitations

- **GLM-5 may hallucinate tool output** — GLM-5 sometimes generates fake bash results instead of running commands. For critical commands, verify in Terminal.
- **GLM-5 identifies as Haiku** — Claude Code's system prompt tells it it's Haiku 4.5. The 🟢 banner is the reliable indicator.
- **Model picker label** — Can't rename "Haiku 4.5" in the UI (hardcoded in the binary). You just have to know Haiku = GLM-5.
- **Rate limit tip** — Don't use `claude-opus-4-6[1m]`. The `[1m]` modifier sends up to 1M tokens per request, which burns through per-minute burst limits instantly even at 2% quota usage.

## File Structure

```
claude-glm-router/
├── README.md
├── install.sh              # One-command setup
├── uninstall.sh            # Clean removal
├── src/
│   ├── model-router-proxy.py   # The proxy server (v6)
│   └── api-banner.py           # Session banner hook
└── config/
    └── com.claude.model-router.plist  # macOS LaunchAgent
```

## License

MIT
