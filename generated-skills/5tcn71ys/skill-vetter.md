# Skill Vetter

## Objective
Provide a structured review gate for any skill document before it is installed or executed. Catch malformed, unsafe, or low-quality skills early, ensuring only vetted skills enter the agent's capability set.

## Execution Steps

### 1. Receive Candidate Skill
- Accept a skill document as either:
  - A file path: `~/.claude/skills/<slug>.md`
  - Raw Markdown content passed directly
- Parse frontmatter (if present) and body sections.

### 2. Structural Validation
Check that the document contains **all** of the following sections (case-insensitive heading match):
- `## Objective` — at least 1 sentence describing the goal.
- `## Execution Steps` — at least 2 numbered or bulleted steps.
- `## Acceptance Criteria` — at least 2 checkable items (`- [ ]` format).

Fail fast with a clear error if any section is missing.

### 3. Safety Review
- Scan step content for high-risk patterns:
  - `rm -rf`, `DROP TABLE`, `curl | bash`, `--force`, `--no-verify`
  - Outbound network calls to non-whitelisted domains
  - Credential or secret exfiltration patterns
- Any match triggers a **BLOCK** with the matched pattern reported.

### 4. Quality Scoring
Score the skill 0–100 across four dimensions (25 pts each):

| Dimension | Criteria |
|-----------|----------|
| Clarity | Steps are unambiguous; no undefined pronouns or vague verbs |
| Completeness | Covers happy path + at least one failure/edge case |
| Testability | Acceptance criteria are objectively verifiable |
| Conciseness | No redundant sections; total length ≤ 600 words |

### 5. Render Verdict
- **PASS** (score ≥ 70, no safety blocks): print score breakdown, approve for install.
- **WARN** (score 50–69, no safety blocks): print score breakdown + specific improvement suggestions; allow install with user confirmation.
- **FAIL** (score < 50 OR any safety block): print detailed reasons; reject install; do not write file.

### 6. Output Report
Print a structured report:
```
Skill Vetter Report
===================
Slug:    <slug>
Verdict: PASS | WARN | FAIL
Score:   <n>/100

Dimension Scores:
  Clarity:      <n>/25
  Completeness: <n>/25
  Testability:  <n>/25
  Conciseness:  <n>/25

Issues Found:
  - <issue 1>
  - <issue 2>
```

## Acceptance Criteria
- [ ] A structurally valid skill with score ≥ 70 receives a PASS verdict and is approved for install.
- [ ] A skill missing any required section receives an immediate FAIL with the missing section named.
- [ ] Any skill containing a high-risk pattern is BLOCKED regardless of quality score.
- [ ] A WARN verdict prompts for explicit user confirmation before proceeding.
- [ ] The output report is always printed, even for PASS verdicts, so there is an audit trail.