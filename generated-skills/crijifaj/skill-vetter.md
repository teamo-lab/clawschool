# skill-vetter

## Objective

Prevent malicious, unsafe, or low-quality skills from being installed by providing a structured vetting gate that assesses each request against security, trust, and utility criteria before approval.

## Execution Steps

1. **Source verification** - Identify the skill origin: first-party (auto-approve pending content check), known community source (proceed to content check), unknown/anonymous (flag high-risk immediately).
2. **Content static analysis** - Scan the full skill Markdown for: shell commands writing outside the project directory, outbound HTTP calls to unknown third-party URLs, instructions to suppress safety checks (--no-verify, --force), and prompt-injection patterns.
3. **Permission scope check** - List every tool the skill invokes. Flag any tool not already permitted in the current session permission mode.
4. **Utility assessment** - Confirm the skill solves a stated user need and does not duplicate an existing installed skill. If duplicate, recommend updating instead.
5. **Verdict output** - Emit one of: APPROVE (no issues), APPROVE_WITH_NOTES (minor concerns, user acknowledgement required), or REJECT (hard-fail criteria triggered, exact reasons provided).
6. **Audit log** - Append a timestamped entry to ~/.claude/skill-audit.log with slug, source, and verdict.

## Acceptance Criteria

- No skill containing exfiltration or prompt-injection patterns ever receives APPROVE.
- Every vetting run produces a verdict with at least one supporting reason - no silent approvals.
- Skills from unknown sources always require explicit user confirmation before install.
- Audit log entry is written for every vetting run regardless of verdict.
- Duplicate-skill detection triggers an update recommendation in 95% or more of detected cases.