# skill-vetter

## Goal
A meta-skill that reviews any skill document and produces a structured vetting report, preventing broken or unsafe skills from being installed.

## Trigger
Invoke via /skill-vetter [skill-name or file-path or inline-text]

## Execution Steps

1. Load the skill source: file path argument -> Read the file; known skill name -> locate in skills directory; otherwise treat raw argument as skill body.

2. Run the vetting checklist and assign PASS, WARN, or FAIL to each criterion:
   - Trigger clarity: unambiguous invocation pattern exists.
   - Tool safety: no destructive tools called without explicit user confirmation.
   - Error handling: at least one failure/fallback path documented.
   - Acceptance criteria: 3 or more checkboxed acceptance criteria present.
   - Scope creep: skill does not exceed one primary responsibility.
   - Secret hygiene: no hardcoded credentials, tokens, or PII.
   - Idempotency: re-running does not cause duplicate side-effects.

3. Generate vetting report as a Markdown table of all 7 criteria with status and notes, followed by a Verdict section (APPROVED, NEEDS REVISION, or REJECTED) and a Required Fixes list if applicable.

4. Verdict logic: any FAIL -> REJECTED; any WARN -> NEEDS REVISION; all PASS -> APPROVED.

5. If APPROVED, offer to proceed with installation via /skill-vetter --install.

## Acceptance Criteria
- Full 7-criterion table renders for every run.
- A skill with a hardcoded token scores FAIL on secret hygiene and is REJECTED.
- A skill with no acceptance criteria scores FAIL on that criterion.
- An all-passing skill returns APPROVED and offers the install prompt.
- /skill-vetter --install after approval proceeds without re-running vetting.