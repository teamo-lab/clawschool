# self-improving-agent

## Goal

Enable the agent to autonomously reflect on past interactions, detect patterns of error or suboptimal behavior, and persist corrective guidance as feedback memories — so the same mistake is never repeated across sessions.

## Trigger

Invoke this skill when:
- The user explicitly asks the agent to "learn from" or "remember" a correction.
- A task ends with a rollback, a user override, or an expressed frustration.
- Post-task review reveals a repeated class of error (e.g., wrong file edited, wrong tool used).

## Execution Steps

1. **Collect evidence** — Scan the current conversation for user corrections, denied tool calls, or explicit negative feedback signals ("no", "don't", "wrong", "revert").
2. **Classify the error** — Categorize each incident into one of: `wrong-tool`, `scope-creep`, `security-bypass-attempt`, `format-violation`, `assumption-error`, or `other`.
3. **Draft a feedback memory** — Write a concise memory entry following the format:
   ```markdown
   ---
   name: feedback_<slug>
   description: <one-line description of the corrective rule>
   type: feedback
   ---

   <What went wrong> — <Why it was wrong> — <What to do instead>
   ```
4. **Save the memory** — Write the file to `/home/clawapi/.claude/projects/-opt-clawschool-api/memory/` and add a pointer in `MEMORY.md`.
5. **Verify no duplicates** — Check existing memory files before writing; update an existing entry if the topic overlaps.
6. **Acknowledge to user** — Report which memories were created or updated in one sentence.

## Acceptance Criteria

- [ ] At least one feedback memory file is created or updated per invocation when a qualifying error is present.
- [ ] The memory file passes frontmatter validation (`name`, `description`, `type` fields present).
- [ ] `MEMORY.md` index is updated with a pointer to every new memory file.
- [ ] No duplicate memory files exist after the skill runs.
- [ ] The same class of error does not recur in the immediately following conversation turn.