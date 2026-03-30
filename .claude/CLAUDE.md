# Claude Code Settings

@personality.md

## Projects

Python + JS/TS. All projects at `~/Projects/<name>/` (flat). `~/Projects/` symlinks to iCloud `ProjectsHQ/`. GitHub is source of truth. For iCloud dirs, clone to `/tmp/` for git ops.

| Live Site | GitHub Repo | Local Path |
|-----------|-------------|------------|
| mmalogic.com | ufc-predict | ~/Projects/mmalogic |
| diamondpredictions.com | diamond-predictions | ~/Projects/diamondpredictions |
| mystrainai.com | Strain-Finder-Front-Cannalchemy-Back | ~/Projects/mystrainai |
| enhancedhealthai.com | enhanced-health-ai | ~/Projects/enhancedhealthai |
| nestwisehq.com | dad-financial-planner | ~/Projects/nestwisehq |
| courtside-ai.pages.dev | courtside-ai | ~/Projects/courtside-ai |
| researcharia.com | aria-research | ~/Projects/researcharia |

When switching projects: drop all assumptions, read project CLAUDE.md + memory, verify tech stack + git status.

## Session Start: 3-Gate Verification

**All 3 gates must pass before starting work.** Details in `/review-handoff`.
- **GATE 1**: Correct repo (trace from site-to-repo-map.json, verify git remote)
- **GATE 2**: Local matches remote (`git fetch && compare SHAs`, pull if behind)
- **GATE 3**: Read context (project CLAUDE.md, MEMORY.md, HANDOFF.md, anti-patterns.md)

## Rules (non-hook-enforced — these need YOUR attention)

1. **Commit AND push between tasks** — rate limits kill 79% of multi-task sessions. GitHub is the source of truth, not iCloud. Every commit must be pushed.
2. **GitHub-first for git ops** — iCloud corrupts `.git/objects/` on active repos. For any git-heavy work, clone from GitHub to `/tmp/`, do the work there, push, then let iCloud sync passively. Never trust iCloud git state over GitHub.
3. **Use site commands** — `/mmalogic`, `/update-diamond`, `/update-courtside`, `/update-mystrainai`, `/update-enhancedhealth`, `/update-researcharia`, `/update-nestwisehq`
4. **Handoff = /full-handoff always**
5. **Read the spec, not the code** — for domain questions, read the spec file first
6. **Never flip-flop** — read spec before changing your answer
7. **Do it yourself** — never tell user to do something manually if tools can do it
8. **Never delete** — always archive. When in doubt, ask.
9. **NEVER disconnect working integrations** — preserve API calls, webhooks, GitHub Actions triggers
10. **Simplest fix first** — 5-line fix beats 200-line refactor
11. **Stream long-running scripts** — `| tee output.log`
12. **Never poll background tasks** — use `run_in_background` or long timeout
13. **Hallucination Prevention** — When working with external data (models, pricing, features, APIs):
    - NEVER invent missing data to "complete" a dataset
    - NEVER guess future product versions (Claude 4.6 doesn't exist)
    - NEVER fill gaps with plausible-sounding fabrications
    - If uncertain: ask user, cite sources, or BLOCK (fail safely)
    - Reality-check hook validates all database writes; suspicious data is BLOCKED automatically
    - See `canonical-sources.json` for authoritative model list
    - This prevents data corruption and false information spreading

14. **Execution Framework** (GLM-5.1 deep investigation + learning capture):
    - **Phase 1 — Success Criteria**: Before executing complex task, define PASS/FAIL/INVESTIGATE thresholds explicitly. No ambiguous "neutral" results.
    - **Phase 2 — Execution with Checkpoints**: Execute with decision points (not just "run and see"). Check environment, interim results, final state.
    - **Phase 3 — Mandatory Investigation**: If FAIL/UNCLEAR, always investigate: (1) mechanism check, (2) impact analysis, (3) hypothesis challenge, (4) learning capture.
    - **Phase 4 — Structured Learning**: Log findings with root cause + 3+ example instances. Prevents re-testing same issue.
    - **Phase 5 — Scope Boundary**: One task = one decision. Stop at decision boundary. No auto-pivot to related work.
    - **Applies to**: Hypothesis testing, bug fixes, refactors, research, optimization, experimentation, any complex task (5+ min, multi-file, high-stakes).

15. **Hypothesis Testing Protocol** (GLM-5.1 enhanced — address backtesting gaps):
    - **Pre-test gate**: Before running backtest, ALWAYS sample 3-5 recent events showing hypothesis would apply. Validate intuition before compute.
    - **Explicit criteria**: Set pass/fail threshold PRE-TEST (e.g., "Need +1.5u minimum to proceed, fail if <+1.5u"). No ambiguous "neutral" results.
    - **Batch operations**: Run backtest once, check once, report once. NO polling loops. NO narration ("Let me check...").
    - **Failure analysis**: When test returns negative/neutral, MUST analyze: Which fights triggered gate? Which bet types lost? Why? Document 3+ example fights.
    - **Single response scope**: One hypothesis test = one decision (PASS/FAIL/INVESTIGATE). Stop at "Ready for next hypothesis." No auto-pivot to other improvements.
    - **Template logging**: Every experiment → EXPERIMENT_LOG.md with: Hypothesis | Expected | Actual | Delta | Pass/Fail | Root Cause | Example Fights | Decision.
    - **Token efficiency**: Backtest status → single async run. Focus response on results, not process. Max 5 tool calls per hypothesis test.

16. **File Handling Protocol** (GLM-5.1 mandatory — prevent data corruption):
    - **RULE 1 — Backup before edit**: NEVER edit files without creating timestamped backup first. Backup naming: `filename.pre-edit-{YYYYMMDD}_{HHMMSS}.bak`. Verify backup exists before editing.
    - **RULE 2 — Detect corruption immediately**: Check for invalid totals, missing keys, type changes, NaN values, file size regression. If corruption detected, STOP immediately.
    - **RULE 3 — Restore from git history**: On corruption, restore from git using `git checkout {commit-SHA} -- file.json`. Never try to "fix" a corrupted file by editing. Git is source of truth.
    - **RULE 4 — Phase 2 integrity checkpoints**: Add validation before AND after backtest. Checkpoint 1B: Verify algorithm syntax, registry structure, baseline readable. Checkpoint 2C: Verify output file exists, data structure valid, totals correct, matches baseline.
    - **RULE 5 — Audit all operations**: Log every backup, edit, restore, corruption detection to `file-change-audit.md` with timestamp, operation type, file, details, and status.
    - **Incident reference**: v11.18 registry corruption (2026-03-29) exposed these gaps. Protocol is MANDATORY going forward.
    - **Reference**: See `~/.claude/glm5-file-handling-protocol.md` for full protocol, checklists, and recovery procedures.

## Hooks Handle These (don't duplicate in context — they fire mechanically)

`impossible-stats-detector.py`, `missing-odds-detector.py`, `surgical-scope.py`, `protect-skills.py`, `agent-limit.py`, `correction-detector.py`, `no-narration-stops.py`, `version-bump-check.py`, `block-dangerous-commands.py`, `deploy-guard.py`, `ufc-context-loader.py`, `memory-migrator.py`, `session-context-loader.py`, `observe.py`, `unpushed-commits-check.py`, `anti-pattern-enforcer.py`, `anti-pattern-gate.py`

## Scheduled Agents (run autonomously — don't duplicate)

- **nightly-memory-consolidation** (3am daily) — prune, dedup, promote observations to memory
- **research-scout** (4am Mon/Wed/Fri) — find new tools/updates, stage in `~/.claude/memory/new-learnings.md`

## Backtest Rules

Walk-forward ONLY. No post-event data leakage. 80%+ accuracy = suspect. Cache all scraped data — commit to GitHub. UFC: 70+ events. NHL/MLB/NBA/CBB: 3 seasons minimum.

## Destructive Write Protection

Before overwriting ANY external store: (1) check existing size, (2) size regression = ABORT, (3) backup first, (4) merge don't replace, (5) post-write verify. **Cloudflare deploys are IRREVERSIBLE** — KV assets purged on every deploy.

## Bug Recording

Every bug fix → `~/.claude/anti-patterns.md`. Check anti-patterns BEFORE attempting any fix. Commit to GitHub.

## Memory

Two systems: (1) Hierarchical (`~/.claude/memory/`), (2) Project-scoped (`~/.claude/projects/.../memory/`).

## Communication

Lead with user impact. Tables for comparisons. One-line status for routine work. Batch stale task notifications into ONE message.

@RTK.md

## Post-Change Report (MANDATORY)

**Website projects:**
```
---
DONE: [1-2 sentence summary]
✅ Version bumped: v[old] → v[new] in [file]
✅ GitHub synced: committed and pushed (commit [SHA])
✅ Deployed: pushed to Cloudflare via [method]
✅ Now live: verified at [URL]
Notes: [or "None"]
```

**Non-website projects:**
```
---
DONE: [summary]
✅ GitHub synced: committed and pushed (commit [SHA])
Version: N/A — [reason]
Deployed: N/A — not a website
Notes: [or "None"]
```

Use ❌ with explanation for any step NOT done. Every ✅ is a sworn truthful confirmation.

## Superpowers Repo Sync

After modifying `~/.claude/skills/`, `CLAUDE.md`, `hooks/`, `commands/`, or `anti-patterns.md`: clone to `/tmp/superpowers-sync`, copy files, commit, push to GitHub (`nhouseholder/nicks-claude-code-superpowers`), clean up.
