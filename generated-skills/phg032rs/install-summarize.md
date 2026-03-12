# Install Summarize Skill

## Goal
Resolve the diagnostic gap (gap=10.0) for question `q6` (技能诊断 B) by ensuring the `summarize` skill is correctly installed and operational in the Claude Code environment.

## Prerequisites
- Claude Code CLI installed and authenticated
- Access to the project working directory
- Sufficient permissions to modify `~/.claude/` configuration

## Execution Steps

### Step 1 — Verify current skill inventory
```bash
ls ~/.claude/skills/
```
Confirm that `summarize` is **absent** (expected given the diagnostic reason).

### Step 2 — Locate or create the skill file
If the skill is distributed via a package or registry, install it:
```bash
# Example: copy from project skills directory if available
cp /opt/clawschool-api/.claude/skills/summarize.md ~/.claude/skills/summarize.md
```
If no upstream source exists, create the skill manually at `~/.claude/skills/summarize.md` with the following minimum content:
```markdown
---
name: summarize
description: Summarize the current file, selection, or conversation context into concise bullet points.
---
Summarize the following content into 3-5 concise bullet points, preserving all key facts:

{{content}}
```

### Step 3 — Validate installation
```bash
ls ~/.claude/skills/summarize.md && echo "OK"
```
Expected output: `OK`

### Step 4 — Smoke-test the skill
In a Claude Code session run:
```
/summarize
```
The skill should activate without a "skill not found" error.

## Acceptance Criteria
- [ ] `~/.claude/skills/summarize.md` exists and is non-empty
- [ ] `/summarize` is recognised by Claude Code (no "unknown skill" error)
- [ ] Re-running 诊断 token `phg032rs` scores `q6` gap ≤ 0
- [ ] No regressions in other installed skills (`/help` lists all prior skills intact)