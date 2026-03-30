#!/usr/bin/env python3
"""GLM-5.1 Execution Phase Detector

Detects complex task requests (hypothesis testing, bug fixes, refactoring, research)
and enforces Phase 1 (Success Criteria Definition) before execution.

Runs on UserPromptSubmit to catch complex tasks early.
"""
import json
import sys

# Task keywords indicating complex work requiring the framework
COMPLEX_TASK_KEYWORDS = {
    "hypothesis": ["test hypothesis", "hypothesis", "experiment"],
    "bug_fix": ["fix bug", "debug", "broken", "error", "failing", "issue"],
    "refactor": ["refactor", "rewrite", "restructure", "optimize", "improve performance"],
    "research": ["research", "investigate", "explore", "analyze", "understand"],
    "feature": ["add feature", "implement", "new endpoint", "new function"],
    "optimization": ["optimize", "speed up", "reduce latency", "improve efficiency"],
}

def detect_complex_task(user_message):
    """Check if task requires execution framework (Phases 1-5)."""
    message_lower = user_message.lower()

    for task_type, keywords in COMPLEX_TASK_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                return task_type

    return None

def check_phase_1_present(user_message):
    """Detect if Phase 1 (success criteria) is defined in message."""
    indicators = {
        "explicit_threshold": ("pass" in user_message.lower() or
                              "succeed" in user_message.lower() or
                              "+u" in user_message or
                              ">" in user_message or
                              "%" in user_message),
        "failure_condition": ("fail" in user_message.lower() or
                             "revert" in user_message.lower() or
                             "auto-" in user_message.lower()),
        "success_state": ("should" in user_message.lower() or
                         "expect" in user_message.lower() or
                         "when" in user_message.lower()),
    }

    present = sum(1 for v in indicators.values() if v)
    return present >= 2, indicators  # Need at least 2 of 3

def output_phase_1_template():
    """Output Phase 1 success criteria template."""
    print("""
🟦 EXECUTION FRAMEWORK — Phase 1: Success Criteria Definition

Before executing this complex task, define what "DONE" looks like explicitly.

**TASK**: [What are you trying to accomplish?]

**SUCCESS CRITERIA**:
- Primary: [What quantified outcome = success? (e.g., "+1.5u improvement")]
- Secondary checks: [What secondary metrics must hold? (e.g., "no single stream loses >5u")]

**FAILURE CRITERIA**:
- Auto-revert if: [What outcome = failure with high confidence? (e.g., "≥-5u loss")]
- Investigate if: [What outcome = unclear? (e.g., "mixed per-stream results")]

**DECISION GATE**:
- ✓ PASS: [Condition for accepting result and proceeding]
- ❌ FAIL: [Condition for reverting and stopping]
- ❓ INVESTIGATE: [Condition for root cause analysis]

See ~/.claude/glm5-execution-framework.md Phase 1 for full template.

Once Phase 1 is complete, I'll execute Phases 2-5 (execution → investigation → learning → scope boundary).
""")

# Hook entry point
try:
    hook_input = json.load(sys.stdin)
    user_message = hook_input.get("user_message", "")

    task_type = detect_complex_task(user_message)

    if task_type:
        phase_1_present, _ = check_phase_1_present(user_message)

        if not phase_1_present:
            output_phase_1_template()

except Exception as e:
    # Fail silently
    pass

sys.exit(0)
