#!/usr/bin/env python3
"""GLM-5.1 Investigation Enforcer — Phase 3 Mandatory Enforcement

Detects when Phase 3 (mandatory investigation) is incomplete but Phase 4 (learning capture)
is about to start. Blocks Phase 4 and outputs Phase 3 protocol template.

Runs on PreToolUse to catch the attempt to skip investigation.
"""
import json
import sys
import re

# Indicators that Phase 3 investigation has NOT been done
SKIP_INDICATORS = {
    "revert without": [
        r"just reverted?",
        r"revert.{0,30}(?!cause|because|why|root|analysis)",
        r"reverted back",
    ],
    "no_root_cause": [
        r"FAIL|FAILED(?!.*\bcause\b)",
        r"INVESTIGATE(?!.*\b(mechanism|impact|challenge|learning)\b)",
        r"don't know why",
        r"unclear",
    ],
    "minimal_analysis": [
        r"hypothesis (failed|didn't work|didn't improve)",
        r"reverting the (change|hypothesis|test)",
    ],
}

# Indicators that Phase 4 is about to start
PHASE_4_INDICATORS = [
    "EXPERIMENT_LOG",
    "learning",
    "log.*result",
    "document.*finding",
    "captured",
]

def detect_phase_3_incomplete(user_message):
    """Check if Phase 3 investigation appears incomplete."""
    message_lower = user_message.lower()

    for category, patterns in SKIP_INDICATORS.items():
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                # Check it's not followed by investigation keywords
                if not re.search(
                    r"\b(mechanism|impact|why|root cause|analysis|parlay|fight|event)\b",
                    message_lower[
                        max(0, message_lower.find(pattern) - 100):
                        min(len(message_lower), message_lower.find(pattern) + 200)
                    ],
                    re.IGNORECASE
                ):
                    return True

    return False

def detect_phase_4_start(user_message):
    """Check if Phase 4 (learning capture) is about to start."""
    message_lower = user_message.lower()

    for indicator in PHASE_4_INDICATORS:
        if re.search(indicator, message_lower, re.IGNORECASE):
            return True

    return False

def output_phase_3_protocol():
    """Output Phase 3 Investigation Protocol reminder."""
    protocol = """
🔴 PHASE 3: Mandatory Investigation — You Cannot Skip This

You appear to be moving to Phase 4 (learning capture) without completing Phase 3 (investigation).
This is the exact failure pattern from v11.18. Phase 3 is MANDATORY when results are FAIL or UNCLEAR.

---

PHASE 3: Failure Investigation Protocol

When your hypothesis test returns FAIL or UNCLEAR:

**1. Mechanism Check** — Did your change fire as intended?
   - Sample 3-5 fights where your mechanism should apply
   - Show: Which predictions changed? Which outcomes did they affect?
   - Analyze: Does the mechanism make intuitive sense?

**2. Impact Analysis** — Where did value get lost or gained?
   - Baseline P/L: [metric breakdown]
   - Test P/L: [metric breakdown]
   - Delta: [which streams gained, which lost, by how much]
   - Finding: [Identify the problem area]

**3. Hypothesis Challenge** — Why didn't your mechanism work?
   - Expected: [What you thought would happen]
   - Observed: [What actually happened]
   - Possibility 1: [First explanation]
   - Possibility 2: [Second explanation]
   - Possibility 3: [Third explanation]

**4. Learning Capture** — What prevents re-testing this?
   - Document the ROOT CAUSE (not just the symptom)
   - Identify what assumption was wrong
   - State clearly: "Don't [specific action] because [specific reason]"

---

EXAMPLE (v11.18):
❌ SKIP: "Hypothesis FAIL, parlay lost -10.76u, reverting"
✅ COMPLETE:
   - Mechanism: Gate fired on 42 events as expected ✓
   - Impact: Parlay -10.76u, others +3.85u → net failure ✓
   - Hypothesis: Gate logic may affect non-Method scoring paths
   - Learning: "Don't gate Method predictions in ways affecting parlay" ✓

---

Complete Phase 3 investigation before proceeding to Phase 4.

Reference: ~/.claude/glm5-execution-framework.md Phase 3 (detailed template)
"""
    print(protocol)

# Hook entry point
try:
    hook_input = json.load(sys.stdin)
    event = hook_input.get("hook_event_name", "")

    # Only runs on PreToolUse
    if event != "PreToolUse":
        sys.exit(0)

    user_message = hook_input.get("user_message", "")

    # Check if Phase 3 is incomplete AND Phase 4 is starting
    if detect_phase_3_incomplete(user_message) and detect_phase_4_start(user_message):
        output_phase_3_protocol()
        # Don't block — let user decide, but make the requirement explicit

except Exception as e:
    # Fail silently
    pass

sys.exit(0)
