# proactive-agent

## Goal
Shift from purely reactive task execution to proactive issue discovery — identify problems the user has not yet noticed and report them with concrete, prioritized recommendations.

## When to Invoke
- When the user asks to "review", "audit", or "check" the project without specifying a target
- After a major refactor or dependency update
- At the start of a new session when the project state is unknown
- Periodically as a background health check (e.g. via `/loop`)

## Execution Steps

1. **Environment snapshot** — Run the following checks in parallel:
   - `git status` — uncommitted or untracked files
   - Scan for TODO/FIXME/HACK comments in source files (Grep)
   - Check for outdated or vulnerable dependencies (e.g. `npm audit`, `pip list --outdated`)
   - Look for missing or stale `.env.example` / config template files
   - Identify test files with no assertions or skipped tests

2. **Security surface scan** — Check for:
   - Hardcoded secrets or tokens in source files
   - Overly permissive file permissions on sensitive config
   - Exposed internal endpoints or debug flags in production config

3. **Triage findings** — Categorize each finding as:
   - `CRITICAL` — data loss, security breach, or build failure risk
   - `WARNING` — degraded reliability or maintainability
   - `INFO` — nice-to-have improvements

4. **Report** — Output a structured list grouped by severity. For each finding include: location (file:line), description, and a one-line recommended action.

5. **Propose next steps** — Ask the user which `CRITICAL` or `WARNING` items to address first. Do not auto-fix without confirmation.

## Acceptance Criteria
- [ ] All four environment snapshot checks are executed
- [ ] Security surface scan is always included
- [ ] Findings are grouped by `CRITICAL` / `WARNING` / `INFO`
- [ ] Each finding includes file path and line number where applicable
- [ ] Agent does NOT auto-apply fixes — user confirmation is required before any mutation
- [ ] If no issues are found, agent explicitly states the project is clean