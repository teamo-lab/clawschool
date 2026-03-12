# skill-vetter

## Goal
Before a skill is shipped or used, systematically verify that it is well-formed, safe, idempotent where required, and actually solves the stated problem. Produce a structured report so the author knows exactly what to fix.

## Trigger
User says: "vet this skill", "review my skill doc", "check if this skill is ready", or passes a `.md` skill file.

## Execution Steps

### 1. Load the skill
- If a file path is given → `Read` it.
- If inline markdown is given → use it directly.
- If a skill name is given → locate it in `~/.claude/skills/` via `Glob`.

### 2. Structural checks (auto-fail if missing)
| Check | Criterion |
|---|---|
| `name` | kebab-case slug, ≤ 40 chars |
| `summary` | single sentence, ≤ 120 chars |
| `Goal` section | present, ≥ 1 sentence |
| `Trigger` section | lists ≥ 1 concrete user phrase |
| `Execution Steps` | numbered, ≥ 2 steps |
| `Acceptance Criteria` | checklist with ≥ 2 items |

### 3. Quality checks (warnings)
- Steps reference real available tools (cross-check against tool list).
- No hallucinated tool names or parameters.
- Error / failure paths addressed for any network or file I/O step.
- No hard-coded secrets, personal data, or absolute paths outside home dir.
- Steps are deterministic — no "maybe do X" ambiguity.

### 4. Safety checks
- Does not instruct bypassing `--no-verify` or destructive git ops without explicit user confirmation.
- Does not auto-push, auto-delete, or auto-send without user approval gate.
- Network requests use only user-supplied or whitelisted URLs.

### 5. Emit report
```
## Skill Vet Report: <skill-name>
Veredict: PASS | FAIL | WARN

### ✅ Passed Checks
- …

### ❌ Failed Checks (must fix before use)
- [structural | quality | safety] <issue> → <suggested fix>

### ⚠️ Warnings (recommended fixes)
- …

### Score: <passed>/<total> checks
```

### 6. Offer to apply fixes
If FAIL or WARN: ask user "Shall I patch the skill doc with the suggested fixes?"
If yes → use `Edit` to apply only the flagged changes.

## Acceptance Criteria
- [ ] Report produced for any valid markdown input without crashing.
- [ ] All 6 structural checks evaluated and explicitly listed.
- [ ] FAIL verdict correctly blocks skills missing Goal, Trigger, or Acceptance Criteria.
- [ ] Safety section flags any auto-destructive instruction.
- [ ] Patch offer presented when issues found; no edits made without user confirmation.