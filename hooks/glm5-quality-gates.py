"""GLM-5.1 Active Quality Gates: Score responses, suggest improvements.

Runs on Stop event. Scores response across 5 dimensions (2pts each = 10 total).
If score <6/10, suggests retry or clarification.

Only runs when GLM-5.1 is active (detects via transcript).
"""
import json
import sys
import os

try:
    hook_input = json.load(sys.stdin)

    # Only run on GLM-5.1
    transcript_path = hook_input.get("transcript_path", "")
    is_glm5 = False
    if transcript_path:
        try:
            with open(transcript_path) as f:
                lines = f.readlines()
            for line in reversed(lines):
                entry = json.loads(line)
                msg = entry.get("message", {})
                if msg.get("role") == "assistant" and "model" in msg:
                    is_glm5 = "haiku" in msg["model"].lower()
                    break
        except Exception:
            pass

    if not is_glm5:
        sys.exit(0)

    # Get response
    response = hook_input.get("last_assistant_message", "") or ""
    if not response or len(response) < 20:
        sys.exit(0)

    # Score across 5 dimensions (2pts each)
    score = 0
    feedback = []

    # 1. Completeness: Does it answer the question?
    has_answer = (
        "Yes" in response or "No" in response or
        "✓" in response or "❌" in response or
        response.count(":") > 2  # Multiple facts
    )
    if has_answer:
        score += 2
    else:
        feedback.append("incomplete (answer the Q directly)")

    # 2. Concreteness: Includes examples/traces?
    has_example = (
        "example" in response.lower() or
        "trace" in response.lower() or
        "`" in response or  # Code snippet
        "1." in response  # Numbered list
    )
    if has_example:
        score += 2
    else:
        feedback.append("vague (add examples)")

    # 3. Clarity: Structured and readable?
    lines = response.split("\n")
    has_structure = (
        len(lines) > 3 or  # Multi-paragraph
        "**" in response or  # Bold formatting
        "-" in response  # Bullet points
    )
    if has_structure:
        score += 2
    else:
        feedback.append("unclear (structure with bullets/bold)")

    # 4. Confidence: Acknowledges uncertainty?
    has_uncertainty = (
        "uncertain" in response.lower() or
        "?" in response or
        "might" in response.lower() or
        "likely" in response.lower()
    )
    if has_uncertainty:
        score += 2
    else:
        feedback.append("overconfident (flag unknowns)")

    # 5. Protocol adherence: Follows PLAN/VERIFY?
    follows_protocol = (
        ("PLAN:" in response or "plan:" in response) or
        ("VERIFY" in response or "trace" in response.lower())
    )
    if follows_protocol:
        score += 2
    else:
        feedback.append("protocol (state PLAN, add trace)")

    # Report
    if score >= 7:
        quality = "✅ HIGH"
    elif score >= 5:
        quality = "⚠️  OK"
    else:
        quality = "❌ LOW"

    msg = f"\n[GLM-5 Quality: {quality} ({score}/10)"
    if feedback:
        msg += f" — improve: {', '.join(feedback)}"
    msg += "]\n"

    print(json.dumps({
        "type": "info",
        "message": msg
    }))

except Exception as e:
    pass
