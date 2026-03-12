# destructive-request-guard

## Goal
Ensure that every destructive or irreversible action (file deletion, database drops, branch force-pushes, resource teardown, etc.) is explicitly confirmed by the user before execution, and that the blast radius is clearly communicated beforehand.

## When to Activate
- User asks to delete files, records, branches, or infrastructure resources
- Command contains keywords: `delete`, `drop`, `remove`, `destroy`, `truncate`, `rm`, `purge`, `wipe`, `reset --hard`, `force-push`
- Any action flagged as non-reversible in the tool description

## Execution Steps

1. **Identify scope** — Before taking any action, list exactly what will be affected (files, rows, branches, projects). State the count and names explicitly.
2. **Classify reversibility** — Label the operation as one of:
   - `REVERSIBLE` (e.g., soft-delete with trash/recycle)
   - `RECOVERABLE` (e.g., recent git commit still in reflog)
   - `IRREVERSIBLE` (e.g., hard delete, DROP TABLE with no backup)
3. **Surface risk** — For `IRREVERSIBLE` operations, output a warning block:
   ```
   ⚠️  IRREVERSIBLE: This will permanently delete [X]. There is no undo.
   Affected: [list of resources]
   ```
4. **Request explicit confirmation** — Ask the user to confirm with a specific phrase (e.g., "yes, delete all" or the resource name) before proceeding. Do not treat silence or a vague "ok" as confirmation.
5. **Execute with audit trail** — After confirmed execution, log what was deleted and when (stdout or a local `deletion_log.txt` entry).
6. **Offer rollback path** — If a recovery option exists (backup, snapshot, reflog), mention it immediately after execution.

## Acceptance Criteria
- [ ] No destructive command executes without an explicit user confirmation step.
- [ ] The affected scope is listed before the confirmation prompt.
- [ ] `IRREVERSIBLE` operations include a visible warning block.
- [ ] A post-execution summary states what was removed.
- [ ] If a rollback path exists, it is communicated to the user.