# self-improving-agent

## Objective

After completing any non-trivial task, the agent reviews its own execution trace, identifies friction points or errors, and—when appropriate—proposes concrete updates to its CLAUDE.md instructions, memory, or skill files so that future runs perform better without user intervention.

## Execution Steps

1. **Post-task reflection trigger** — When a task completes (success or failure), automatically enter a brief reflection phase. Check if the task involved ≥3 tool calls or produced an error/retry.
2. **Trace analysis** — Review the tool call sequence and any error messages from the current conversation. Identify: (a) repeated lookups that could be cached in memory, (b) wrong first approaches that required backtracking, (c) missing context that caused unnecessary user questions.
3. **Improvement candidate generation** — For each identified friction point, draft one of the following:
   - A new or updated memory file under `.claude/projects/.../memory/`
   - A clarifying line in `CLAUDE.md`
   - A new skill document if the pattern is reusable
4. **Confidence gate** — Only apply the change automatically if confidence is HIGH (pattern seen ≥2 times or error was unambiguous). Otherwise, present the proposed change to the user with a one-line rationale and ask for approval.
5. **Apply & index** — Write the approved improvement file and update `MEMORY.md` or the skill index as appropriate.
6. **Log the improvement** — Append a single line to `.claude/projects/.../memory/improvements_log.md` with date, task summary, and change made.

## Acceptance Criteria

- [ ] After a task with a backtrack/retry, the agent produces at least one improvement candidate.
- [ ] Low-confidence candidates are surfaced to the user before being written.
- [ ] High-confidence candidates are applied without prompting and appear in `improvements_log.md`.
- [ ] No improvement overwrites an existing memory without first reading and merging it.
- [ ] The skill does not trigger on trivial single-tool tasks (e.g., a simple file read).