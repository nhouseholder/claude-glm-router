#!/usr/bin/env python3
"""GLM-5.1 Hypothesis Pre-Flight Validator

Runs on UserPromptSubmit to detect hypothesis testing requests and enforce Phase 1 completion.
Detects: "test hypothesis", "run backtest", "try this change", etc.
Validates: All Phase 1 gates passed before proceeding to execution.
"""
import json
import sys
import os

hypothesis_keywords = [
    "test hypothesis",
    "test this hypothesis",
    "run backtest",
    "try this change",
    "try this improvement",
    "test this idea",
    "backtest",
    "hypothesis test",
]

phase_1_requirements = [
    "hypothesis statement",
    "mechanism",
    "expected impact",
    "sample",
    "pass threshold",
    "sample_validation",
]

def detect_hypothesis_request(user_message):
    """Check if user is asking for hypothesis test."""
    message_lower = user_message.lower()
    for keyword in hypothesis_keywords:
        if keyword in message_lower:
            return True
    return False

def check_phase_1_complete(user_message):
    """Detect if Phase 1 validation is present in user message."""
    indicators = {
        "hypothesis": "hypothesis" in user_message.lower() or "change:" in user_message.lower(),
        "mechanism": "because" in user_message.lower() or "reason" in user_message.lower() or "why" in user_message.lower(),
        "expected": ("expect" in user_message.lower() or "+u" in user_message or "u)" in user_message),
        "sample": ("fight" in user_message.lower() or "example" in user_message.lower()),
        "threshold": ("pass" in user_message.lower() or "improve" in user_message.lower() or "+1" in user_message or "+2" in user_message or "+3" in user_message),
    }

    complete = sum(1 for v in indicators.values() if v)
    return complete >= 3, indicators  # Need at least 3 of 5 Phase 1 elements

def output_phase_1_reminder():
    """Output Phase 1 validation reminder."""
    print("""
🔷 HYPOTHESIS PRE-FLIGHT CHECK

Before running backtest, complete Phase 1 (5 min):

(1) **Hypothesis statement** — What exactly changes?
    Example: "Skip DEC when opponent has low striking defense (<45%) AND high SApM (>4.0)"

(2) **Mechanism** — Why should this improve ROI?
    Example: "Low StrDef + high SApM = opponent gets beaten up = unlikely distance = DEC unlikely to cash"

(3) **Expected impact** — Quantified prediction
    Example: "+3-5u (medium confidence)" or "+1-2u (exploratory)"

(4) **Sample validation** — 3-5 recent fights where hypothesis applies
    Example: Fight A (stats X): Gate triggers, current pred DEC, would skip it. Outcome: [actual result]. Gate makes sense? [yes/no]

(5) **Pass/Fail thresholds** — Specific numbers
    Example: "PASS if ≥+1.5u combined, FAIL if <+1.5u"

See ~/.claude/glm5-hypothesis-testing-protocol.md Phase 1 for full template.

Once Phase 1 is complete, I'll run Phase 2 (backtest) efficiently without narration or polling.
""")

# Hook entry point
try:
    hook_input = json.load(sys.stdin)
    user_message = hook_input.get("user_message", "")

    if detect_hypothesis_request(user_message):
        phase_1_complete, indicators = check_phase_1_complete(user_message)

        if not phase_1_complete:
            output_phase_1_reminder()

except Exception as e:
    # Fail silently
    pass

sys.exit(0)
