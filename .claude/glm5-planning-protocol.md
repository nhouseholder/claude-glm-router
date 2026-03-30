# GLM-5.1 Enhanced Planning Protocol
**When to use**: Any task that takes >5 minutes, involves multiple files, or has unknowns.
**Goal**: Think strategically before executing; prevent hasty decisions; surface assumptions and risks.

---

## Gate 1: Complexity Assessment (30 seconds)

**Ask before planning:**
1. **Single file or multi-file?** (single = lite, multi = full)
2. **Known domain or unfamiliar?** (known = lite, unfamiliar = full)
3. **Reversible or destructive?** (reversible = lite, destructive = full)
4. **User specified the approach, or open-ended?** (specified = lite, open = full)

**Lite planning** (≤1 min): PLAN statement + SANITY CHECK (3 assumptions). Execute.

**Full planning** (≤10 min): Run SPEC-INTERVIEW → DECISION FRAMEWORK → ASSUMPTION LOG → RISK ASSESSMENT → PLAN. Then execute with checkpoints.

---

## Gate 2: Spec Interview (2-3 min) — *Full Planning Only*

**Interview the requirement deeply** (don't just read the user's words):

```
USER SAID: "Add a button to the settings page"

CLARIFY:
- WHERE on page? (top, sidebar, modal footer?)
- WHAT does it do? (trigger action, navigate, open dialog?)
- WHEN is it visible? (always, conditionally?)
- WHO can use it? (all users, admin-only?)
- WHAT happens after? (success state, confirmation?)
- ERROR handling? (what if action fails?)
- BACKWARDS COMPAT? (old settings still work?)
```

**Output**: 1-paragraph clarified requirement (more specific than original request)

---

## Gate 3: Decision Framework (2 min) — *Full Planning Only*

**For each major decision, document:**
```
DECISION: [What choice needs to be made?]
OPTIONS:
  - [Option A] — [pro] | [con]
  - [Option B] — [pro] | [con]
SELECTED: [Option X] because [1-line reason]
REVERSIBILITY: [Can we undo this? how?]
```

**Example:**
```
DECISION: Store handoff checkpoints in .git/ or .glm-handoff-checkpoints/?
OPTIONS:
  - .git/glm-checkpoints/ — keeps everything in repo | pollutes git directory
  - .glm-handoff-checkpoints/ — clean separation | new dir to manage
SELECTED: .glm-handoff-checkpoints/ because isolation = fewer conflicts, cleaner recovery
REVERSIBILITY: Easy — just rm -rf the directory, handoff state lost but local HANDOFF.md survives
```

---

## Gate 4: Assumption Log (2 min) — *Full Planning Only*

**Document every assumption. Format:**
```
ASSUMPTION #1: [claim]
EVIDENCE: [why you believe this]
TEST: [how to verify] — [result: PASS/FAIL]
IMPACT IF WRONG: [what breaks?]

ASSUMPTION #2: ...
```

**Example:**
```
ASSUMPTION #1: Z AI proxy always runs at localhost:17532
EVIDENCE: Startup LaunchAgent, documented in z-ai-switch skill
TEST: curl http://127.0.0.1:17532/health — [PASS: responds with status:ok]
IMPACT IF WRONG: GLM-5.1 routing fails silently, falls back to Opus

ASSUMPTION #2: Git repos are always pushed to GitHub before session end
EVIDENCE: CLAUDE.md rule #2, unpushed-commits-check hook
TEST: git push origin $(git branch --show-current) — [must succeed]
IMPACT IF WRONG: Next session reads stale code, breaks continuity

ASSUMPTION #3: Project memory path is always ~/.claude/projects/[name]/memory/
EVIDENCE: Handoff storage protocol, project-manifest.json
TEST: mkdir -p "$MEMORY_PATH" — [succeeds]
IMPACT IF WRONG: Handoff not stored, work loss across sessions
```

---

## Gate 5: Risk Assessment (3 min) — *Full Planning Only*

**Identify 3+ ways the plan could fail:**
```
RISK #1: [What could go wrong?]
LIKELIHOOD: [high/medium/low]
MITIGATION: [How to prevent or detect]
RECOVERY: [If it happens, how to fix]

RISK #2: ...
```

**Example:**
```
RISK #1: GitHub push fails (rate limit, network, auth)
LIKELIHOOD: medium (happens ~5% of CLaude sessions)
MITIGATION: Test 'git push' with timeout before storage step; explicit fallback
RECOVERY: Document failure in handoff footer, continue with local+memory storage

RISK #2: Context window overflows mid-handoff (large project)
LIKELIHOOD: medium (50+ file projects)
MITIGATION: Track token estimate after each section; abort if >115K
RECOVERY: Save checkpoint, resume later with 'glm-full-handoff --resume'

RISK #3: User interrupts mid-execution (closes Claude)
LIKELIHOOD: high (user controls session lifecycle)
MITIGATION: Checkpointing system saves state every major step
RECOVERY: Detect checkpoint, skip completed sections, resume from last safe point
```

---

## Gate 6: Strategic Plan (3-5 min) — *Full Planning Only*

**Write implementation steps with:**
- **Goal** (what problem does this solve?)
- **Approach** (why this strategy vs alternatives?)
- **Atomic steps** (each one succeeds/fails independently)
- **Verification** (how to know each step worked?)
- **Exit criteria** (what does "done" look like?)

**Example:**
```
GOAL: Enable reliable handoffs for GLM-5.1 even if interrupted.

APPROACH: Checkpoint system (save state after each major section) allows resumption.
Why: Prevents loss of work if context overflows, network fails, or user closes app.

STEPS:
1. Detect project + load previous checkpoints (ATOMIC: succeeds or explicit error)
2. Gather git facts with timeouts (ATOMIC: timeouts prevent hangs)
3. Build handoff content with context tracking (ATOMIC: abort cleanly if overflow)
4. Storage: local → memory → GitHub (ATOMIC: local always succeeds; others fail gracefully)
5. Verify architecture (pushed? dates match? cleanup done?)

VERIFICATION:
- Step 1: Checkpoint A saved ✓
- Step 2: Checkpoint B with git data ✓
- Step 3: Checkpoint C with handoff filename ✓
- Step 4: Checkpoint D with storage results ✓
- Step 5: Report shows ✓ or ⚠ for each location

EXIT CRITERIA:
- All 17 handoff sections have real content (no placeholders)
- Handoff stored in ≥2 locations (local is mandatory; GitHub optional)
- Checkpoints saved for resumption
- User sees clear status report
```

---

## Execution with Progress Checkpoints (During Work)

**As you execute, track progress:**
```
Step 1/5: [Description] → [Status: in-progress/done/failed]
  Checkpoint: [saved/not-saved]

Step 2/5: [Description] → [Status]
  Checkpoint: [saved/not-saved]
```

**On failure:**
- Save checkpoint with error details
- Don't retry blindly; diagnose
- Either: (a) fix and resume, or (b) abort with clear reason

**On success:**
- Verify exit criteria for that step
- Document key fact learned (for multi-file work)
- Move to next step

---

## Post-Execution: Verification (1-2 min)

**After executing the plan, verify:**

1. **Did it answer the original question?** (re-read user request)
2. **Did assumptions hold?** (which tests failed?)
3. **Did risks materialize?** (any unexpected problems?)
4. **Is the output usable?** (trace one example)
5. **What surprised you?** (log to anti-patterns.md if relevant)

**Example trace:**
```
USER ASKED: "Can GLM-5.1 reliably execute the full-handoff command?"

VERIFIED:
- full-handoff skill is accessible (invoked successfully) ✓
- Skill has 9 atomic steps with error handling ✓
- Checkpointing system designed for recovery ✓
- Tested on current project (claude-glm-router) ✓
- But: Didn't run end-to-end test on real large project ⚠
- Answer: 90% ready (core logic done; needs live testing)

SURPRISED BY: iCloud corruption breaking git objects (mmalogic repo)
LOG TO ANTI-PATTERNS: "iCloud + active git repos = fatal tree errors"
```

---

## When NOT to Use Full Planning

Skip to lite (PLAN + SANITY CHECK only) if:
- Task is <5 minutes
- Completely reversible (edit a single line)
- Domain is trivial (typo fix, obvious change)
- User gave explicit step-by-step instructions
- Urgent/time-sensitive (but document assumptions still)

---

## Template: Copy-Paste for Any Task

```markdown
# [Task Name] — Planning Document

## COMPLEXITY GATE
- Single/multi-file: [answer]
- Known/unfamiliar domain: [answer]
- Reversible/destructive: [answer]
→ Lite / Full planning? [choice]

## SPEC INTERVIEW
USER SAID: "[original request]"
CLARIFIED: "[more specific requirement]"

## DECISION FRAMEWORK
DECISION 1: [choice needed]
SELECTED: [option] because [reason]
...

## ASSUMPTION LOG
ASSUMPTION 1: [claim]
TEST: [verification method] → [PASS/FAIL]
...

## RISK ASSESSMENT
RISK 1: [failure mode]
MITIGATION: [how to prevent]
RECOVERY: [how to fix]
...

## STRATEGIC PLAN
GOAL: [problem solved]
APPROACH: [why this strategy]
STEPS: 1. [atomic] 2. [atomic] 3. ...
EXIT CRITERIA: [what "done" means]

## EXECUTION LOG
Step 1 → [in-progress/done/failed]
Step 2 → [status]
...

## VERIFICATION
- Did it answer the Q? [yes/no]
- Assumptions held? [which passed/failed]
- Risks realized? [yes/no which]
- Output usable? [trace one example]
```

---

## Integration with GLM-5.1 Hooks

**When this protocol runs:**
- PLAN statement from Gate 1 (complexity) → satisfies PreToolUse validator
- SANITY CHECK from Gate 1 (3 assumptions) → can be explicit for auditor
- VERIFY trace from Verification section → satisfies quality gates
- Response stays <40 lines by deferring full planning to separate artifact (this doc)

**Result**: GLM-5.1 responds concisely in chat, but thinks deeply in planning doc before acting.
