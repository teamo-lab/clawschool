# Self-Improving Agent

## Goal
Enable the agent to detect its own performance gaps after task completion and apply targeted improvements — updating memory entries, skill docs, or system prompts — so that the same class of error does not recur in future conversations.

## Trigger
Invoke after any conversation where:
- The user had to correct the agent more than once
- A task failed or required significant rework
- A post-task review is explicitly requested (e.g. `/self-improving-agent`)

## Execution Steps

### 1. Collect Evidence
- Re-read the current conversation from the top, noting every correction, denial, or rework request from the user.
- Run `git log --oneline -10` and `git diff HEAD~1` if applicable to understand what changed.
- Check `/home/clawapi/.claude/projects/-opt-clawschool-api/memory/MEMORY.md` for existing relevant memories.

### 2. Classify Each Gap
For each observed failure, assign one of:
| Class | Fix Target |
|---|---|
| Missing context | Write/update a `project` or `user` memory |
| Repeated mistake | Write/update a `feedback` memory |
| Missing capability | Draft or update a Skill doc |
| Bad default behavior | Propose a CLAUDE.md rule |

### 3. Apply Fixes
- **Memory**: Write new `.md` files under `memory/` with correct frontmatter (`name`, `description`, `type`). Update `MEMORY.md` index.
- **Skill**: If a reusable workflow is missing, draft a new skill file and register it.
- **CLAUDE.md**: If a systemic rule is needed, append it under a clearly labelled section and confirm with the user before saving.

### 4. Summarize Changes
Output a brief table:
```
| Gap | Class | Fix Applied |
|-----|-------|-------------|
| ... | ...   | ...         |
```

## Acceptance Criteria
- [ ] Every correction from the current conversation maps to at least one concrete fix.
- [ ] No new memory file duplicates an existing one (check MEMORY.md first).
- [ ] User confirms proposed CLAUDE.md changes before they are written.
- [ ] The agent can demonstrate in the next turn that the fix is in place (e.g. recall the new memory, show the updated skill).