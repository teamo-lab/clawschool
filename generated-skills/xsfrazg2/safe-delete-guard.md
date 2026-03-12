# safe-delete-guard

## Goal

Prevent irreversible data loss by requiring explicit user confirmation and evidence collection before executing any destructive command, API call, or database mutation.

## When to Invoke

Trigger this skill whenever the task involves:
- HTTP `DELETE` requests or SQL `DROP / TRUNCATE / DELETE` statements
- File-system removals (`rm`, `unlink`, bulk-delete scripts)
- Cloud resource teardown (buckets, databases, deployments)

## Execution Steps

1. **Identify scope** — List every resource that will be permanently affected. Output the list to the user before proceeding.
2. **Assess reversibility** — Check whether a backup, soft-delete flag, or recycle-bin mechanism exists. If yes, prefer the reversible path.
3. **Require explicit confirmation** — Use `AskUserQuestion` to ask: *"You are about to permanently delete [N items / resource name]. Type YES to confirm."* Do not proceed on ambiguous answers.
4. **Dry-run first** — Where the tooling supports it (e.g., `--dry-run`, `EXPLAIN`, preview mode), execute a non-destructive preview and show the output.
5. **Execute with minimal blast radius** — Delete the smallest unit possible; avoid wildcard patterns unless the user explicitly approves.
6. **Verify post-deletion** — Confirm the resource is gone and that no unintended collateral was removed (check row counts, directory listings, API responses).
7. **Log the action** — Record what was deleted, by whom (user-confirmed), and when, in a brief inline summary.

## Acceptance Criteria

- [ ] No destructive command is executed without an explicit user `YES` confirmation.
- [ ] A dry-run or preview step is performed and shown to the user whenever the tool supports it.
- [ ] Post-deletion verification confirms only the intended resources were removed.
- [ ] If the reversible path exists, it is offered to the user before the permanent path.
- [ ] The skill refuses to proceed if the blast radius cannot be determined (e.g., wildcard with unknown scope).