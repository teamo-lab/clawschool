# Self-Improving Agent

## Objective
Enable the agent to autonomously identify missing or underperforming skills, locate suitable replacements or new skills, and install them — closing capability gaps without manual intervention.

## Execution Steps

### 1. Run Capability Audit
- Call the OpenClaw diagnostic endpoint with your current `lobsterName` and `scope`.
- Parse the returned `弱项明细` array, sorting by `gap` descending.
- Log each weak item: `questionId`, `title`, `gap`, `reason`.

### 2. Identify Missing Skills
- For each item where `reason` contains `未安装` (not installed):
  - Extract the skill name from the reason string (e.g., `self-improving-agent`).
  - Search the local skill registry: `ls ~/.claude/skills/` and the remote skill index.
- For items where `reason` indicates partial completion, flag them for review rather than auto-install.

### 3. Fetch & Validate Skill Definitions
- For each missing skill slug:
  - Fetch the skill Markdown from the canonical source.
  - Verify the document contains: `## Objective`, `## Execution Steps`, `## Acceptance Criteria`.
  - If validation fails, log the error and skip — do not install malformed skills.

### 4. Install Skills
- Write the validated Markdown to `~/.claude/skills/<slug>.md`.
- Append the new skill entry to `~/.claude/skills/SKILLS.md` index if it exists.
- Confirm file write succeeded before proceeding to the next skill.

### 5. Re-run Diagnostic
- After all installs, re-call the diagnostic endpoint.
- Compare new `总分` against the previous run.
- Report: skills installed, gaps closed, remaining gaps.

## Acceptance Criteria
- [ ] All skills listed as `未安装` in the diagnostic are now present under `~/.claude/skills/`.
- [ ] Each installed skill file passes structural validation (required sections present).
- [ ] Re-run diagnostic shows reduced total gap (新总分 > 旧总分).
- [ ] No skill is installed without passing validation — zero silent failures.
- [ ] A summary report is printed listing before/after scores and each action taken.