# Skill Vetter

## Goal
Prevent low-quality, unsafe, or redundant skill documents from entering the agent's skill library by applying a structured review checklist before any skill is registered.

## Trigger
Invoke whenever:
- A new skill document is about to be written or saved
- An existing skill is being significantly revised
- The user runs `/skill-vetter <skill-name-or-path>`

## Execution Steps

### 1. Locate the Candidate Skill
- Accept either a file path or raw Markdown as input.
- If a path is given, read the file with the Read tool.

### 2. Apply the Vetting Checklist
Score each criterion **Pass / Warn / Fail**:

| # | Criterion | Guidance |
|---|-----------|----------|
| 1 | **Clear slug** | Lowercase, hyphen-separated, ≤ 40 chars, describes the action not the domain |
| 2 | **One-sentence summary** | Must fit in a skill picker tooltip; no jargon |
| 3 | **Explicit trigger** | States exactly when to invoke (and when NOT to) |
| 4 | **Stepwise execution** | Numbered steps, each actionable without further clarification |
| 5 | **Acceptance criteria** | Checkboxes that can be verified without subjective judgement |
| 6 | **No destructive defaults** | Steps that delete, force-push, or drop data require explicit user confirmation |
| 7 | **No duplication** | Glob `~/.claude/skills/**` and confirm no existing skill covers the same trigger |
| 8 | **Security hygiene** | No hardcoded secrets, no `--no-verify`, no `rm -rf` without guard |
| 9 | **Scope match** | Skill complexity matches frequency of use; one-off tasks should not become skills |

### 3. Report Results
Output the checklist table with scores and, for every Warn/Fail, a one-line remediation suggestion.

### 4. Decision Gate
- **All Pass**: Approve and register the skill.
- **Any Warn**: Ask the user whether to fix before registering.
- **Any Fail**: Block registration, output required fixes, re-run vetter after edits.

### 5. Register (if approved)
- Save the skill file to the appropriate location.
- Confirm registration by listing the skill name in the response.

## Acceptance Criteria
- [ ] Checklist covers all 9 criteria with explicit Pass/Warn/Fail per criterion.
- [ ] No skill with a Fail rating is registered without user override.
- [ ] Duplicate detection runs against the live skill directory, not from memory.
- [ ] Security criteria (#6, #8) are never downgraded to Warn without user acknowledgement.