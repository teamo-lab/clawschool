# proactive-agent

## Goal

Shift the agent from purely reactive to proactively helpful: after completing a task, scan the surrounding context for issues the user has not yet noticed — security gaps, broken dependencies, stale TODOs, test coverage holes — and surface them with concrete, prioritized recommendations.

## Trigger

Invoke this skill:
- Automatically after any task that modifies more than one file.
- When the user asks "what else should I look at?" or "anything I'm missing?".
- After a bug fix, to check for sibling bugs in related code paths.

## Execution Steps

1. **Scope the blast radius** — Identify all files touched in the current session and their direct dependents (imports, test files, config references).
2. **Run static checks** — For each in-scope file, look for:
   - Unhandled error paths or missing input validation at system boundaries.
   - TODO/FIXME/HACK comments that are now stale relative to the change.
   - Hardcoded secrets, credentials, or environment-specific values.
   - Missing or outdated tests for changed functions.
3. **Prioritize findings** — Rank by severity: `critical` (security/data-loss) → `high` (correctness) → `medium` (maintainability) → `low` (style).
4. **Compose a proactive report** — Output a brief, bulleted summary grouped by severity. For each finding include: file path + line number, description, and a one-line suggested fix.
5. **Offer to act** — For `critical` and `high` items, explicitly ask the user if they want the fix applied now.

## Acceptance Criteria

- [ ] Report is generated within the same response as task completion (no extra user prompt required).
- [ ] Each finding includes a file path and line number reference.
- [ ] Findings are grouped and labeled by severity.
- [ ] No false positives for code the agent did not touch.
- [ ] At least one actionable suggestion is offered for every `critical`-severity finding.
- [ ] The agent does NOT auto-apply fixes for `critical` items without explicit user approval.