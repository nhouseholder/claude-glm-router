#!/usr/bin/env python3
"""GLM-5.1 Reality-Check Hook — Block hallucinated data before database writes.

Prevents fabrication of fake AI models, pricing, and other external data.
Runs on PreToolUse to intercept database/file operations.

Example blocks:
- Model "Claude 4.6" (latest is 4.5) → BLOCKED
- Model "Gemini 3.2 Pro" (not released) → BLOCKED
- Pricing $0.000001/$0.000002 (unrealistic) → BLOCKED
- Context window 5000000 (out of range) → BLOCKED
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Canonical sources — source of truth for what's real
CANONICAL_MODELS = {
    "anthropic": ["Claude Opus 4.6", "Claude Sonnet 4.6", "Claude Haiku 4.5"],
    "openai": ["GPT-4o", "GPT-4o mini", "GPT-4 Turbo", "GPT-3.5 Turbo"],
    "google": ["Gemini 2.0 Flash", "Gemini 1.5 Pro", "Gemini 1.5 Flash"],
    "z-ai": ["GLM-5.1", "GLM-5", "GLM-4"],
    "meta": ["Llama 3", "Llama 3.1"],
    "deepseek": ["DeepSeek V3", "DeepSeek V2.5"],
    "mistral": ["Mistral Large 2", "Mixtral 8x22B"],
}

FALSE_MODELS = {
    "Claude 4.6": "Latest is 4.5",
    "Claude 5.0": "Unreleased (expected Q3 2026)",
    "Claude 6.0": "Does not exist",
    "Gemini 3.2 Pro": "Not released",
    "Gemini 3.0": "Not released",
    "DeepSeek V4": "Latest is V3",
    "GPT-5": "Not released",
    "GPT-6": "Does not exist",
}

def is_model_real(model_name):
    """Check if model exists in canonical list."""
    model_lower = model_name.lower()

    # Check false models first
    for fake, reason in FALSE_MODELS.items():
        if fake.lower() in model_lower:
            return False, f"Known false model: {fake} ({reason})"

    # Check canonical list
    for brand, models in CANONICAL_MODELS.items():
        for real_model in models:
            if real_model.lower() in model_lower:
                return True, "Found in canonical sources"

    return False, f"Not in canonical model list"

def validate_pricing(input_price, output_price):
    """Validate AI model pricing sanity."""
    try:
        inp = float(input_price)
        out = float(output_price)
    except (ValueError, TypeError):
        return False, "Pricing must be numeric"

    # Output price should be >= input price
    if out < inp:
        return False, f"Output price (${out:.6f}) < Input price (${inp:.6f}) — physically impossible"

    # Known range: $0.0001 - $10 per 1M tokens
    if inp < 0.00001 or inp > 100:
        return False, f"Input price ${inp} out of known range ($0.00001-$100)"
    if out < 0.00001 or out > 100:
        return False, f"Output price ${out} out of known range ($0.00001-$100)"

    return True, "Pricing in realistic range"

def validate_context_window(context_window):
    """Validate context window sanity."""
    try:
        ctx = int(context_window)
    except (ValueError, TypeError):
        return False, "Context window must be numeric"

    # Known range: 4K - 2M tokens
    if ctx < 4000:
        return False, f"Context {ctx} < 4K (minimum known)"
    if ctx > 2000000:
        return False, f"Context {ctx} > 2M (unrealistic)"

    return True, "Context window in realistic range"

def validate_database_write(data):
    """
    Validate data before writing to database.
    Returns: (valid: bool, message: str, action: "ALLOW" or "BLOCK")
    """

    if not data.get("type"):
        return True, "No type specified; allowing", "ALLOW"

    data_type = data.get("type", "").lower()

    # ===== MODEL VALIDATION =====
    if data_type == "model":
        model_name = data.get("model_name", "")

        if not model_name:
            return False, "Model name missing", "BLOCK"

        # Check if model is real
        is_real, reason = is_model_real(model_name)
        if not is_real:
            return False, f"Hallucination risk: {reason}. Model '{model_name}' not in canonical sources.", "BLOCK"

        # Validate pricing if provided
        if data.get("input_price") is not None and data.get("output_price") is not None:
            valid, reason = validate_pricing(data["input_price"], data["output_price"])
            if not valid:
                return False, f"Pricing validation failed: {reason}", "BLOCK"

        # Validate context window if provided
        if data.get("context_window") is not None:
            valid, reason = validate_context_window(data["context_window"])
            if not valid:
                return False, f"Context validation failed: {reason}", "BLOCK"

        return True, f"Model '{model_name}' validated ✓", "ALLOW"

    # ===== GENERIC FALLBACK =====
    return True, "Validation passed", "ALLOW"

# Hook entry point
try:
    hook_input = json.load(sys.stdin)
    event = hook_input.get("hook_event_name", "")

    # Only validate on PreToolUse for database operations
    if event != "PreToolUse":
        sys.exit(0)

    # Extract the tool being called
    tool_name = hook_input.get("tool_name", "")
    tool_args = hook_input.get("tool_args", {})

    # Check if this is a database write operation
    is_db_write = "d1" in tool_name.lower() or "database" in tool_name.lower() or "write" in tool_name.lower()

    if not is_db_write:
        sys.exit(0)  # Not a database operation; skip validation

    # Try to extract data from tool args
    data = tool_args.get("data", {})

    if not data:
        sys.exit(0)  # No data to validate

    # Validate
    valid, message, action = validate_database_write(data)

    if action == "BLOCK":
        # Output error message for user
        print(f"\n⚠️ REALITY CHECK BLOCKED:\n{message}\n")
        print("This prevents hallucinated data (fake models, pricing, etc.) from entering the database.")
        print("\nTo proceed:")
        print("1. Verify the data is real (check official sources)")
        print("2. Ask your user to provide the data manually")
        print("3. Cite the source when adding")
        sys.exit(1)  # Block the tool call
    else:
        sys.exit(0)  # Allow the operation

except Exception as e:
    # On error, fail safely (don't corrupt data)
    print(f"Reality-check error (failing safely): {e}")
    sys.exit(1)
