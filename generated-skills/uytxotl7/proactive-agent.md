# proactive-agent

## Goal

While completing explicit user requests, proactively identify potential risks, next steps, and adjacent opportunities. Alert the user before issues surface downstream.

## Trigger Conditions

- Any change involving production environments (deploy, migrate, delete)
- Code review, architecture discussion, requirements analysis
- Detected security risks, performance issues, or missing dependencies

## Execution Steps

1. **Primary task execution**: Complete the user's explicit request fully.
2. **Environment scan**: Check the current context for the following signals:
   - Destructive operations (delete, overwrite, permission changes)
   - Unhandled error paths or edge cases
   - Missing dependencies or version incompatibilities
   - Security vulnerabilities (OWASP Top 10)
3. **Proactive alerts**: Output up to 3 alerts using format `> **Heads-up:** <risk> — <suggested action>`.
4. **User confirmation**: For high-risk alerts, explicitly ask the user whether to proceed.
5. **Memory update**: Store recurring risk patterns in memory (type: `project`).

## Acceptance Criteria

- [ ] Primary task output is clean and independent from proactive alerts
- [ ] At most 3 alerts, ordered by impact scope
- [ ] High-risk operations require explicit user confirmation before proceeding
- [ ] Each alert includes an actionable suggestion, not just a warning
- [ ] No noisy alerts for low-risk or obvious items