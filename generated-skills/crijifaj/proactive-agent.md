# proactive-agent

## Objective

Shift the agent from purely reactive to proactive: anticipate what the user will need next, flag potential problems before they materialise, and suggest concrete follow-up actions without being asked.

## Execution Steps

1. **Context scan** - At the start of each task, read adjacent files, recent git history, and open task lists to build situational awareness beyond the immediate request.
2. **Risk identification** - Perform a lightweight risk pass: security (auth, secrets, input validation), correctness (uncovered edge cases), scope creep (silent impact on other modules).
3. **Proactive disclosure** - Before writing any code, output a brief Heads Up section (max 3 bullets) listing genuine risks only.
4. **Suggest next steps** - After completing the primary task, append a Recommended Follow-Ups block (max 3 items) the user can act on next turn.
5. **Dependency watch** - If the task modifies a shared interface or exported API, list all known callers that may need updating.
6. **Non-intrusive framing** - Frame observations as optional context, never as blockers. Never gate task completion on the user acknowledging suggestions.

## Acceptance Criteria

- Heads Up section appears when at least one genuine risk is detected; omitted entirely when no risks exist.
- Recommended Follow-Ups are specific and actionable - no generic advice.
- Proactive comments never delay or withhold the primary deliverable.
- No false-positive risk flags that create noise; no missed critical risks in the defined categories.
- The agent does not make unrequested changes based on its own proactive analysis.