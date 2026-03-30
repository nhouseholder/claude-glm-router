# GLM-5.1 Hallucination Prevention — Reality-Check System

**Problem**: GLM-5.1 fabricated fake AI models (Claude 4.6, Gemini 3.2 Pro, DeepSeek V4, etc.) when asked to pull data from web sources, then wrote them to database.

**Root cause**: No validation before database writes. When web scraping returned incomplete data, GLM-5.1 invented missing entries instead of failing + asking user.

**Solution**: Multi-layer prevention system that validates facts before acting.

---

## Layer 1: Reality-Check Hook (PreToolUse)

**Goal**: Before ANY write to external store (database, file, API), verify the data is real.

**When to trigger**:
- User asks to pull data from web
- About to insert into database
- Writing model/API/pricing data

**Validation logic**:

```python
# glm5-reality-check.py (new hook)

def validate_before_write(action, data):
    """
    Before writing data to external store, verify it's real.

    Covers:
    - AI model names
    - Pricing information
    - API endpoints
    - Feature claims
    """

    if action == "database_write" and data.get("type") == "model":
        model = data.get("model_name")

        # Check 1: Model name against canonical list
        KNOWN_MODELS = {
            "Claude": ["Opus 4.6", "Sonnet 4.6", "Haiku 4.5"],
            "Anthropic": ["Claude Opus 4.6", "Claude Sonnet 4.6", "Claude Haiku 4.5"],
            "OpenAI": ["GPT-4o", "GPT-4 Turbo", "GPT-3.5 Turbo"],
            "Google": ["Gemini 2.0", "Gemini 1.5", "Gemini 1.0"],
            "DeepSeek": ["DeepSeek V3", "DeepSeek V2.5"],  # NOT V4
            "Z AI": ["GLM-5.1", "GLM-5", "GLM-4"],
        }

        # Check if model exists in canonical list
        model_found = False
        for brand, versions in KNOWN_MODELS.items():
            if any(version.lower() in model.lower() for version in versions):
                model_found = True
                break

        if not model_found:
            return {
                "valid": False,
                "reason": f"Model '{model}' not in canonical list. Hallucination risk.",
                "action": "BLOCK_WRITE",
                "suggest": "Verify this model exists in official sources before proceeding"
            }

        # Check 2: Pricing sanity
        if data.get("input_price") and data.get("output_price"):
            inp = float(data["input_price"])
            out = float(data["output_price"])

            # Output price should be > input price (always)
            if out < inp:
                return {
                    "valid": False,
                    "reason": f"Output price (${out}) < Input price (${inp}). Suspicious.",
                    "action": "BLOCK_WRITE"
                }

            # Sanity bounds (LLM pricing typically $0.001 - $1 per 1M tokens)
            if inp < 0.0001 or inp > 10 or out > 10:
                return {
                    "valid": False,
                    "reason": f"Pricing out of known range: ${inp}/${out}",
                    "action": "BLOCK_WRITE"
                }

        # Check 3: Context window sanity
        if data.get("context_window"):
            ctx = int(data["context_window"])
            # Known range: 4K - 2M tokens
            if ctx < 4000 or ctx > 2000000:
                return {
                    "valid": False,
                    "reason": f"Context window {ctx} out of known range (4K-2M)",
                    "action": "BLOCK_WRITE"
                }

        # If all checks pass
        return {"valid": True, "action": "ALLOW_WRITE"}

    return {"valid": True, "action": "ALLOW_WRITE"}
```

**Behavior**:
- ✓ Real model → write allowed
- ✗ Fake/unknown model → BLOCK + error message
- ⚠ Suspicious pricing → BLOCK + explain why
- ⚠ Out-of-range context → BLOCK + ask user to verify

**Implementation**: Add to settings.json PreToolUse hooks, runs before any database operation.

---

## Layer 2: Canonical Sources Registry

**Goal**: Establish what counts as "real" so GLM-5.1 can verify before inventing.

**File**: `~/.claude/canonical-sources.json`

```json
{
  "anthropic": {
    "models": ["Claude Opus 4.6", "Claude Sonnet 4.6", "Claude Haiku 4.5"],
    "sources": [
      "https://anthropic.com/models",
      "https://docs.anthropic.com/en/docs/about-claude/models/overview"
    ],
    "version_pattern": "\\d+\\.\\d+(\\.\\d+)?",
    "next_release": "Claude 5.0 (expected 2026-Q3)"
  },
  "openai": {
    "models": ["GPT-4o", "GPT-4o mini", "GPT-4 Turbo", "GPT-3.5 Turbo"],
    "sources": ["https://platform.openai.com/docs/models"],
    "version_pattern": "gpt-\\d+",
    "note": "NO GPT-5, GPT-6, etc. yet"
  },
  "google": {
    "models": ["Gemini 2.0 Flash", "Gemini 1.5 Pro", "Gemini 1.5 Flash"],
    "sources": ["https://ai.google.dev/models"],
    "version_pattern": "Gemini \\d+\\.\\d+",
    "note": "2.0 released 2024, no 3.0 yet"
  },
  "z-ai": {
    "models": ["GLM-5.1"],
    "sources": ["https://z-ai-api.internal/models"],
    "version_pattern": "GLM-\\d+(\\.\\d+)?",
    "next_release": "GLM-6 (TBD)"
  },
  "false_models": {
    "Claude 4.6": "FAKE — latest is 4.5",
    "Gemini 3.2 Pro": "FAKE — not released",
    "DeepSeek V4": "FAKE — latest is V3",
    "GPT-5": "FAKE — not released",
    "Claude 5.0": "UNRELEASED — don't include yet"
  }
}
```

**Usage by GLM-5.1**:
- Before accepting a model name: check canonical-sources.json
- If not listed → DON'T INVENT; ask user to verify
- If marked as FALSE → immediately reject
- If marked as UNRELEASED → ask user if they meant a released version

---

## Layer 3: Validation Before Web Scraping

**Goal**: When pulling data from web, validate before writing.

**Protocol for data scraping tasks**:

```
USER: "Pull LLM pricing from [source]"

BEFORE SCRAPING:
1. Announce which models you'll look for
   "I'll search for: Claude Opus 4.6, GPT-4o, Gemini 2.0, GLM-5.1"

2. If source is unfamiliar, ask for confirmation
   "I don't recognize [source]. Is this an official pricing page?"

3. For each model found, verify against canonical sources
   "Found Claude 3.5 Sonnet. Checking... NOT in canonical list. Skipping (hallucination risk)."

4. For pricing, cross-reference against ≥2 sources
   "Opus pricing: $15/$75 per 1M from Anthropic docs. ✓"
   "Opus pricing: $12/$60 from [third-party]. ⚠ Discrepancy noted."

5. BLOCK if uncertain
   "Model 'Claude 4.6' not found in official sources. Cannot write."

AFTER SCRAPING:
6. Count: "Found 3 real models, skipped 2 fake ones"
7. Ask before writing: "Ready to write 3 models to database?"
```

**Implementation**: Add prompting to all web-scraping workflows.

---

## Layer 4: Anti-Pattern Logging

**Goal**: Track hallucinations so we learn the pattern.

**File**: `~/.claude/anti-patterns.md` (new entries)

When hallucination is detected:

```markdown
## HALLUCINATION_MODEL_FABRICATION

**Pattern**: GLM-5.1 invents AI models that don't exist when web scraping incomplete data.

**Examples**:
- Claude 4.6 (latest is 4.5) ✗
- Gemini 3.2 Pro (not released) ✗
- DeepSeek V4 (latest is V3) ✗

**Trigger conditions**:
- Asked to "pull all LLM data from web"
- Web source has incomplete model list
- GLM-5.1 fills gaps by inventing versions

**Root cause**: No validation before database writes; assumption that "if I found some models, I should find all".

**Fix**: Reality-check hook validates before write. Canonical sources registry blocks unknown models.

**Prevention**:
1. Always verify model existence before writing to DB
2. If web scraping returns <5 known models from major brands, ask user instead of inventing
3. Check canonical-sources.json before accepting any model name
4. Log attempted hallucinations to error-memory for tracking

**Severity**: HIGH (corrupts data, spreads false info)
**Recurrence**: This session only (if prevention works)
```

---

## Layer 5: User Prompts that Trigger Caution

**Risky patterns** (GLM-5.1 should slow down and verify):

| Prompt | Risk | Prevention |
|--------|------|-----------|
| "Pull all LLM data from web" | Invents missing models | Verify each model before write |
| "List every AI model available" | Tries to be comprehensive | Only list confirmed real ones |
| "What's the latest version of X?" | Guesses future releases | Check canonical sources only |
| "Fill in missing pricing data" | Invents prices | BLOCK; ask user for source |
| "Add models that might exist soon" | Fabricates futures | BLOCK; don't speculate |

**GLM-5.1 response to these prompts**:
```
USER: "Pull all LLM data from web and update the database"

GLM-5.1 SHOULD:
1. Verify canonical sources first
2. Announce which models I'll write
3. If incomplete, say "Found only 3 models; refusing to invent others"
4. Ask user for confirmation before writing
5. Log any skipped/uncertain models
```

---

## Layer 6: Explicit "Uncertain? Block" Rule

**Rule**: If GLM-5.1 is unsure whether a model is real, **do not write**.

Add to CLAUDE.md rules:
```
## Hallucination Prevention

When working with external data (AI models, pricing, features):
- NEVER invent missing data
- NEVER guess future versions
- NEVER fill gaps with plausible-sounding fabrications
- If uncertain: ask user, cite sources, or BLOCK

Failure to follow this = data corruption = users see false information.
This is worse than being incomplete.
```

---

## Implementation Checklist

- [ ] Create `glm5-reality-check.py` hook (validates before DB writes)
- [ ] Create `canonical-sources.json` (authoritative model list)
- [ ] Add hook to settings.json PreToolUse
- [ ] Update anti-patterns.md with HALLUCINATION_MODEL_FABRICATION entry
- [ ] Add "uncertain? block" rule to CLAUDE.md
- [ ] Test on all-things-ai: try to insert fake model → should be blocked
- [ ] Update web scraping workflows to announce models + verify

---

## Testing the Prevention

**Test case 1**: Try to insert "Claude 4.6"
```
USER: "Add Claude 4.6 to the database with pricing $10/$50"
GLM-5.1: "Claude 4.6 not in canonical sources. Latest is Claude 4.5. BLOCKED."
```

**Test case 2**: Try to fill incomplete data
```
USER: "I found GPT-4o and Opus on the web. Add all other major models."
GLM-5.1: "Found 2 models. Refusing to invent the others. Add them manually or provide sources."
```

**Test case 3**: Pricing out of range
```
USER: "Add GLM-5.1 with input=$0.000001 and output=$0.000002"
GLM-5.1: "Pricing $0.000001/$0.000002 is unrealistic. BLOCKED. Verify source?"
```

---

## What This Prevents

| Hallucination | Blocked By |
|---------------|-----------|
| Fabricating fake models | Reality-check hook + canonical sources |
| Inventing pricing | Sanity checks (bounds, output > input) |
| Guessing context windows | Range validation (4K-2M) |
| Filling incomplete data | "Uncertain? Block" rule |
| Future version speculation | Version pattern validation |

---

## Integration with GLM-5.1 Protocols

**Fits into**: SANITY CHECK phase (before executing)
- Assumption: "This data comes from real sources"
- Test: Check canonical-sources.json
- Risk: If wrong → data corruption

**Fits into**: EXECUTE phase
- Rule: "Use tools for facts, never generate" → extended to databases
- Reality-check hook enforces this for external writes

**Fits into**: VERIFY phase
- Trace: "Checked 10 models; 3 were real, 7 blocked as hallucinations"
- Log: All blocked attempts to anti-patterns.md
