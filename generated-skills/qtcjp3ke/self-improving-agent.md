# self-improving-agent

## Goal
Enable the agent to periodically audit its own performance, detect systematic weaknesses, and persist corrective guidance so that the same mistakes are not repeated across conversations.

## When to Invoke
- After completing a complex multi-step task
- When the user explicitly points out a repeated mistake
- At the end of a session involving more than 3 tool-call failures or corrections

## Execution Steps

1. **Collect evidence** — Review the current conversation for:
   - Tool calls that were denied or failed
   - User corrections ("no, instead do…", "don't…", "stop…")
   - Tasks that required more than 2 retries
   - Any security or policy violations flagged

2. **Classify each issue** into one of four categories:
   - `feedback` — behavioral correction to avoid repeating
   - `user` — new understanding of the user's skill level or preferences
   - `project` — context about the project that informed a decision
   - `reference` — pointer to an external resource that was discovered

3. **Deduplicate** — Check existing memory files under `~/.claude/projects/*/memory/` to see if a relevant memory already exists. Update rather than duplicate.

4. **Write memory files** — For each net-new insight, create a `.md` file with proper frontmatter (`name`, `description`, `type`) and register it in `MEMORY.md`.

5. **Self-score** — At the end, output a one-paragraph summary: what improved, what gaps remain, and what the next highest-priority improvement is.

## Acceptance Criteria
- [ ] At least one new or updated memory file is written per invocation (or the agent explicitly states there is nothing new to record)
- [ ] `MEMORY.md` index is updated to reflect all new files
- [ ] No memory is written for information already derivable from the codebase or git history
- [ ] The self-score paragraph is present in the final response
- [ ] No duplicate memories are created